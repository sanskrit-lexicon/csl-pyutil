# -*- coding: utf-8 -*-
"""NKRYa shared client (H5282) — the module's own offline selftest plus the
throttle/429 contract the consumers depend on."""
import json
import os
import urllib.error
import urllib.request

import pytest

from csl_pyutil import nkrya


def test_module_selftest_offline():
    nkrya.selftest()


def test_fixtures_ship_with_the_package():
    files = sorted(f for f in os.listdir(nkrya.FIXTURES) if f.endswith(".json"))
    assert len(files) == 3, files
    for name in files:
        with open(os.path.join(nkrya.FIXTURES, name), encoding="utf-8") as f:
            assert "response" in json.load(f)


def test_default_cache_dir_is_per_caller(tmp_path, monkeypatch):
    monkeypatch.setenv(nkrya.CACHE_ENV, str(tmp_path / "x"))
    assert nkrya.default_cache_dir() == str(tmp_path / "x")
    monkeypatch.delenv(nkrya.CACHE_ENV)
    assert nkrya.default_cache_dir().startswith(os.path.expanduser("~"))
    # an explicit constructor arg always wins over env and default
    monkeypatch.setenv(nkrya.CACHE_ENV, str(tmp_path / "env"))
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path / "given"), offline=True)
    assert cli.cache_dir == os.path.abspath(str(tmp_path / "given"))


def test_rate_and_burst_read_env(monkeypatch, tmp_path):
    monkeypatch.setenv(nkrya.RATE_ENV, "12")
    monkeypatch.setenv(nkrya.BURST_ENV, "4")
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), offline=True)
    assert cli.bucket.rate_per_min == 12.0 and cli.bucket.capacity == 4.0
    monkeypatch.setenv(nkrya.RATE_ENV, "nonsense")
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), offline=True)
    assert cli.bucket.rate_per_min == nkrya.DEFAULT_RATE_PER_MIN
    with pytest.raises(ValueError):
        nkrya.TokenBucket(rate_per_min=0)


def _fake_clock():
    fake = {"t": 0.0}
    slept = []

    def clock():
        return fake["t"]

    def sleeper(s):
        slept.append(s)
        fake["t"] += s

    return fake, slept, clock, sleeper


def test_fifteen_freq_calls_survive_every_other_429(tmp_path, monkeypatch):
    """Acceptance 3 shape, offline: a 429 every second call, zero raised."""
    _fake, slept, clock, sleeper = _fake_clock()
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), token="dummy",
                            rate_per_min=6.0, burst=3.0, clock=clock, sleeper=sleeper)
    state = {"n": 0}

    def fake_urlopen(req, timeout=None):
        state["n"] += 1
        if state["n"] % 2 == 0:
            raise nkrya._FakeHTTPError(429, {"Retry-After": "13"})
        return nkrya._FakeResponse({"frequencyData": {"ipm": 1.0, "category": 1}})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    out = [cli.freq("слово%d" % i, "S") for i in range(15)]
    assert len(out) == 15 and all(r["ipm"] == 1.0 for r in out)
    # 29 live calls: 15 that answered, and a 429 between each pair of them
    assert cli.http_calls == 29
    assert cli.throttled_429 == 14 and cli.bucket.penalties == 14
    # After a 429 the next token costs the Retry-After (13 s) plus the ordinary
    # 10 s refill at 6/min; a client ignoring the header would sleep 10 s flat.
    assert any(abs(s - 23.0) < 1e-6 for s in slept), slept
    assert min(slept) >= 10.0 - 1e-6, slept
    assert len(os.listdir(str(tmp_path))) == 15


def test_429_past_max_retries_raises_not_silently_empty(tmp_path, monkeypatch):
    _fake, _slept, clock, sleeper = _fake_clock()
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), token="dummy", max_retries=2,
                            rate_per_min=60.0, clock=clock, sleeper=sleeper)

    def always_429(req, timeout=None):
        raise nkrya._FakeHTTPError(429, {"Retry-After": "1"})

    monkeypatch.setattr(urllib.request, "urlopen", always_429)
    with pytest.raises(nkrya.NkryaError):
        cli.freq("туча", "S")
    assert cli.http_calls == 3 and not os.listdir(str(tmp_path))


def test_server_error_backs_off_without_bucket_penalty(tmp_path, monkeypatch):
    _fake, slept, clock, sleeper = _fake_clock()
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), token="dummy",
                            rate_per_min=60.0, clock=clock, sleeper=sleeper)
    state = {"n": 0}

    def flaky(req, timeout=None):
        state["n"] += 1
        if state["n"] == 1:
            raise nkrya._FakeHTTPError(503)
        return nkrya._FakeResponse({"frequencyData": {"ipm": 2.0, "category": 2}})

    monkeypatch.setattr(urllib.request, "urlopen", flaky)
    assert cli.freq("туча", "S")["ipm"] == 2.0
    assert cli.throttled_429 == 0 and cli.bucket.penalties == 0 and slept


def test_auth_failure_is_not_retried(tmp_path, monkeypatch):
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), token="bad", rate_per_min=60.0)

    def refused(req, timeout=None):
        raise nkrya._FakeHTTPError(403, body=b'{"detail":"nope"}')

    monkeypatch.setattr(urllib.request, "urlopen", refused)
    with pytest.raises(nkrya.NkryaAuthError):
        cli.freq("туча", "S")
    assert cli.http_calls == 1


def test_retry_after_http_date_and_junk():
    import email.utils
    import time

    assert nkrya.parse_retry_after("5") == 5.0
    assert nkrya.parse_retry_after("") is None
    assert nkrya.parse_retry_after("later") is None
    assert nkrya.parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0
    soon = email.utils.formatdate(time.time() + 30, usegmt=True)
    assert 10.0 < nkrya.parse_retry_after(soon) <= 35.0


def test_offline_miss_raises_and_cache_roundtrip(tmp_path, monkeypatch):
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), offline=True)
    with pytest.raises(nkrya.NkryaOffline):
        cli.freq("несуществующее", "S")
    live = nkrya.NkryaClient(cache_dir=str(tmp_path), token="dummy", rate_per_min=600.0)
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=None: nkrya._FakeResponse(
                            {"frequencyData": {"ipm": 9.0, "category": 4}}))
    assert live.freq("туча", "S") == {"ipm": 9.0, "category": 4}
    assert nkrya.NkryaClient(cache_dir=str(tmp_path), offline=True).freq("туча", "S") == {
        "ipm": 9.0, "category": 4}


def test_lazy_package_attribute():
    import csl_pyutil

    assert csl_pyutil.nkrya is nkrya
    assert "nkrya" in dir(csl_pyutil)


def test_no_token_fails_closed_before_network(tmp_path, monkeypatch):
    monkeypatch.delenv(nkrya.TOKEN_ENV, raising=False)
    monkeypatch.setattr(nkrya, "load_token", lambda: None)

    def boom(req, timeout=None):
        raise AssertionError("must not reach the network without a token")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    with pytest.raises(nkrya.NkryaAuthError) as e:
        nkrya.NkryaClient(cache_dir=str(tmp_path)).freq("туча", "S")
    assert "ruscorpora-api" in str(e.value)


def test_urlerror_is_wrapped(tmp_path, monkeypatch):
    _fake, _slept, clock, sleeper = _fake_clock()
    cli = nkrya.NkryaClient(cache_dir=str(tmp_path), token="dummy", max_retries=1,
                            rate_per_min=60.0, clock=clock, sleeper=sleeper)

    def down(req, timeout=None):
        raise urllib.error.URLError("no route")

    monkeypatch.setattr(urllib.request, "urlopen", down)
    with pytest.raises(nkrya.NkryaError):
        cli.freq("туча", "S")
