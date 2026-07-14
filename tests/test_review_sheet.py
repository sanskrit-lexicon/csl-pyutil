# -*- coding: utf-8 -*-
import json
import re

import pytest

from csl_pyutil import render_review_sheet


def _config(**overrides):
    cfg = {
        "sheet_id": "test-sheet_scope", "title": "Test Sheet",
        "subtitle": "a test sheet", "footer": "Approve/Reject/Defer per item.",
        "approve_label": "Approve", "reject_label": "Reject",
        "filters": [("a", "A"), ("b", "B")], "generated": "2026-07-14",
    }
    cfg.update(overrides)
    return cfg


def _items():
    return [
        {"id": "L1", "filt": "a", "title": "item one", "badges": ["x"],
         "question": "Is this right?", "panels": [("context", "<pre>old vs new</pre>")]},
        {"id": "L2", "filt": "b", "title": "item two", "question": "second question",
         "panels": []},
    ]


def test_basic_shape():
    out = render_review_sheet(_items(), _config())
    assert out.startswith("<!DOCTYPE html>")
    assert "Test Sheet" in out
    assert "a test sheet" in out
    assert out.count("<script>") == out.count("</script>")


def test_extras_adds_save_button_and_legend():
    out = render_review_sheet(_items(), _config(), extras=True)
    assert 'id="saveBtn"' in out
    assert "showSaveFilePicker" in out
    assert "class=\"legend\"" in out


def test_extras_false_matches_donor_core_shape():
    out = render_review_sheet(_items(), _config(), extras=False)
    assert 'id="saveBtn"' not in out
    assert "showSaveFilePicker" not in out
    assert "class=\"legend\"" not in out


def test_items_and_filters_embedded_correctly():
    out = render_review_sheet(_items(), _config())
    m = re.search(r"var ids = (\[.*?\]);", out)
    assert m
    ids = json.loads(m.group(1))
    assert ids == ["L1", "L2"]
    assert 'data-filter="a">A' in out
    assert 'data-filter="b">B' in out
    assert 'data-filter="unvoted">unvoted only' in out


def test_custom_approve_reject_labels_appear():
    out = render_review_sheet(_items(), _config(approve_label="Correct", reject_label="Wrong"))
    assert "&#9989; Correct" in out
    assert "&#10060; Wrong" in out


def test_decisions_json_contract_fields_present():
    out = render_review_sheet(_items(), _config())
    assert "sheet_id: SHEET_ID" in out
    assert "decided: decided" in out
    assert "note: rec.note" in out


def test_panels_and_badges_rendered():
    out = render_review_sheet(_items(), _config())
    assert "<h4>context</h4>" in out
    assert "old vs new" in out
    assert '<span class="badge">x</span>' in out


def test_item_with_no_panels_renders_empty_but_valid():
    out = render_review_sheet(_items(), _config())
    assert "second question" in out


def test_html_escaping_in_title_and_badges():
    items = [{"id": "L1", "filt": "a", "title": "<script>alert(1)</script>",
              "badges": ["<img onerror=alert(1)>"], "question": "q", "panels": []}]
    out = render_review_sheet(items, _config())
    assert "<script>alert(1)</script>" not in out.split("<main")[1].split("</main>")[0]
    assert "&lt;script&gt;" in out
    assert "&lt;img onerror=alert(1)&gt;" in out


def test_generated_is_caller_supplied_not_computed():
    out1 = render_review_sheet(_items(), _config(generated="2020-01-01"))
    out2 = render_review_sheet(_items(), _config(generated="2020-01-01"))
    assert out1 == out2  # fully deterministic given the same explicit "generated"
    assert "2020-01-01" in out1
