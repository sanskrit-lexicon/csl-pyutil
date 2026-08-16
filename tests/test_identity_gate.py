# -*- coding: utf-8 -*-
"""V13 (H2854 step 2) — identity gate. MG, gating the BookIndex crosswalk
sheets (H2841/H2842): a card that names an internal id without also naming
the human identity behind it lets a reviewer vote on a bare token. Named V13,
not the plan's original "V12" — H2858 (merged the same day) already claimed
V12 for the partial hand-in + pause layer.
"""
import pytest

from csl_pyutil.evidence import PreflightError, PreflightWarning
from test_review_sheet import _config, _items, render_review_sheet
from csl_pyutil import render_review_sheet as _render_raw


def _items_with_ids():
    return [
        {"id": "L1", "filt": "a", "title": "item one",
         "question": "Is acc001 (А.А. Зализняк. Коротко об арабском языке) right?",
         "panels": []},
        {"id": "L2", "filt": "b", "title": "item two",
         "question": "second question, no internal id here", "panels": []},
    ]


_GATE_OK = {
    "patterns": [r"acc\d{3}"],
    "labels": {"acc001": "А.А. Зализняк. Коротко об арабском языке"},
}


def test_identity_gate_passes_when_every_match_labeled_and_named():
    out = render_review_sheet(_items_with_ids(), _config(identity_gate=_GATE_OK))
    assert "acc001" in out


def test_identity_gate_raises_on_match_with_no_label():
    gate = {"patterns": [r"acc\d{3}"], "labels": {}}
    with pytest.raises(PreflightError, match="acc001"):
        render_review_sheet(_items_with_ids(), _config(identity_gate=gate))


def test_identity_gate_raises_when_label_not_in_question():
    gate = {"patterns": [r"acc\d{3}"], "labels": {"acc001": "wrong label text"}}
    with pytest.raises(PreflightError, match="does not appear"):
        render_review_sheet(_items_with_ids(), _config(identity_gate=gate))


def test_identity_gate_ignores_ids_inside_tags():
    """A regex match must come from the visible question text, not markup."""
    items = [{"id": "L1", "filt": "a", "title": "t",
              "question": '<span data-ref="acc999">clean question</span>',
              "panels": []}]
    gate = {"patterns": [r"acc\d{3}"], "labels": {}}
    # acc999 only appears inside a stripped attribute, not in the visible text,
    # so no card-visible match — nothing to flag.
    out = render_review_sheet(items, _config(identity_gate=gate))
    assert "clean question" in out


def test_identity_gate_missing_warns_under_extras_true():
    with pytest.warns(PreflightWarning, match="V13"):
        render_review_sheet(_items(), _config())


def test_identity_gate_missing_silent_under_extras_false():
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _render_raw(_items(), _config(), extras=False)


def test_identity_gate_requires_patterns():
    gate = {"patterns": [], "labels": {}}
    with pytest.raises(ValueError, match="patterns"):
        render_review_sheet(_items_with_ids(), _config(identity_gate=gate))


def test_identity_gate_requires_labels_mapping():
    gate = {"patterns": [r"acc\d{3}"], "labels": None}
    with pytest.raises(TypeError, match="labels"):
        render_review_sheet(_items_with_ids(), _config(identity_gate=gate))
