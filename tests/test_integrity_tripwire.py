# -*- coding: utf-8 -*-
"""H2891 — the overlay tripwire, tested against synthetic wipes.

A hasher-only unit test proves nothing here (plan decision 16): the question is
never "does sha256 work", it is "would this have caught the wipe that actually
happened". So every fixture in ``tests/fixtures/integrity/`` is a scale model of
a real incident:

* ``pwg_ru_preserve_rebuild.jsonl`` — a legitimate rebuild. Rows reordered, an
  unreviewed row added, unreviewed German text edited, records re-serialized
  with different key order and spacing, new pipeline fields attached. The
  reviewed projection is untouched, so the gate must stay GREEN. This is the
  H2153 false-alarm case that killed the whole-file SHA-256.
* ``pwg_ru_field_overwrite.jsonl`` — a reviewer's ``review_status`` overwritten
  with ``ai_translated`` at an identical row count and identical key set. Only
  the overlay digest moves. This is the shape a promote without
  ``--override-reviewed`` would leave.
* ``pwg_ru_keyset_shrink.jsonl`` — the ``editorial_decision`` stamps stripped
  off a row, so it stops being reviewed at all. The key set shrinks 2 -> 1.
* ``atlas_review_reseeded.json`` — ``build-r2-checkpoint-review.mjs --reseed``
  in miniature: the human rulings are reset to ``pending`` while the two
  agent-attributed rows survive untouched. Both digests move.

The baseline fixture also carries a deliberate key collision between two
UNREVIEWED rows (``dah``/``dah-1``/``s3`` twice), because the live pwg_ru store
has 573 of them. Collisions outside the reviewed set must be tolerated;
a collision inside it must refuse.
"""
import io
import json
import os
import shutil

import pytest

from csl_pyutil import integrity_tripwire as it
from csl_pyutil.integrity_tripwire import (
    TripwireError,
    build_pin,
    canonical_bytes,
    check,
    extract,
    is_reviewed,
    keyset_digest,
    overlay_digest,
    project,
)

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "integrity")

PWG_PREDICATE = {
    "any_of": [
        {"field": "reviewer", "test": "truthy"},
        {"field": "review_status", "test": "nonempty_string_not_prefixed", "prefix": "ai_"},
        {"field_prefix": "editorial_decision", "test": "any_truthy"},
    ]
}

ATLAS_PREDICATE = {
    "all_of": [
        {"field": "reviewStatus", "test": "in", "values": ["reviewed-ok", "reviewed-corrected"]},
        {
            "field": "reviewer",
            "test": "human_identity",
            "known_human": ["gasyoun"],
            "known_agent": ["codex", "Antigravity"],
        },
    ]
}


def _pwg_spec(store_file="store.jsonl", extract_path=""):
    return {
        "store_id": "pwg_ru_fixture",
        "source_gitignored": bool(extract_path),
        "extract_path": extract_path,
        "key_fields": ["key1", "subcard", "sense_tag"],
        "reviewed_fields": ["reviewer", "review_status", "human_review"],
        "reviewed_predicate": PWG_PREDICATE,
        "sources": [{"path": store_file, "container": "jsonl"}],
    }


def _atlas_spec(store_file="review.json"):
    return {
        "store_id": "atlas_fixture",
        "source_gitignored": False,
        "extract_path": "",
        "key_fields": ["queue", "reviewId"],
        "reviewed_fields": ["reviewStatus", "reviewedValue", "reviewer", "reviewedAt", "note"],
        "reviewed_predicate": ATLAS_PREDICATE,
        "sources": [{"path": store_file, "container": "json", "records_at": "items"}],
    }


def _whitney_spec():
    return {
        "store_id": "whitney_fixture",
        "source_gitignored": False,
        "extract_path": "",
        "key_fields": ["id", "root"],
        "reviewed_fields": ["id", "root", "meaning", "ppp", "ppp_uncertain"],
        "reviewed_predicate": {"kind": "file_level"},
        "sources": [
            {"path": "app_data.json", "container": "json", "records_at": "lexicon"},
            {
                "path": "roots.csv",
                "container": "csv",
                "key_fields": ["whitney_no"],
                "reviewed_fields": "*",
            },
        ],
    }


def _repo(tmp_path, mapping):
    """Build a throwaway repo root out of fixture copies."""
    root = tmp_path / "repo"
    root.mkdir(exist_ok=True)
    for dest, fixture in mapping.items():
        shutil.copyfile(os.path.join(FIXTURES, fixture), str(root / dest))
    return str(root)


def _pin_at(root, spec, reason="wave-1-baseline", updated="17-08-2026", name="store.pin.json"):
    per_source, _ = extract(spec, root=root)
    pin = build_pin(spec, per_source, reason, updated)
    path = os.path.join(root, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(pin, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def _swap(root, name, fixture):
    shutil.copyfile(os.path.join(FIXTURES, fixture), os.path.join(root, name))


# --------------------------------------------------------------------------
# hash contract
# --------------------------------------------------------------------------

def test_canonical_bytes_are_the_locked_serialization():
    assert canonical_bytes({"b": 1, "a": "ā"}) == '{"a":"ā","b":1}'.encode("utf-8")


def test_digests_ignore_serializer_whitespace_and_key_order():
    a = [{"k": "agni", "reviewer": "gasyoun"}]
    b = [{"reviewer": "gasyoun", "k": "agni"}]
    assert overlay_digest(a) == overlay_digest(b)


def test_overlay_digest_ignores_row_order_but_not_content():
    rows = [{"k": "a", "r": "x"}, {"k": "b", "r": "y"}]
    assert overlay_digest(rows) == overlay_digest(list(reversed(rows)))
    assert overlay_digest(rows) != overlay_digest([{"k": "a", "r": "x"}, {"k": "b", "r": "z"}])


def test_keyset_digest_moves_only_with_the_key_set():
    rows = [{"k": "a", "r": "x"}, {"k": "b", "r": "y"}]
    same_keys_new_content = [{"k": "a", "r": "CHANGED"}, {"k": "b", "r": "y"}]
    assert keyset_digest(rows, ["k"]) == keyset_digest(same_keys_new_content, ["k"])
    assert keyset_digest(rows, ["k"]) != keyset_digest(rows[:1], ["k"])


def test_project_keeps_only_key_and_reviewed_fields():
    got = project(
        [{"k": "a", "reviewer": "gasyoun", "de": "Feuer", "pc_all": [1]}], ["k"], ["reviewer"]
    )
    assert got == [{"k": "a", "reviewer": "gasyoun"}]


def test_project_records_an_absent_reviewed_field_as_none():
    # A wipe often leaves the field gone rather than emptied; absence must be
    # part of the digest, not skipped.
    got = project([{"k": "a"}], ["k"], ["reviewer"])
    assert got == [{"k": "a", "reviewer": None}]
    assert overlay_digest(got) != overlay_digest(project([{"k": "a", "reviewer": "x"}], ["k"], ["reviewer"]))


def test_project_refuses_a_record_with_no_key_field():
    with pytest.raises(TripwireError) as exc:
        project([{"reviewer": "gasyoun"}], ["k"], ["reviewer"])
    assert "key field" in str(exc.value)


def test_star_reviewed_fields_projects_the_whole_record():
    got = project([{"whitney_no": "1", "root": "aṃś", "note": ""}], ["whitney_no"], "*")
    assert got == [{"whitney_no": "1", "root": "aṃś", "note": ""}]


# --------------------------------------------------------------------------
# predicates
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "record,expected",
    [
        ({"reviewer": "gasyoun"}, True),
        ({"reviewer": "", "review_status": "ai_translated"}, False),
        ({"review_status": "human_ok"}, True),
        ({"review_status": "ai_edited"}, False),
        ({"review_status": "ai_reviewed", "editorial_decision": "keep"}, True),
        ({"review_status": ""}, False),
        ({"reviewer": None, "review_status": "ai_reviewed"}, False),
        ({"editorial_decision_at": "2026-08-01"}, True),
    ],
)
def test_pwg_predicate_matches_human_touched(record, expected):
    assert is_reviewed(record, PWG_PREDICATE) is expected


def test_atlas_predicate_refuses_agent_attribution():
    """H1684 — 137 of 147 status-reviewed atlas rows carry an agent identity."""
    human = {"reviewStatus": "reviewed-ok", "reviewer": "gasyoun"}
    agent = {"reviewStatus": "reviewed-ok", "reviewer": "codex"}
    unknown = {"reviewStatus": "reviewed-ok", "reviewer": "some-new-bot"}
    pending = {"reviewStatus": "pending", "reviewer": "gasyoun"}
    assert is_reviewed(human, ATLAS_PREDICATE) is True
    assert is_reviewed(agent, ATLAS_PREDICATE) is False
    assert is_reviewed(unknown, ATLAS_PREDICATE) is False
    assert is_reviewed(pending, ATLAS_PREDICATE) is False


def test_file_level_predicate_reviews_everything():
    assert is_reviewed({"anything": 1}, {"kind": "file_level"}) is True
    assert is_reviewed({"anything": 1}, None) is True


def test_unknown_predicate_test_is_an_error_not_a_false():
    with pytest.raises(TripwireError):
        is_reviewed({"x": 1}, {"any_of": [{"field": "x", "test": "vibes"}]})


# --------------------------------------------------------------------------
# the four acceptance gates
# --------------------------------------------------------------------------

def test_preserve_rebuild_is_green(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    pin = _pin_at(root, spec)

    _swap(root, "store.jsonl", "pwg_ru_preserve_rebuild.jsonl")
    report = []
    assert check(None, pin, root=root, report=report) == 0
    assert "OK" in report[0]


def test_reviewed_field_overwrite_is_red(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    pin = _pin_at(root, spec)

    _swap(root, "store.jsonl", "pwg_ru_field_overwrite.jsonl")
    report = []
    assert check(None, pin, root=root, report=report) == 1
    blob = "\n".join(report)
    assert "TRIPWIRE" in blob
    assert "overlay_sha256" in blob
    # identical key count and key set — only the content moved
    assert "keyset_sha256  pinned" not in blob
    assert "pinned 2 -> now 2" in blob


def test_keyset_shrink_is_red(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    pin = _pin_at(root, spec)

    _swap(root, "store.jsonl", "pwg_ru_keyset_shrink.jsonl")
    report = []
    assert check(None, pin, root=root, report=report) == 1
    blob = "\n".join(report)
    assert "keyset_sha256" in blob
    assert "pinned 2 -> now 1" in blob


def test_pin_bumped_to_the_new_hash_is_green(tmp_path):
    """The whole acknowledgement ritual: re-pin in the same commit with a reason."""
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    pin = _pin_at(root, spec)
    _swap(root, "store.jsonl", "pwg_ru_field_overwrite.jsonl")
    assert check(None, pin, root=root, report=[]) == 1

    _pin_at(root, spec, reason="agni-1 downgraded to ai_translated on purpose")
    report = []
    assert check(None, pin, root=root, report=report) == 0
    assert "agni-1 downgraded" in report[0]


def test_atlas_reseed_is_red_and_names_the_file(tmp_path):
    root = _repo(tmp_path, {"review.json": "atlas_review_baseline.json"})
    spec = _atlas_spec()
    pin = _pin_at(root, spec)

    per_source, _ = extract(spec, root=root)
    assert per_source[0]["key_count"] == 2, "only the two gasyoun rows are human-reviewed"
    assert per_source[0]["records_scanned"] == 5

    _swap(root, "review.json", "atlas_review_reseeded.json")
    report = []
    assert check(None, pin, root=root, report=report) == 1
    blob = "\n".join(report)
    assert "review.json" in blob
    assert "pinned 2 -> now 0" in blob


# --------------------------------------------------------------------------
# the mutation gate — plan decision 16
# --------------------------------------------------------------------------

def test_mutation_a_hasher_that_drops_a_reviewed_field_goes_blind(tmp_path):
    """If someone shortens `reviewed_fields`, the tripwire stops seeing the wipe.

    This is the mutation the plan demands a test for. The full contract
    distinguishes baseline from the field-overwrite wipe; a hasher missing
    ``review_status`` cannot — it returns the *same* digest for both, i.e. a
    green CI over overwritten reviewer data. The assertions below fail the
    moment ``review_status`` leaves the projection, so the contract cannot be
    narrowed by accident.
    """
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    full = spec["reviewed_fields"]
    mutated = [f for f in full if f != "review_status"]
    assert len(mutated) == len(full) - 1

    baseline = it.load_records(os.path.join(root, "store.jsonl"), "jsonl")
    _swap(root, "store.jsonl", "pwg_ru_field_overwrite.jsonl")
    wiped = it.load_records(os.path.join(root, "store.jsonl"), "jsonl")

    keys = spec["key_fields"]
    reviewed_before = [r for r in baseline if is_reviewed(r, PWG_PREDICATE)]
    reviewed_after = [r for r in wiped if is_reviewed(r, PWG_PREDICATE)]

    intact = overlay_digest(project(reviewed_before, keys, full))
    intact_after = overlay_digest(project(reviewed_after, keys, full))
    assert intact != intact_after, "the locked contract must see the overwrite"

    blind = overlay_digest(project(reviewed_before, keys, mutated))
    blind_after = overlay_digest(project(reviewed_after, keys, mutated))
    assert blind == blind_after, (
        "a projection without review_status cannot see the overwrite — this is "
        "why the field list is locked in the census, not chosen per repo"
    )


def test_mutation_a_status_only_atlas_predicate_overclaims(tmp_path):
    """Dropping the H1684 human-identity half inflates the reviewed set."""
    root = _repo(tmp_path, {"review.json": "atlas_review_baseline.json"})
    records = it.load_records(os.path.join(root, "review.json"), "json", "items")
    locked = [r for r in records if is_reviewed(r, ATLAS_PREDICATE)]
    status_only = [
        r
        for r in records
        if is_reviewed(r, {"any_of": [ATLAS_PREDICATE["all_of"][0]]})
    ]
    assert len(locked) == 2
    assert len(status_only) == 4, "status alone over-claims human review 2x here"


# --------------------------------------------------------------------------
# key uniqueness — the H2890 census requirement
# --------------------------------------------------------------------------

def test_collisions_among_unreviewed_rows_are_tolerated(tmp_path):
    """The live store has 573 colliding keys; none of them is reviewed."""
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    per_source, projection = extract(_pwg_spec(), root=root)
    assert per_source[0]["records_scanned"] == 6
    assert len(projection) == 2


def test_a_reviewed_row_on_a_colliding_key_refuses_loudly(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    path = os.path.join(root, "store.jsonl")
    with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(
                {
                    "key1": "agni",
                    "subcard": "agni-1",
                    "sense_tag": "s1",
                    "reviewer": "gasyoun",
                    "review_status": "human_ok",
                    "de": "a second reviewed row on the same key",
                },
                ensure_ascii=False,
            )
            + "\n"
        )
    with pytest.raises(TripwireError) as exc:
        extract(_pwg_spec(), root=root)
    assert "duplicate key" in str(exc.value)


# --------------------------------------------------------------------------
# the gitignored-store path: extract + check against the committed projection
# --------------------------------------------------------------------------

def test_extract_then_check_without_the_live_store(tmp_path):
    """pwg_ru's CI shape: the live 26 MB store is gitignored and absent."""
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec(extract_path="data/integrity/overlay.jsonl")
    per_source, projection = extract(spec, root=root)
    out = os.path.join(root, spec["extract_path"])
    it.write_extract(out, projection)
    pin = _pin_at(root, spec)

    os.remove(os.path.join(root, "store.jsonl"))
    assert check(out, pin, root=root, report=[]) == 0


def test_a_tampered_extract_is_red_even_with_the_live_store_gone(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec(extract_path="data/integrity/overlay.jsonl")
    per_source, projection = extract(spec, root=root)
    out = os.path.join(root, spec["extract_path"])
    it.write_extract(out, projection)
    pin = _pin_at(root, spec)
    os.remove(os.path.join(root, "store.jsonl"))

    rows = it.load_records(out, "jsonl")
    rows[0]["reviewer"] = ""
    it.write_extract(out, rows)
    assert check(out, pin, root=root, report=[]) == 1


def test_extract_written_as_lf_utf8_without_bom(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec(extract_path="data/integrity/overlay.jsonl")
    _, projection = extract(spec, root=root)
    out = os.path.join(root, spec["extract_path"])
    it.write_extract(out, projection)
    raw = io.open(out, "rb").read()
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")


# --------------------------------------------------------------------------
# multi-source stores
# --------------------------------------------------------------------------

def test_multi_source_pin_names_the_file_that_moved(tmp_path):
    root = _repo(
        tmp_path,
        {"app_data.json": "whitney_app_data.json", "roots.csv": "whitney_roots.csv"},
    )
    spec = _whitney_spec()
    pin = _pin_at(root, spec)

    with io.open(os.path.join(root, "app_data.json"), encoding="utf-8") as handle:
        doc = json.load(handle)
    doc["lexicon"][1]["ppp"] = ""          # an apply_* script blanking a reviewed field
    doc["metadata"]["built"] = "2026-08-17"  # untracked metadata churn, must be invisible
    with io.open(os.path.join(root, "app_data.json"), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(doc, handle, ensure_ascii=False, indent=2)

    report = []
    assert check(None, pin, root=root, report=report) == 1
    blob = "\n".join(report)
    assert "app_data.json" in blob
    assert "roots.csv" not in blob, "the untouched source must not be blamed"


def test_file_level_store_counts_every_record(tmp_path):
    root = _repo(
        tmp_path,
        {"app_data.json": "whitney_app_data.json", "roots.csv": "whitney_roots.csv"},
    )
    per_source, projection = extract(_whitney_spec(), root=root)
    assert [s["key_count"] for s in per_source] == [3, 3]
    assert len(projection) == 6


def test_an_extract_cannot_stand_in_for_a_multi_source_store(tmp_path):
    root = _repo(
        tmp_path,
        {"app_data.json": "whitney_app_data.json", "roots.csv": "whitney_roots.csv"},
    )
    spec = _whitney_spec()
    pin = _pin_at(root, spec)
    with pytest.raises(TripwireError) as exc:
        check(os.path.join(root, "app_data.json"), pin, root=root)
    assert "exactly one source" in str(exc.value)


# --------------------------------------------------------------------------
# pin hygiene
# --------------------------------------------------------------------------

def test_an_unpinned_baseline_refuses_rather_than_passing(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    path = os.path.join(root, "store.pin.json")
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"store_id": "pwg_ru_fixture", "spec": spec}, handle)
    with pytest.raises(TripwireError) as exc:
        check(None, path, root=root)
    assert "pin the baseline first" in str(exc.value)


def test_pin_carries_its_own_spec_so_ci_needs_no_private_census(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    pin_path = _pin_at(root, _pwg_spec())
    with io.open(pin_path, encoding="utf-8") as handle:
        pin = json.load(handle)
    assert pin["spec"]["reviewed_predicate"] == PWG_PREDICATE
    assert pin["key_count"] == 2
    assert len(pin["overlay_sha256"]) == 64
    assert pin["reason"] == "wave-1-baseline"


def test_missing_source_is_an_error_not_a_silent_pass(tmp_path):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    pin = _pin_at(root, _pwg_spec())
    os.remove(os.path.join(root, "store.jsonl"))
    with pytest.raises(TripwireError) as exc:
        check(None, pin, root=root)
    assert "not found" in str(exc.value)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def test_cli_check_returns_zero_then_one(tmp_path, capsys):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    pin = _pin_at(root, _pwg_spec())
    assert it.main(["--check", "--pin", pin, "--root", root]) == 0
    _swap(root, "store.jsonl", "pwg_ru_field_overwrite.jsonl")
    assert it.main(["--check", "--pin", pin, "--root", root]) == 1
    assert "TRIPWIRE" in capsys.readouterr().out


def test_cli_extract_write_pin_round_trips(tmp_path, capsys):
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec(extract_path="data/integrity/overlay.jsonl")
    pin = os.path.join(root, "store.pin.json")
    with io.open(pin, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"store_id": "pwg_ru_fixture", "spec": spec}, handle)

    rc = it.main(
        ["--extract", "--pin", pin, "--root", root, "--write-pin",
         "--reason", "wave-1-baseline", "--updated", "17-08-2026"]
    )
    assert rc == 0
    assert os.path.exists(os.path.join(root, spec["extract_path"]))
    assert it.main(["--check", "--pin", pin, "--root", root]) == 0
    assert "OK" in capsys.readouterr().out


def test_cli_reports_a_broken_spec_as_exit_two(tmp_path, capsys):
    """A defect must not look like a clean store, and must not look like a wipe."""
    root = _repo(tmp_path, {"store.jsonl": "pwg_ru_baseline.jsonl"})
    spec = _pwg_spec()
    spec["key_fields"] = ["no_such_field"]
    pin = os.path.join(root, "store.pin.json")
    with io.open(pin, "w", encoding="utf-8", newline="\n") as handle:
        json.dump({"store_id": "x", "spec": spec, "overlay_sha256": "0" * 64,
                   "keyset_sha256": "0" * 64}, handle)
    assert it.main(["--check", "--pin", pin, "--root", root]) == 2
    assert "integrity_tripwire:" in capsys.readouterr().err


def test_public_api_is_exported_from_the_package():
    import csl_pyutil

    for name in ("project", "overlay_digest", "keyset_digest", "check", "extract",
                 "is_reviewed", "TripwireError", "integrity_tripwire"):
        assert hasattr(csl_pyutil, name), name
