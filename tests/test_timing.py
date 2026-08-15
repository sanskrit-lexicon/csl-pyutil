# -*- coding: utf-8 -*-
"""V11 (H2840) — the active-time metering layer.

MG, voting the BookIndex crosswalk gate 15-08-2026: the sheet itself must
measure how long the reviewer spends on the page and on each card, here and in
every other vote. These tests pin the contract: default ON for extras=True,
absent from the donor fixture path, opt-out via config["timing"]=False, and the
export carries time_total_seconds + per-item time_seconds.
"""
import pytest

from test_review_sheet import _config, _items, render_review_sheet
from csl_pyutil import render_review_sheet as _render_raw


def test_timing_on_by_default_with_extras():
    out = render_review_sheet(_items(), _config())
    assert 'id="t-total"' in out
    assert "TIME_KEY" in out
    assert "time_total_seconds: __timeTotal()" in out
    assert "time_seconds: __timeFor(id)" in out


def test_timing_reaches_every_item_literal_variant():
    """The item surgery must catch the plain, autosave, strict, rating and
    reject-label constructors — none may export an item without time_seconds."""
    out = render_review_sheet(
        _items(),
        _config(rating={"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4},
                reject_labels=[("acc", "Accuracy"), ("style", "Style")],
                strict_review={"reviewer": "MG"}),
    )
    assert "note: rec.note || ''," in out
    # strict mode replaces the autosave payload with strictPayload(), so the
    # two surviving constructors are the core download and strictItems()
    assert out.count("time_seconds: __timeFor(id)") >= 2
    # no un-instrumented literal left behind
    assert "note: rec.note || '' }" not in out


def test_timing_opt_out():
    out = render_review_sheet(_items(), _config(timing=False))
    assert 'id="t-total"' not in out
    assert "time_total_seconds" not in out


def test_timing_absent_from_donor_fixture_path():
    out = _render_raw(_items(), _config(), extras=False)
    assert 'id="t-total"' not in out
    assert "time_total_seconds" not in out


def test_timing_type_checked():
    with pytest.raises(TypeError, match="timing"):
        render_review_sheet(_items(), _config(timing="yes"))


def test_timing_tooltip_localizable():
    out = render_review_sheet(
        _items(),
        _config(ui_strings={"timing_title": "активное время на листе"}),
    )
    assert "активное время на листе" in out
    assert "active time on this sheet" not in out
