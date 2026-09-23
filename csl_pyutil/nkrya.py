#!/usr/bin/env python3
"""NKRYa (Russian National Corpus, ruscorpora.ru) API client — shared (H5282).

Ported out of SanskritLexicography `RussianTranslation/src/nkrya_client.py`
(H5261) so every consumer repo imports ONE client instead of copying it.
Consumers keep a thin shim that sets their own cache dir and fixtures path.

Official API only: https://github.com/ruscorpora/public-api (Bearer token,
https://ruscorpora.ru/api/v1/). Scraping and the unofficial user clients
(kunansy/rnc, kmike/ruscorpora-tools) are ruled out (grill 22-09-2026).

Three queries, all cached on disk by request hash:

  sketch(lemma, pos)          word-portrait PORTRAIT_SKETCH: up to 10 collocates per
                              syntactic relation, ranked by dice (the API returns no more)
  freq(lemma, pos)            word-portrait PORTRAIT_FREQUENCY: ipm + 1..6 category
  concordance(query, n=3)     lex-gramm concordance: total hits (queryStats) + n lines

Default corpus is MAIN. The 19th-century archaism check is a concordance run with a
`created` 1800-1899 subcorpus (a word portrait takes no subcorpus).

Rate limiting (H5282): live 23-09-2026 the API answered HTTP 429 after ~10 calls
in a minute. Every live call passes a token bucket — default 6 requests/min with a
burst of 3, overridable per client or via env `NKRYA_RATE_PER_MIN` / `NKRYA_BURST`.
A 429 honours `Retry-After` (seconds or HTTP-date) when present, otherwise backs off
exponentially, and is retried up to `max_retries` times (default 5) — one 429 never
fails a batch run.

Cache dir is per caller: constructor arg, else env `CSL_PYUTIL_NKRYA_CACHE`, else
`~/.cache/csl_pyutil/nkrya`. Nothing repo-specific lives here.

Token (never in git or a repo .env), first hit wins:
  1. env RUSCORPORA_API_TOKEN
  2. macOS keychain generic password, service `ruscorpora-api`
  3. python `keyring` service `ruscorpora-api` (Windows Credential Manager on MSI)
No token -> NkryaAuthError with the exact command to store one (fail closed).

CLI:
  python -m csl_pyutil.nkrya --selftest
  python -m csl_pyutil.nkrya probe
  python -m csl_pyutil.nkrya sketch туча S
  python -m csl_pyutil.nkrya freq сплочённый A
  python -m csl_pyutil.nkrya pair сплочённый туча [--19c]
"""

import argparse
import email.utils
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

API = "https://ruscorpora.ru/api/v1"
KEYCHAIN_SERVICE = "ruscorpora-api"
TOKEN_ENV = "RUSCORPORA_API_TOKEN"
CACHE_ENV = "CSL_PYUTIL_NKRYA_CACHE"
RATE_ENV = "NKRYA_RATE_PER_MIN"
BURST_ENV = "NKRYA_BURST"
HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures", "nkrya")
DEFAULT_RATE_PER_MIN = 6.0   # live 23-09-2026: 429 after ~10 calls/min
DEFAULT_BURST = 3.0
MAX_RETRIES = 5              # on 429 / 5xx; Retry-After honoured when sent
MAX_BACKOFF_S = 120.0        # cap on any single sleep between retries
SEED = 5261                  # fixed seed -> stable example sorting across runs
SLICE_19C = {"fieldName": "created", "intRange": {"begin": 1800, "end": 1899}}

STORE_HINT = (
    "No NKRYa API token found. Generate a non-expiring key at "
    "https://ruscorpora.ru/accounts/profile/for-devs, then store it:\n"
    "  macOS:   security add-generic-password -a \"$USER\" -s ruscorpora-api -w\n"
    "           (prompts for the key; nothing lands in shell history)\n"
    "  Windows: python -c \"import keyring,getpass; "
    "keyring.set_password('ruscorpora-api','token',getpass.getpass())\"\n"
    "or export %s for one shell." % TOKEN_ENV)


class NkryaError(RuntimeError):
    pass


class NkryaAuthError(NkryaError):
    pass


class NkryaOffline(NkryaError):
    """Raised in offline/fixture mode when a request is not in the cache."""


def default_cache_dir():
    """Per-caller cache dir: env override, else a user-level cache dir."""
    env = os.environ.get(CACHE_ENV, "").strip()
    if env:
        return env
    home = os.path.expanduser("~")
    return os.path.join(home, ".cache", "csl_pyutil", "nkrya")


def load_token():
    tok = os.environ.get(TOKEN_ENV, "").strip()
    if tok:
        return tok
    if sys.platform == "darwin":
        try:
            p = subprocess.run(
                ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
                capture_output=True, text=True, encoding="utf-8", timeout=10)
            if p.returncode == 0 and p.stdout.strip():
                return p.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    try:
        import keyring  # optional; the Windows credential store on MSI
        tok = keyring.get_password(KEYCHAIN_SERVICE, "token")
        if tok:
            return tok.strip()
    except Exception:
        pass
    return None


def request_key(endpoint, payload):
    blob = json.dumps({"endpoint": endpoint, "payload": payload},
                      ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def parse_retry_after(value, now=None):
    """`Retry-After` -> seconds to wait (float), or None when unusable.

    The header is either a delta in seconds or an HTTP-date (RFC 7231); a date
    in the past yields 0.0, never a negative sleep.
    """
    if not value:
        return None
    raw = str(value).strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        stamp = time.mktime(when.timetuple())
    else:
        stamp = when.timestamp()
    return max(0.0, stamp - (time.time() if now is None else now))


class TokenBucket:
    """Requests-per-minute throttle: `take()` blocks until a token is free.

    A 429 calls `penalise(seconds)`, which empties the bucket AND pushes the
    refill clock forward, so the pause the server asked for is respected by
    every later call too — not just the one that got refused.
    """

    def __init__(self, rate_per_min=DEFAULT_RATE_PER_MIN, burst=DEFAULT_BURST,
                 clock=time.monotonic, sleeper=time.sleep):
        rate_per_min = float(rate_per_min)
        if rate_per_min <= 0:
            raise ValueError("rate_per_min must be > 0, got %r" % rate_per_min)
        self.rate_per_min = rate_per_min
        self.rate = rate_per_min / 60.0
        self.capacity = max(1.0, float(burst))
        self.clock = clock
        self.sleeper = sleeper
        self.tokens = self.capacity
        self.updated = clock()
        self.waited_s = 0.0      # cumulative throttle sleep, for reporting
        self.penalties = 0       # how many times a 429 pushed the clock

    def _refill(self):
        now = self.clock()
        if now > self.updated:
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
            self.updated = now

    def take(self, n=1):
        """Block until n tokens are available; return the seconds slept."""
        slept = 0.0
        while True:
            self._refill()
            if self.tokens >= n:
                self.tokens -= n
                return slept
            need = (n - self.tokens) / self.rate
            if self.updated > self.clock():        # penalty window still open
                need += self.updated - self.clock()
            self.sleeper(need)
            slept += need
            self.waited_s += need

    def penalise(self, seconds):
        """After a 429: drop the tokens and delay the next refill by `seconds`."""
        seconds = max(0.0, float(seconds or 0.0))
        self.tokens = 0.0
        self.updated = max(self.updated, self.clock()) + seconds
        self.penalties += 1
        return seconds


class NkryaClient:
    def __init__(self, cache_dir=None, offline=False, token=None,
                 rate_per_min=None, burst=None, max_retries=MAX_RETRIES,
                 clock=time.monotonic, sleeper=time.sleep):
        self.cache_dir = os.path.abspath(cache_dir or default_cache_dir())
        self.offline = offline
        self._token = token
        self.max_retries = int(max_retries)
        self.used_keys = []          # cache entries this client read or wrote
        self.http_calls = 0          # live requests actually issued
        self.throttled_429 = 0       # 429s absorbed by the retry/backoff path
        if rate_per_min is None:
            rate_per_min = _env_float(RATE_ENV, DEFAULT_RATE_PER_MIN)
        if burst is None:
            burst = _env_float(BURST_ENV, DEFAULT_BURST)
        self.bucket = TokenBucket(rate_per_min, burst, clock=clock, sleeper=sleeper)
        self._sleeper = sleeper

    # ---- transport -------------------------------------------------------
    def _cache_path(self, key):
        return os.path.join(self.cache_dir, key + ".json")

    def _call(self, endpoint, payload, method):
        key = request_key(endpoint, payload)
        path = self._cache_path(key)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.used_keys.append(key)
                return json.load(f)["response"]
        if self.offline:
            raise NkryaOffline("not cached (offline): %s %s" % (endpoint, key))
        if self._token is None:
            self._token = load_token()
        if not self._token:
            raise NkryaAuthError(STORE_HINT)
        resp = self._http(endpoint, payload, method)
        os.makedirs(self.cache_dir, exist_ok=True)
        rec = {"request": {"endpoint": endpoint, "method": method, "payload": payload},
               "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "response": resp}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=1, sort_keys=True)
            f.write("\n")
        self.used_keys.append(key)
        return resp

    def _http(self, endpoint, payload, method):
        url = API + endpoint
        headers = {"Authorization": "Bearer " + self._token,
                   "Accept": "application/json",
                   "User-Agent": "csl-pyutil-nkrya/1 (H5282)"}
        data = None
        if method == "GET":
            url += "?" + urllib.parse.urlencode(
                {"query": json.dumps(payload, ensure_ascii=False)})
        else:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        for attempt in range(self.max_retries + 1):
            self.bucket.take()
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            self.http_calls += 1
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", "replace")[:400]
                if e.code in (401, 403):
                    raise NkryaAuthError("NKRYa refused the token (HTTP %d): %s\n%s"
                                         % (e.code, body, STORE_HINT))
                if e.code == 429 or e.code >= 500:
                    if attempt < self.max_retries:
                        retry_after = None
                        try:
                            retry_after = parse_retry_after(
                                (e.headers or {}).get("Retry-After"))
                        except Exception:
                            retry_after = None
                        wait = retry_after if retry_after is not None else 2 ** attempt * 2
                        wait = min(float(wait), MAX_BACKOFF_S)
                        if e.code == 429:
                            self.throttled_429 += 1
                            self.bucket.penalise(wait)
                        else:
                            self._sleeper(wait)
                        continue
                raise NkryaError("HTTP %d on %s: %s" % (e.code, endpoint, body))
            except urllib.error.URLError as e:
                if attempt < self.max_retries:
                    self._sleeper(min(2 ** attempt * 2.0, MAX_BACKOFF_S))
                    continue
                raise NkryaError("network error on %s: %s" % (endpoint, e))
        raise NkryaError("retries exhausted on %s" % endpoint)

    # ---- queries ---------------------------------------------------------
    def _portrait(self, lemma, pos, result_type, corpus="MAIN"):
        # word-portrait indexes lemmas without ё: "сплочённый" -> null, "сплоченный" -> 0.94 ipm
        # (live, 23-09-2026). Concordance search handles ё itself, so only portraits fold it.
        payload = {"lemma": yo_fold(lemma), "corpus": {"type": corpus},
                   "resultType": [result_type], "seed": SEED}
        if pos:
            payload["pos"] = pos
        return self._call("/word-portrait/", payload, "GET")

    def sketch(self, lemma, pos=None, corpus="MAIN"):
        """{relation: [(collocate, dice), ...]} ranked as returned (dice desc, top 10)."""
        raw = self._portrait(lemma, pos, "PORTRAIT_SKETCH", corpus)
        rels = {}
        for block in (raw.get("sketchData") or {}).get("collocates") or []:
            rel = block.get("sketchSynRelation") or "?"
            rows = []
            for c in block.get("collocations") or []:
                word = ((c.get("collocate") or {}).get("valString") or {}).get("v")
                dice = next((m.get("value") for m in c.get("metrics") or []
                             if m.get("name") in ("dice", "logDice")), None)
                if word:
                    rows.append((word, dice))
            rels[rel] = rows
        return rels

    def freq(self, lemma, pos=None, corpus="MAIN"):
        """{'ipm': float|None, 'category': int|None}."""
        raw = self._portrait(lemma, pos, "PORTRAIT_FREQUENCY", corpus)
        fd = raw.get("frequencyData") or {}
        return {"ipm": fd.get("ipm"), "category": fd.get("category")}

    def concordance(self, lexgramm, n=3, corpus="MAIN", subcorpus_conditions=None):
        """{'hits': int|None, 'docs': int|None, 'lines': [str]} for a lexGramm form."""
        payload = {"corpus": {"type": corpus}, "lexGramm": lexgramm,
                   "params": {"pageParams": {"page": 0, "docsPerPage": n,
                                             "snippetsPerDoc": 1},
                              "seed": SEED}}
        if subcorpus_conditions:
            payload["subcorpus"] = {"sectionValues": [
                {"conditionValues": list(subcorpus_conditions)}]}
        raw = self._call("/lex-gramm/concordance", payload, "POST")
        qs = raw.get("queryStats") or {}
        return {"hits": qs.get("wordUsageCount"), "docs": qs.get("textCount"),
                "lines": snippet_lines(raw, n)}

    def pair(self, modifier, head, n=3, dist=(1, 3), slice_19c=False, corpus="MAIN"):
        """Concordance of lemma `modifier` followed within `dist` words by lemma `head`."""
        return self.concordance(pair_query(modifier, head, dist), n=n, corpus=corpus,
                                subcorpus_conditions=[SLICE_19C] if slice_19c else None)


def _env_float(name, fallback):
    raw = os.environ.get(name, "").strip()
    if not raw:
        return fallback
    try:
        value = float(raw)
    except ValueError:
        return fallback
    return value if value > 0 else fallback


def pair_query(first, second, dist=(1, 3)):
    return {"sectionValues": [{
        "conditionValues": [{"fieldName": "disambmod", "text": {"v": "main"}},
                            {"fieldName": "distmod", "text": {"v": "with_zeros"}}],
        "subsectionValues": [
            {"conditionValues": [{"fieldName": "lex", "text": {"v": first}}]},
            {"conditionValues": [{"fieldName": "lex", "text": {"v": second}},
                                 {"fieldName": "dist",
                                  "intRange": {"begin": dist[0], "end": dist[1]}}]}]}]}


def snippet_lines(raw, n):
    """Render up to n concordance snippets; hit words wrapped in [ ]."""
    out = []
    for group in raw.get("groups") or []:
        for doc in group.get("docs") or []:
            title = ((doc.get("info") or {}).get("title") or "").strip()
            for sg in doc.get("snippetGroups") or []:
                for snip in sg.get("snippets") or []:
                    parts = []
                    for seq in snip.get("sequences") or []:
                        for w in seq.get("words") or []:
                            t = w.get("text") or ""
                            if (w.get("displayParams") or {}).get("hit"):
                                t = "[" + t + "]"
                            parts.append(t)
                    text = " ".join("".join(parts).split())
                    if text:
                        out.append(text + (" — " + title if title else ""))
                    if len(out) >= n:
                        return out
    return out


def yo_fold(s):
    """ё/Ё -> е/Е — NKRYa word portraits key lemmas without ё."""
    return s.replace("ё", "е").replace("Ё", "Е") if s else s


def rank_in(rows, word):
    """1-based rank of word in a sketch relation list, or None (not in the top 10)."""
    for i, (w, _d) in enumerate(rows, 1):
        if yo_fold(w) == yo_fold(word):
            return i, _d
    return None, None


# ---- selftest (offline, recorded doc-shaped fixtures) -----------------------
class _FakeHTTPError(urllib.error.HTTPError):
    """A 429/5xx response with headers, without touching the network."""

    def __init__(self, code, headers=None, body=b"{}"):
        import io
        urllib.error.HTTPError.__init__(self, "https://example.invalid", code,
                                        "fake", headers or {}, io.BytesIO(body))


class _FakeResponse:
    """What `urlopen` returns, minus the socket."""

    def __init__(self, payload):
        self._body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def selftest(fixtures=None, client_class=None, label="csl_pyutil.nkrya"):
    """Offline checks against recorded doc-shaped fixtures.

    `fixtures` lets a consumer shim run the same checks against its own copy of
    the fixture dir; `client_class` lets it exercise its own subclass.
    """
    import shutil
    import tempfile

    fx = os.path.abspath(fixtures or FIXTURES)
    client_class = client_class or NkryaClient
    cli = client_class(cache_dir=fx, offline=True)

    # 1. sketch parse on the official `слово` example shape
    rels = cli.sketch("слово", "S")
    assert rels["amod_S_A"][0] == ("честный", 10.3028), rels["amod_S_A"][:2]
    assert len(rels["amod_S_A"]) == 10
    assert "nsubj_S_V" in rels and rels["nsubj_S_V"][0][0] == "звучать"
    assert rank_in(rels["amod_S_A"], "добрый") == (4, 8.57147)
    assert rank_in(rels["amod_S_A"], "сплочённый") == (None, None)
    # ё-fold (23-09-2026): portraits key lemmas without ё; matching ignores ё both ways
    assert yo_fold("сплочённый") == "сплоченный" and yo_fold("Ёж") == "Еж"
    assert rank_in([("черный", 1.0)], "чёрный") == (1, 1.0)

    # 2. freq parse (official `кошка` example: ipm 44.0418, category 3)
    assert cli.freq("кошка", "S") == {"ipm": 44.0418, "category": 3}

    # 3. concordance: stats + hit marking + n cap
    c = cli.pair("чёрный", "кошка", n=2)
    assert c["hits"] == 137 and c["docs"] == 98, c
    assert len(c["lines"]) == 2 and "[чёрная] [кошка]" in c["lines"][0], c["lines"]

    # 4. offline miss fails loudly, never silently empty
    try:
        cli.freq("несуществующее", "S")
        raise AssertionError("offline miss must raise")
    except NkryaOffline:
        pass

    # 5. cache key is stable and order-insensitive
    assert request_key("/x", {"a": 1, "b": 2}) == request_key("/x", {"b": 2, "a": 1})
    assert request_key("/x", {"a": 1}) != request_key("/y", {"a": 1})

    # 6. Retry-After parsing: delta-seconds, HTTP-date, junk, past date
    assert parse_retry_after("30") == 30.0
    assert parse_retry_after(" 0 ") == 0.0
    assert parse_retry_after(None) is None and parse_retry_after("soon") is None
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0   # past -> 0, never < 0
    future = email.utils.formatdate(time.time() + 40, usegmt=True)
    assert 20.0 < parse_retry_after(future) <= 45.0, parse_retry_after(future)

    # 7. token bucket: a burst passes, then the rate paces; a fake clock, no real sleep
    fake = {"t": 0.0}
    slept = []

    def clock():
        return fake["t"]

    def sleeper(s):
        slept.append(s)
        fake["t"] += s

    b = TokenBucket(rate_per_min=6.0, burst=3.0, clock=clock, sleeper=sleeper)
    for _ in range(3):
        assert b.take() == 0.0        # the burst is free
    assert not slept
    assert abs(b.take() - 10.0) < 1e-6, slept     # 6/min -> one per 10 s
    # a 429 penalty delays the next token by the Retry-After the server sent
    b.penalise(25.0)
    waited = b.take()                             # 25 s penalty + 10 s refill
    assert abs(waited - 35.0) < 1e-6, waited
    assert b.penalties == 1 and b.waited_s > 0

    # 8. 15 freq calls survive injected 429s: the REAL _http loop runs, only the
    #    socket is faked — Retry-After honoured, nothing raised, cache complete
    tmp = tempfile.mkdtemp()
    try:
        fake["t"] = 0.0
        del slept[:]
        live = client_class(cache_dir=tmp, token="dummy", rate_per_min=6.0, burst=3.0,
                            clock=clock, sleeper=sleeper)
        state = {"n": 0}

        def fake_urlopen(req, timeout=None):
            state["n"] += 1
            if state["n"] % 4 == 0:      # every 4th live call is refused
                raise _FakeHTTPError(429, {"Retry-After": "7"})
            return _FakeResponse({"frequencyData": {"ipm": float(state["n"]),
                                                    "category": 3}})

        real_urlopen = urllib.request.urlopen
        urllib.request.urlopen = fake_urlopen
        try:
            got = [live.freq("лемма%d" % i, "S")["ipm"] for i in range(15)]
        finally:
            urllib.request.urlopen = real_urlopen
        assert len(got) == 15 and all(g for g in got), got
        assert live.throttled_429 >= 3, live.throttled_429
        assert len(os.listdir(tmp)) == 15, os.listdir(tmp)
        assert sum(slept) >= 100.0, sum(slept)   # throttle + penalties really paced it

        # 9. no token -> fail closed with the storing hint, before any network
        saved = os.environ.pop(TOKEN_ENV, None)
        try:
            broke = client_class(cache_dir=tmp, token="")
            try:
                broke.freq("туча", "S")
                raise AssertionError("empty token must fail closed")
            except NkryaAuthError as e:
                assert "security add-generic-password" in str(e)
        finally:
            if saved is not None:
                os.environ[TOKEN_ENV] = saved

        # 10. a live response is written to the cache and re-read without network
        one = client_class(cache_dir=tmp, token="dummy")
        one._http = lambda ep, pl, m: {"frequencyData": {"ipm": 1.5, "category": 2}}
        assert one.freq("туча", "S")["ipm"] == 1.5
        again = client_class(cache_dir=tmp, offline=True)
        assert again.freq("туча", "S") == {"ipm": 1.5, "category": 2}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("%s selftest OK (10 checks, offline fixtures: %s)" % (label, fx))


def main(argv=None, default_cache=None, fixtures=None, client_class=None,
         label="csl_pyutil.nkrya"):
    ap = argparse.ArgumentParser(description="NKRYa evidence client (H5282)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--offline", action="store_true", help="cache only, no network")
    ap.add_argument("--cache", default=default_cache or default_cache_dir())
    ap.add_argument("--rate-per-min", type=float, default=None,
                    help="live requests per minute (default %g)" % DEFAULT_RATE_PER_MIN)
    ap.add_argument("cmd", nargs="?", choices=["probe", "sketch", "freq", "pair"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--19c", dest="c19", action="store_true")
    ap.add_argument("-n", type=int, default=3)
    a = ap.parse_args(argv)
    client_class = client_class or NkryaClient
    if a.selftest:
        selftest(fixtures=fixtures, client_class=client_class, label=label)
        return 0
    if not a.cmd:
        ap.error("command required")
    cli = client_class(cache_dir=a.cache, offline=a.offline, rate_per_min=a.rate_per_min)
    try:
        if a.cmd == "probe":
            tok = load_token()
            if not tok:
                raise NkryaAuthError(STORE_HINT)
            cli._token = tok
            me = cli._http("/auth/check-authenticated/", {}, "GET")
            print("auth:", json.dumps(me, ensure_ascii=False))
            c = cli.pair("чёрный", "туча", n=1, slice_19c=True)
            print("19c subcorpus accepted: hits=%s" % c["hits"])
        elif a.cmd == "sketch":
            for rel, rows in cli.sketch(*a.args).items():
                print(rel, ", ".join("%s %.2f" % (w, d or 0) for w, d in rows))
        elif a.cmd == "freq":
            print(json.dumps(cli.freq(*a.args), ensure_ascii=False))
        elif a.cmd == "pair":
            print(json.dumps(cli.pair(a.args[0], a.args[1], n=a.n, slice_19c=a.c19),
                             ensure_ascii=False, indent=1))
    except NkryaError as e:
        print("NKRYa: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
