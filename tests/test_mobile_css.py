# -*- coding: utf-8 -*-
"""Mobile layer (H2854 step 2, decision 12) — one @media block, always-emitted
for every extras=True sheet, no config flag, no JS."""
from test_review_sheet import _config, _items, render_review_sheet
from csl_pyutil import render_review_sheet as _render_raw


def test_mobile_media_query_present_with_extras():
    out = render_review_sheet(_items(), _config())
    assert "@media (max-width: 640px)" in out
    assert "min-height: 44px" in out


def test_mobile_layer_absent_from_donor_fixture_path():
    out = _render_raw(_items(), _config(), extras=False)
    assert "@media (max-width: 640px)" not in out
