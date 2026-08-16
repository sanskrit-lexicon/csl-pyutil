# -*- coding: utf-8 -*-
"""V14 — export context: decisions payloads carry their provenance.

MG, handing in a partial of the BookIndex crosswalk gate (16-08-2026):
«почему в скачанном .json нет главного, H2707 для опознания к кому он
принадлежит?» These tests pin the contract: config["context"] rides as a
top-level ``context`` field in EVERY export payload (download, autosave,
strict, hand-in), shows in the header beside sheet_id, defaults to
absent, validates its shape, and never touches the donor fixture path.
"""
import json

import pytest

from test_review_sheet import _config, _items, render_review_sheet

CTX = {"handoff": "H2707", "repo": "gasyoun/BookIndex"}


def test_context_var_and_every_payload_site():
    out = render_review_sheet(_items(), _config(context=CTX))
    assert "var CONTEXT = %s;" % json.dumps(CTX, ensure_ascii=False) in out
    assert "sheet_id: SHEET_ID," not in out.replace(
        "sheet_id: SHEET_ID, context: CONTEXT,", "")
    # both the plain download and the V12 hand-in payloads carry it
    assert out.count("sheet_id: SHEET_ID, context: CONTEXT,") >= 2


def test_context_shown_in_header():
    out = render_review_sheet(_items(), _config(context=CTX))
    assert "handoff H2707" in out
    assert "repo gasyoun/BookIndex" in out


def test_context_absent_by_default():
    out = render_review_sheet(_items(), _config())
    assert "var CONTEXT" not in out
    assert "context: CONTEXT" not in out


def test_context_validates_shape():
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(context="H2707"))
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(context={}))
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(context={"handoff": ["H2707"]}))


def test_context_covers_strict_payload():
    cfg = _config(context=CTX, strict_review={"reviewer": "MG"})
    out = render_review_sheet(_items(), cfg)
    # strictPayload's literal was rewritten too
    assert "sheet_id: SHEET_ID," not in out.replace(
        "sheet_id: SHEET_ID, context: CONTEXT,", "")


def test_context_absent_from_donor_path():
    out = render_review_sheet(_items(), _config(), extras=False)
    assert "CONTEXT" not in out
