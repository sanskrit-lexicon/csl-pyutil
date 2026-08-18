# -*- coding: utf-8 -*-
"""V9 (evidence reuse) + V10 (no non-decisions) — H1889.

The detector-level assertions are the donor's own selftest, lifted with the code
from SanskritLexicography/RussianTranslation/src/review_evidence_preflight.py so
the lift is provably faithful; the rest exercises the emitter wiring.
"""
import warnings

import pytest

from csl_pyutil import evidence
from csl_pyutil.evidence import (EvidenceManifest, PreflightError, PreflightWarning,
                                 find_mixed_script, find_slp1, preflight,
                                 sutra_href, sutra_is_possible, valid_sutras)
from csl_pyutil.review_sheet import render_review_sheet


def _screening(n_human):
    return {"deterministic": 0, "lookup": 0, "agent": 0, "human": n_human,
            "evidence_path": "tests/fixture_screening.md", "rules": ["none"]}


def _config(**overrides):
    cfg = {"sheet_id": "test-sheet_h1889", "title": "Test Sheet",
           "subtitle": "a test sheet", "footer": "Approve/Reject/Defer per item.",
           "approve_label": "Approve", "reject_label": "Reject",
           "filters": [("a", "A")], "generated": "2026-07-29",
           # the repo scan is exercised on its own below; the wiring tests do not
           # need to walk a checkout
           "preflight": {"skip_prior_art": True},
           # this file is about V9/V10; neutralize the unrelated V13 identity-gate
           # warning (H2854) so it does not add a second recorded warning here —
           # V13 gets its own tests/test_identity_gate.py
           "identity_gate": {"patterns": [r"nomatch\d+"], "labels": {}}}
    cfg.update(overrides)
    return cfg


_ID_POOL = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"]


def _items(n=2, **extra):
    out = []
    # alphabetic ids: EvidenceManifest.scan_prior_art tokenizes on [A-Za-z~]+, so a
    # digit-suffixed id is invisible to the overlap scan (a donor property this port
    # deliberately preserves rather than "fixes")
    for i in range(n):
        it = {"id": _ID_POOL[i], "filt": "a", "title": "item %d" % i,
              "question": "keep it?", "panels": [("Panel", "<pre>body</pre>")]}
        it.update(extra)
        out.append(it)
    return out


def _manifest(items, repo_root, min_evidence_fields=1):
    man = EvidenceManifest("test-sheet_h1889", [it["id"] for it in items],
                           repo_root=str(repo_root),
                           min_evidence_fields=min_evidence_fields)
    for it in items:
        man.add_card(it["id"], ["verdict"])
    return man


def _render(items, config, **kw):
    kw.setdefault("screening", _screening(len(items)))
    return render_review_sheet(items, config, **kw)


# --------------------------------------------------------------- lifted selftest
def test_donor_selftest_passes_unchanged():
    assert evidence.selftest().startswith("selftest OK")


def test_sutra_structural_validity():
    assert sutra_is_possible(4, 1, 104)
    assert not sutra_is_possible(9, 21, 22)
    assert not sutra_is_possible(1, 12, 28)
    assert not sutra_is_possible(10, 85, 38)      # RV 10.85.38, not a sutra
    good, bad = valid_sutras('P.4.1.104|P.6.5|P.6.5.1|P.8.11.21|P.9.6.24')
    assert good == ['4.1.104']
    assert bad == ['6.5', '6.5.1', '8.11.21', '9.6.24']
    assert sutra_href('4.1.104') == 'https://ashtadhyayi.com/sutraani/4/1/104'
    assert sutra_href('4.1') == 'https://ashtadhyayi.com/sutraani/4/1'
    assert sutra_href('4') is None


def test_mixed_script_and_slp1_detectors():
    assert find_mixed_script('Пāṇini:') == ['Пā']
    assert find_mixed_script('Панини') == [] and find_mixed_script('Pāṇini') == []
    assert find_slp1('PWG-членение: bfhant + kAya') == ['bfhant', 'kAya']
    assert find_slp1('членение: bṛhant + kāya') == []
    assert find_slp1('votes persist to localStorage in RussianTranslation') == []
    assert find_slp1('akzarajIvika') == ['akzarajIvika']
    assert find_slp1('duHsTita and kAya', allow=['duHsTita']) == ['kAya']
    # the undecidable all-lowercase case stays undecided, by design
    assert find_slp1('agni + deva') == []


def test_conceptual_omission_cannot_silence_a_found_artifact(tmp_path):
    """The deliberate asymmetry: only declare_omitted_path() clears a real file."""
    (tmp_path / "adjudication.tsv").write_text("id\tverdict\nalpha\tkeep\n",
                                               encoding="utf-8")
    man = EvidenceManifest("t", ["alpha"], repo_root=str(tmp_path),
                           min_evidence_fields=1)
    man.add_card("alpha", ["x"])
    man.declare_omitted("adjudication.tsv",
                        because="a conceptual note must not clear a real file")
    with pytest.raises(PreflightError) as err:
        preflight(man, "<p>ok</p>")
    assert "PRIOR ART NOT JOINED" in str(err.value)

    man.declare_omitted_path("adjudication.tsv",
                             because="superseded by the H1681 rerun, kept for audit")
    assert preflight(man, "<p>ok</p>")["prior_art_undeclared"] == []


def test_evidence_floor_blocks_and_a_stated_reason_clears_it(tmp_path):
    man = EvidenceManifest("t", ["a", "b"], repo_root=str(tmp_path))
    man.add_card("a", ["x", "y"])
    man.add_card("b", [])
    with pytest.raises(PreflightError, match="EVIDENCE FLOOR"):
        preflight(man, "<p>ok</p>", skip_prior_art=True)
    man.add_card("b", [], omitted=["no DCS sentence map exists at compound level"])
    assert preflight(man, "<p>ok</p>", skip_prior_art=True)["evidence_starved"] == []


# ------------------------------------------------------------------- V9 wiring
def test_v9_missing_manifest_warns_with_the_reason():
    with pytest.warns(PreflightWarning) as rec:
        _render(_items(), _config())
    msg = str(rec[0].message)
    assert "test-sheet_h1889" in msg and "manifest=" in msg
    assert "EvidenceManifest" in msg and "1.0.0" in msg


def test_v9_manifest_passes_a_clean_sheet(tmp_path):
    items = _items()
    with warnings.catch_warnings():
        warnings.simplefilter("error", PreflightWarning)   # must not warn
        doc = _render(items, _config(), manifest=_manifest(items, tmp_path))
    assert "<!DOCTYPE html>" in doc


def test_v9_raises_before_returning_html(tmp_path):
    """A sheet whose manifest omits a real overlapping artifact must RAISE."""
    (tmp_path / "adjudication.tsv").write_text(
        "id\tverdict\nalpha\tkeep\nbeta\tdrop\n", encoding="utf-8")
    items = _items()
    man = _manifest(items, tmp_path)
    cfg = _config(preflight={"overlap_threshold": 0.5})
    with pytest.raises(PreflightError) as err:
        _render(items, cfg, manifest=man)
    assert "PRIOR ART NOT JOINED" in str(err.value)

    man.declare_joined("adjudication.tsv", ["verdict"])
    assert "<!DOCTYPE html>" in _render(items, cfg, manifest=man)


def test_v9_sees_the_finished_localized_document(tmp_path):
    """The gate runs after ui_strings, so a translation that leaks SLP1 blocks."""
    items = _items()
    cfg = _config(ui_strings={"defer_button": "Отложить kAya"})
    with pytest.raises(PreflightError, match="SLP1 IN HUMAN-FACING TEXT"):
        _render(items, cfg, manifest=_manifest(items, tmp_path))


def test_v9_rejects_an_unknown_preflight_key(tmp_path):
    items = _items()
    with pytest.raises(ValueError, match="unknown config\\['preflight'\\] key"):
        _render(items, _config(preflight={"skip_prior_are": True}),
                manifest=_manifest(items, tmp_path))


def test_v9_donor_path_is_silent_but_still_gated(tmp_path):
    """extras=False reproduces a historical shell — no migration nag — yet a
    manifest passed there is still enforced."""
    items = _items()
    cfg = _config()
    with warnings.catch_warnings():
        warnings.simplefilter("error", PreflightWarning)
        render_review_sheet(items, cfg, extras=False)
    man = EvidenceManifest("t", [it["id"] for it in items], repo_root=str(tmp_path),
                           min_evidence_fields=2)
    man.add_card("alpha", ["verdict"])
    with pytest.raises(PreflightError, match="EVIDENCE FLOOR"):
        render_review_sheet(items, cfg, extras=False, manifest=man)


# ------------------------------------------------------------------ V10 wiring
def test_v10_blocks_a_machine_resolvable_card_by_default():
    items = _items(4)
    items[0]["machine_resolvable"] = True
    with pytest.raises(PreflightError) as err:
        _render(items, _config())
    assert "NON-DECISIONS" in str(err.value) and "alpha" in str(err.value)


def test_v10_threshold_is_caller_tunable():
    items = _items(4)
    items[0]["machine_resolvable"] = True          # 25 %
    with pytest.warns(PreflightWarning):
        assert "<!DOCTYPE html>" in _render(items, _config(non_decision_share=0.25))
    items[1]["machine_resolvable"] = True          # 50 %
    with pytest.raises(PreflightError, match="NON-DECISIONS"):
        _render(items, _config(non_decision_share=0.25))


def test_v10_is_vacuous_for_an_unflagged_sheet():
    with pytest.warns(PreflightWarning):
        assert "<!DOCTYPE html>" in _render(_items(3), _config())


def test_v10_rejects_a_nonsense_threshold():
    for bad, exc in ((True, TypeError), ("0.5", TypeError), (1.5, ValueError),
                     (-0.1, ValueError)):
        with pytest.raises(exc):
            _render(_items(), _config(non_decision_share=bad))


def test_v10_applies_to_the_donor_path_too():
    items = _items(2)
    items[0]["machine_resolvable"] = True
    with pytest.raises(PreflightError, match="NON-DECISIONS"):
        render_review_sheet(items, _config(), extras=False)


# ------------------------------------------------- the two untranslatable strings
def test_defer_button_and_reject_reason_localise():
    items = _items(2)
    cfg = _config(reject_labels=[("terminology", "терминология"), ("style", "стиль")])
    with pytest.warns(PreflightWarning):
        plain = _render(items, cfg)
    assert '<button class="vote defer" data-vote="defer">&#9208; Defer</button>' in plain
    assert ">Reason</span>" in plain

    cfg = _config(reject_labels=[("terminology", "терминология"), ("style", "стиль")],
                  ui_strings={"defer_button": "Отложить", "reject_reason_label": "Причина"})
    with pytest.warns(PreflightWarning):
        ru = _render(items, cfg)
    # every card, not just the first
    assert ru.count('data-vote="defer">&#9208; Отложить</button>') == len(items)
    assert ru.count(">Причина</span>") == len(items)
    assert ">Defer</button>" not in ru and ">Reason</span>" not in ru
    # the surrounding markup survives untouched
    assert '<button class="vote defer" data-vote="defer">' in ru
    assert 'class="rejectlabellabel"' in ru
    # the H779 legend's own "Defer" explanation is a different string and stays
    assert "<b>Defer</b>" in ru


# ------------------------------------------------------- scratch dirs are not prior art (H2991)

def test_scan_prior_art_skips_agent_worktrees(tmp_path):
    """A scratch checkout is not prior art — it is the same art seen twice.

    Measured 18-08-2026: two stale worktrees under `.claude/worktrees/` made the
    500-card BLI gold sheet unbuildable with 13 blocking findings, every one a
    COPY of a file the manifest had already declared.
    """
    from csl_pyutil.evidence import EvidenceManifest

    # the scanner tokenizes on [A-Za-z~]{3,}, so ids must be letters
    ids = ["rowid" + chr(ord("a") + i // 26) + chr(ord("a") + i % 26)
           for i in range(60)]
    body = "\n".join(ids)

    real = tmp_path / "data"
    real.mkdir()
    (real / "crosswalk.tsv").write_text(body, encoding="utf-8")

    for scratch in (".claude/worktrees/agent-abc/data",
                    ".venv/lib/site-packages/pkg",
                    "node_modules/thing",
                    "build/lib/data"):
        d = tmp_path / scratch
        d.mkdir(parents=True)
        (d / "crosswalk.tsv").write_text(body, encoding="utf-8")

    man = EvidenceManifest(sheet_id="s", row_ids=ids, repo_root=str(tmp_path))
    hits = [h[0] for h in man.scan_prior_art(threshold=0.5)]

    assert "data/crosswalk.tsv" in hits, "the real artifact must still be found"
    for bad in (".claude", ".venv", "node_modules", "build"):
        assert not any(h.startswith(bad) for h in hits), \
            "%s was scanned; scratch/dependency trees are not prior art (%s)" % (bad, hits)
