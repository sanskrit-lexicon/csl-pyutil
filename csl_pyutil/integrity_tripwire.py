# -*- coding: utf-8 -*-
"""integrity_tripwire — a standing checksum on human-reviewed overlay data.

Built for wave 1 of the Q7 data-integrity programme (H2890 census, H2891 this
module). The problem it exists for is not hypothetical and not rare:

* **csl-atlas** — ``build-r2-checkpoint-review.mjs --reseed`` skips
  ``loadPreserved`` and rewrites the review report with a machine-only seed,
  dropping every human ruling in it.
* **WhitneyRoots** — eleven ``scripts/dcs/apply_*.py`` writers open
  ``src/app_data.json`` with ``'w'`` and no lock, no reviewed gate, no backup.
* **pwg_ru** — 26 MB of cards behind a ``.gitignore``, four writers with no
  lock at all, one of which (``run_batch.py``) is the very code that *creates*
  the reviewer stamps it can also erase.

In every one of those cases the wipe is silent. The file still parses, the row
count barely moves, CI stays green, and a human notices months later that a
ruling they made is gone. That is the whole failure mode this module closes:
**the reviewed projection of a store gets a committed hash, and CI fails the
commit that changes it without saying so.**

## Why not a whole-file SHA-256

Because it was tried and it cried wolf. H2153: ``pwg_ru_translated.jsonl`` lost
1.29 MB at an *identical* row count — a serializer change, not a data loss. A
whole-file digest is red for every reformat and therefore gets ignored, which is
the same as not having one. So the gate is a **projection**: only the key fields
and the reviewed fields of the rows that the census predicate calls reviewed.
Whitespace, key order, field additions elsewhere in the record, and rows nobody
reviewed are all invisible to it. A dropped ``reviewer`` stamp is not.

## The two digests

``overlay_sha256`` answers *did the reviewed content change*.
``keyset_sha256`` answers *did the reviewed row set change*. Both are needed:
overwriting a reviewer's verdict in place leaves the key set untouched, and
deleting a reviewed row leaves the surviving content untouched. One digest
catches one of those.

## Hash contract (locked by
docs/ARCHITECTURE_UPRAVA_DATA_INTEGRITY_Q7_TRIPWIRES.md)

    json.dumps(records, sort_keys=True, ensure_ascii=False,
               separators=(',', ':')).encode('utf-8')

then ``sha256`` hex. UTF-8, LF, no BOM, compact separators, sorted keys — so a
serializer swap cannot move the digest.

## The predicate is data, not code

Each store's "a row is reviewed when…" rule lives in the Uprava census
(``data/integrity_tripwires.json``) and is copied verbatim into the ``spec``
block of each consumer's pin, because the census repo is private and CI cannot
read it. Three stores do not share a review stamp — pwg_ru has ``reviewer`` /
``review_status`` / ``editorial_decision*``, csl-atlas has ``reviewStatus`` plus
a *human* ``reviewer`` (H1684: an agent-attributed row must not claim human
review — 137 of 147 status-reviewed atlas rows are agent-attributed), and
WhitneyRoots has no per-row stamp at all and is reviewed file-level. Hardcoding
three predicates in three checkers is how they drift apart.

## Public API

``project(records, key_fields, reviewed_fields)``   canonical projection
``overlay_digest(projection)``                      SHA-256 of the content
``keyset_digest(projection, key_fields)``           SHA-256 of the key set
``is_reviewed(record, predicate)``                  the census predicate
``extract(spec, root)``                             read → filter → project
``check(extract_path, pin_path, root=None)``        0 match, 1 mismatch

CLI::

    python -m csl_pyutil.integrity_tripwire --check   --pin data/integrity/x.pin.json
    python -m csl_pyutil.integrity_tripwire --extract --pin data/integrity/x.pin.json --write-pin

A legitimate change bumps the pin **in the same commit** and writes a one-line
``reason``. That is the entire acknowledgement ritual — no sign-off file, no
second human. Auto-refreshing the pin would turn the tripwire into a changelog.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import sys

__all__ = [
    "TripwireError",
    "canonical_bytes",
    "project",
    "overlay_digest",
    "keyset_digest",
    "is_reviewed",
    "load_records",
    "extract",
    "build_pin",
    "check",
    "main",
]


class TripwireError(Exception):
    """A store cannot be projected at all — a defect, not a mismatch.

    Distinct from a digest mismatch on purpose. A mismatch is the tripwire
    doing its job and exits 1; a TripwireError means the spec and the data
    disagree about what the store even is (missing key field, colliding keys,
    unreadable container) and exits 2. Silently treating the second as the
    first would let a broken spec look like a clean store.
    """


# --------------------------------------------------------------------------
# canonical bytes and the two digests
# --------------------------------------------------------------------------

def canonical_bytes(obj):
    """The locked serialization. Every digest in this module goes through here."""
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _sha256(payload):
    return hashlib.sha256(payload).hexdigest()


def redact(value):
    """Replace a value with a digest of itself: ``sha256:<hex>``.

    The point is to keep a field *in* the tripwire while keeping its content
    *out* of git. pwg_ru's ``human_review`` is a reviewed field — a wipe of it
    is exactly what this module exists to catch — but it holds the curator's
    verbatim free-text notes, and the committed extract lives in a PUBLIC repo
    while the store it comes from is gitignored precisely because its bytes are
    not published. Storing the digest keeps every wipe detectable and publishes
    nothing: the hash moves the instant a single character does.
    """
    return "sha256:" + _sha256(canonical_bytes(value))


def project(records, key_fields, reviewed_fields, redact_fields=()):
    """Reduce each record to its key fields plus its reviewed fields.

    ``reviewed_fields`` may be ``"*"`` (or ``["*"]``) for file-level stores
    whose whole record is the reviewed content — WhitneyRoots' crosswalks have
    no per-field review stamp, so narrowing them would be inventing one.

    ``redact_fields`` names reviewed fields whose value is replaced by a digest
    of itself, for content that must be watched but must not be committed.

    A key field missing from a record is a TripwireError, not a ``None``: a row
    that cannot be keyed cannot be tracked, and quietly keying it as null would
    let two such rows collapse into one.
    """
    if reviewed_fields == "*":
        reviewed_fields = ["*"]
    star = list(reviewed_fields) == ["*"]
    redact_fields = set(redact_fields or ())
    if redact_fields & set(key_fields):
        raise TripwireError(
            "cannot redact a key field (%s) — the key set must stay legible"
            % (", ".join(sorted(redact_fields & set(key_fields))),)
        )

    out = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TripwireError(
                "record %d is %s, not an object" % (index, type(record).__name__)
            )
        projected = {}
        for field in key_fields:
            if field not in record:
                raise TripwireError(
                    "record %d has no key field %r (keys: %s)"
                    % (index, field, ", ".join(sorted(record)[:12]))
                )
            projected[field] = record[field]
        if star:
            for field, value in record.items():
                projected[field] = value
        else:
            for field in reviewed_fields:
                # An absent reviewed field is meaningful — it is exactly the
                # shape a wipe leaves behind — so it is recorded as absent
                # rather than skipped, and absence is part of the digest.
                projected[field] = record.get(field, None)
        for field in redact_fields:
            if field in projected and projected[field] is not None:
                projected[field] = redact(projected[field])
        out.append(projected)
    return out


def overlay_digest(projection):
    """SHA-256 over the reviewed content of every projected record.

    The projection is sorted into canonical order first, so **row order is not
    part of the digest**. This is deliberate: every writer in all three stores
    rewrites the file wholesale, and several of them reorder as a side effect
    (a rebuild that regroups by headword, a promote that appends). Row order
    carries no reviewed meaning in a keyed store, and a digest that moved on
    every reorder would be red so often it would be ignored — which is exactly
    how the whole-file SHA-256 failed on pwg_ru (H2153). Rows that ARE reviewed
    are proven unique by ``_assert_unique`` at extract time, so sorting them
    cannot fold two distinct rulings into one.
    """
    return _sha256(canonical_bytes(sorted(projection, key=canonical_bytes)))


def key_tuples(projection, key_fields):
    """The key set as a sorted list of value lists (JSON has no tuples)."""
    keys = [[record[field] for field in key_fields] for record in projection]
    return sorted(keys, key=canonical_bytes)


def keyset_digest(projection, key_fields):
    """SHA-256 over the sorted key set — catches a deleted or added row."""
    return _sha256(canonical_bytes(key_tuples(projection, key_fields)))


# --------------------------------------------------------------------------
# the census predicate, evaluated as data
# --------------------------------------------------------------------------

def _clause(record, clause):
    test = clause.get("test")

    if test == "truthy":
        return bool(record.get(clause["field"]))

    if test == "nonempty_string_not_prefixed":
        value = record.get(clause["field"])
        if not isinstance(value, str) or not value.strip():
            return False
        return not value.startswith(clause["prefix"])

    if test == "any_truthy":
        prefix = clause["field_prefix"]
        return any(
            bool(value) for field, value in record.items() if field.startswith(prefix)
        )

    if test == "in":
        return record.get(clause["field"]) in clause["values"]

    if test == "human_identity":
        # H1684. An unrecognised identity is NOT read as human: over-claiming
        # human review is the defect this test was written for. A genuinely new
        # human reviewer changes the key set, so CI still goes red and the
        # census gains the name in the same pass that bumps the pin.
        value = record.get(clause["field"])
        if not isinstance(value, str) or not value.strip():
            return False
        return value.strip() in set(clause.get("known_human", []))

    raise TripwireError("unknown predicate test %r" % (test,))


def is_reviewed(record, predicate):
    """Apply one census ``reviewed_predicate`` to one record.

    ``None``, ``{}`` or ``kind: file_level`` mean every record in the file is
    reviewed — that is WhitneyRoots, where reviewed-ness is a property of the
    file and AGENTS.md, not of a stamp inside the row.
    """
    if not predicate or predicate.get("kind") == "file_level":
        return True
    if "any_of" in predicate:
        return any(_clause(record, c) for c in predicate["any_of"])
    if "all_of" in predicate:
        return all(_clause(record, c) for c in predicate["all_of"])
    raise TripwireError("predicate has neither any_of, all_of nor kind: file_level")


# --------------------------------------------------------------------------
# readers
# --------------------------------------------------------------------------

def _dig(doc, path):
    """Walk a dotted ``records_at`` path down to the record list."""
    if not path:
        return doc
    node = doc
    for step in path.split("."):
        if not isinstance(node, dict) or step not in node:
            raise TripwireError("records_at %r: no %r here" % (path, step))
        node = node[step]
    return node


def load_records(path, container, records_at=""):
    """Read one source file into a list of dicts.

    Containers: ``jsonl`` (one object per line), ``json`` (``records_at``
    points at the list), ``csv`` (DictReader; every value stays a string —
    the digest is over what the file says, not over a guessed type).
    """
    if container == "jsonl":
        records = []
        with io.open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except ValueError as exc:
                    raise TripwireError("%s:%d is not JSON: %s" % (path, lineno, exc))
        return records

    if container == "json":
        with io.open(path, encoding="utf-8") as handle:
            doc = json.load(handle)
        records = _dig(doc, records_at)
        if not isinstance(records, list):
            raise TripwireError(
                "%s: records_at %r is %s, not a list"
                % (path, records_at, type(records).__name__)
            )
        return records

    if container == "csv":
        with io.open(path, encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    raise TripwireError("unknown container %r" % (container,))


# --------------------------------------------------------------------------
# spec handling
# --------------------------------------------------------------------------

def load_spec(path):
    """Accept either a bare spec document or a pin file that embeds one."""
    with io.open(path, encoding="utf-8") as handle:
        doc = json.load(handle)
    if isinstance(doc, dict) and isinstance(doc.get("spec"), dict):
        return doc["spec"], doc
    return doc, doc


def _source_settings(spec, source):
    """Per-source overrides fall back to the store-level defaults."""
    return (
        list(source.get("key_fields", spec["key_fields"])),
        source.get("reviewed_fields", spec.get("reviewed_fields", "*")),
        source.get("container", spec.get("container", "json")),
        source.get("records_at", ""),
        source.get("reviewed_predicate", spec.get("reviewed_predicate")),
        source.get("redact_fields", spec.get("redact_fields", ())),
    )


def _assert_unique(projection, key_fields, label):
    """Fail loudly on a colliding key.

    Required by the H2890 census: (key1, subcard, sense_tag) collides on 573 of
    11,603 pwg_ru rows and is collision-free only over the 5 rows that are
    reviewed today. If a future reviewed row lands inside a collision group,
    a row substitution inside that group is invisible to the key-set digest —
    so the extract refuses rather than pinning a digest it cannot defend.
    """
    seen = {}
    for record in projection:
        key = canonical_bytes([record[field] for field in key_fields])
        if key in seen:
            raise TripwireError(
                "%s: duplicate key %s among reviewed records — the key-set digest "
                "cannot tell those rows apart. Widen key_fields in the census."
                % (label, key.decode("utf-8"))
            )
        seen[key] = True


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------

def extract(spec, root=".", records_by_source=None):
    """Read every source, keep the reviewed records, project them.

    Returns ``(per_source, projection)`` where ``per_source`` is one dict per
    source carrying its own digests. Digests are computed per source and then
    rolled up, so a red CI job names the file that moved instead of one opaque
    hash for fourteen review reports.

    ``records_by_source`` lets a caller (the ``--check`` path for a gitignored
    store, and the tests) supply already-loaded records instead of reading the
    live file.
    """
    per_source = []
    combined = []
    for source in spec["sources"]:
        path = source["path"]
        (
            key_fields,
            reviewed_fields,
            container,
            records_at,
            predicate,
            redact_fields,
        ) = _source_settings(spec, source)
        if records_by_source is not None and path in records_by_source:
            records = records_by_source[path]
        else:
            full = os.path.join(root, path)
            if not os.path.exists(full):
                raise TripwireError("source file not found: %s" % (full,))
            records = load_records(full, container, records_at)

        reviewed = [r for r in records if is_reviewed(r, predicate)]
        projection = project(reviewed, key_fields, reviewed_fields, redact_fields)
        _assert_unique(projection, key_fields, path)

        per_source.append(
            {
                "path": path,
                "key_count": len(projection),
                "records_scanned": len(records),
                "overlay_sha256": overlay_digest(projection),
                "keyset_sha256": keyset_digest(projection, key_fields),
            }
        )
        combined.extend(projection)
    return per_source, combined


def _rollup(per_source, field):
    """One digest over the per-source digests, in declared source order."""
    return _sha256(
        canonical_bytes([{"path": s["path"], field: s[field]} for s in per_source])
    )


def build_pin(spec, per_source, reason, updated, store_id=None):
    """Assemble the pin sidecar from a fresh extract."""
    return {
        "store_id": store_id or spec.get("store_id"),
        "overlay_sha256": _rollup(per_source, "overlay_sha256"),
        "keyset_sha256": _rollup(per_source, "keyset_sha256"),
        "key_count": sum(s["key_count"] for s in per_source),
        "sources": [
            {
                "path": s["path"],
                "key_count": s["key_count"],
                "overlay_sha256": s["overlay_sha256"],
                "keyset_sha256": s["keyset_sha256"],
            }
            for s in per_source
        ],
        "reason": reason,
        "updated": updated,
        "source_gitignored": bool(spec.get("source_gitignored")),
        "spec": spec,
    }


def write_extract(path, projection):
    """Write the committed projection as JSONL, canonical bytes per line."""
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        for record in projection:
            handle.write(canonical_bytes(record).decode("utf-8"))
            handle.write("\n")


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------

def check(extract_path, pin_path, root=".", report=None):
    """Compare the store against its pin. 0 = match, 1 = mismatch.

    ``extract_path`` is used when the live store is gitignored and CI can only
    see the committed projection (pwg_ru). Pass ``None`` to re-derive from the
    live tracked sources (csl-atlas, WhitneyRoots).
    """
    lines = [] if report is None else report
    spec, pin = load_spec(pin_path)

    for field in ("overlay_sha256", "keyset_sha256"):
        if not pin.get(field):
            raise TripwireError(
                "%s has no %s — pin the baseline first "
                "(--extract --write-pin)" % (pin_path, field)
            )

    records_by_source = None
    if extract_path:
        if len(spec["sources"]) != 1:
            raise TripwireError(
                "an extract stands in for exactly one source; %s declares %d"
                % (pin_path, len(spec["sources"]))
            )
        if not os.path.exists(extract_path):
            raise TripwireError("extract not found: %s" % (extract_path,))
        # The extract holds already-projected records. Re-projecting them is a
        # no-op that also proves the extract still carries every field the spec
        # names — an extract built by an older spec fails here rather than
        # hashing to a value nobody can reproduce.
        records_by_source = {
            spec["sources"][0]["path"]: load_records(extract_path, "jsonl")
        }
        # The extract is the reviewed set already; re-filtering it through the
        # predicate would drop nothing but would fail file-level stores. Its
        # redacted fields are likewise already digests — hashing them a second
        # time would produce a value nothing can reproduce.
        spec = dict(spec)
        spec["sources"] = [dict(spec["sources"][0])]
        spec["sources"][0]["reviewed_predicate"] = None
        spec["sources"][0]["redact_fields"] = ()
        spec["sources"][0].pop("container", None)

    per_source, _ = extract(spec, root=root, records_by_source=records_by_source)
    fresh = {
        "overlay_sha256": _rollup(per_source, "overlay_sha256"),
        "keyset_sha256": _rollup(per_source, "keyset_sha256"),
        "key_count": sum(s["key_count"] for s in per_source),
    }

    bad = []
    for field in ("overlay_sha256", "keyset_sha256"):
        if fresh[field] != pin[field]:
            bad.append(field)

    if not bad:
        lines.append(
            "OK  %s — %d reviewed record(s) across %d source(s) match the pin "
            "(reason: %s, updated: %s)"
            % (
                pin.get("store_id"),
                fresh["key_count"],
                len(per_source),
                pin.get("reason"),
                pin.get("updated"),
            )
        )
        if report is None:
            _emit(lines)
        return 0

    lines.append("TRIPWIRE  %s — reviewed data changed without a pin bump." % (pin.get("store_id"),))
    lines.append(
        "  key_count  pinned %s -> now %s" % (pin.get("key_count"), fresh["key_count"])
    )
    for field in bad:
        lines.append("  %s  pinned %s" % (field, pin[field]))
        lines.append("  %s  now    %s" % (" " * len(field), fresh[field]))

    pinned_sources = {s["path"]: s for s in pin.get("sources", [])}
    for source in per_source:
        was = pinned_sources.get(source["path"])
        if was is None:
            lines.append("  + %s  (not in the pin)" % (source["path"],))
            continue
        moved = [
            f
            for f in ("overlay_sha256", "keyset_sha256")
            if was.get(f) != source[f]
        ]
        if moved:
            lines.append(
                "  ! %s  %s  (%d -> %d reviewed record(s))"
                % (
                    source["path"],
                    ", ".join(moved),
                    was.get("key_count", -1),
                    source["key_count"],
                )
            )
    for path in pinned_sources:
        if not any(s["path"] == path for s in per_source):
            lines.append("  - %s  (pinned but no longer in the spec)" % (path,))

    lines.append("")
    lines.append(
        "  If this change is intended, regenerate the pin IN THE SAME COMMIT and "
        "replace `reason` with one line saying what changed:"
    )
    lines.append(
        "    python -m csl_pyutil.integrity_tripwire --extract --pin %s "
        '--write-pin --reason "..."' % (pin_path,)
    )
    lines.append(
        "  If it is NOT intended, a human-reviewed overlay has just been "
        "overwritten. Do not bump the pin; restore the rows first."
    )
    if report is None:
        _emit(lines)
    return 1


def _emit(lines):
    for line in lines:
        print(line)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):  # pragma: no cover - 3.7+ only
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="python -m csl_pyutil.integrity_tripwire",
        description="Checksum + key-set tripwire on human-reviewed overlay data.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="compare store against pin")
    mode.add_argument("--extract", action="store_true", help="re-derive the projection")
    parser.add_argument("--pin", required=True, help="path to the pin sidecar")
    parser.add_argument("--root", default=".", help="repo root the spec paths are relative to")
    parser.add_argument(
        "--extract-path",
        default=None,
        help="committed projection to check instead of the live source "
        "(default: the spec's extract_path, when it declares one)",
    )
    parser.add_argument("--write-pin", action="store_true", help="--extract: rewrite the pin")
    parser.add_argument("--reason", default=None, help="--write-pin: one line saying what changed")
    parser.add_argument("--updated", default=None, help="--write-pin: DD-MM-YYYY")
    args = parser.parse_args(argv)

    try:
        spec, pin = load_spec(args.pin)
        declared = spec.get("extract_path") or ""

        if args.check:
            extract_path = args.extract_path
            if extract_path is None and declared:
                extract_path = os.path.join(args.root, declared)
            return check(extract_path, args.pin, root=args.root)

        per_source, projection = extract(spec, root=args.root)
        if declared:
            out = os.path.join(args.root, declared)
            write_extract(out, projection)
            print("wrote %s (%d reviewed record(s))" % (out, len(projection)))

        if args.write_pin:
            reason = args.reason or pin.get("reason")
            if not reason:
                parser.error("--write-pin needs --reason (or a reason already in the pin)")
            updated = args.updated or pin.get("updated")
            if not updated:
                parser.error("--write-pin needs --updated DD-MM-YYYY")
            fresh = build_pin(spec, per_source, reason, updated, pin.get("store_id"))
            with io.open(args.pin, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(fresh, handle, ensure_ascii=False, indent=2, sort_keys=False)
                handle.write("\n")
            print("pinned %s  overlay %s  keys %d"
                  % (args.pin, fresh["overlay_sha256"][:12], fresh["key_count"]))
        else:
            for source in per_source:
                print(
                    "%s  %d reviewed / %d scanned  overlay %s  keyset %s"
                    % (
                        source["path"],
                        source["key_count"],
                        source["records_scanned"],
                        source["overlay_sha256"][:12],
                        source["keyset_sha256"][:12],
                    )
                )
        return 0
    except TripwireError as exc:
        print("integrity_tripwire: %s" % (exc,), file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
