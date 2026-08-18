# -*- coding: utf-8 -*-
"""U7 (H2846) — a typology/classification label rendered on a card must carry
its count on this card and its share of the sheet's population beside it. The
v2 re-glue card asked a reviewer to approve a typology whose distribution
(1,534 restatements / 250 additions / 1 correction) was invisible on the
card; a label with neither count nor share is a build error, not a style
lapse.
"""
import pytest

from csl_pyutil.evidence import PreflightError
from test_review_sheet import _config, _items, render_review_sheet


def _items_with_typology(entry):
    items = _items()
    items[0]["typology"] = [entry]
    return items


def test_typology_chip_renders_label_count_and_share():
    out = render_review_sheet(
        _items_with_typology({"label": "restatement", "n": 1534, "share": 0.86}),
        _config(),
    )
    assert "restatement" in out
    assert "1534" in out
    assert "86%" in out
    assert "badge-typology" in out


def test_typology_share_unknown_renders_explicit_text():
    out = render_review_sheet(
        _items_with_typology({"label": "addition", "n": 250, "share_unknown": True}),
        _config(),
    )
    assert "share unknown" in out


def test_typology_missing_n_raises():
    with pytest.raises(PreflightError, match="missing count"):
        render_review_sheet(
            _items_with_typology({"label": "restatement", "share": 0.86}),
            _config(),
        )


def test_typology_missing_share_raises():
    with pytest.raises(PreflightError, match="missing share"):
        render_review_sheet(
            _items_with_typology({"label": "restatement", "n": 1534}),
            _config(),
        )


def test_typology_missing_label_raises():
    with pytest.raises(PreflightError, match="missing 'label'"):
        render_review_sheet(
            _items_with_typology({"n": 1534, "share": 0.86}),
            _config(),
        )


def test_typology_entry_must_be_a_mapping():
    with pytest.raises(PreflightError, match="must be mappings"):
        render_review_sheet(
            _items_with_typology("restatement"),
            _config(),
        )


def test_items_without_typology_key_are_unaffected():
    out = render_review_sheet(_items(), _config())
    assert '<span class="badge badge-typology"' not in out
