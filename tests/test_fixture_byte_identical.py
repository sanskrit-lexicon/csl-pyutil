# -*- coding: utf-8 -*-
"""Proves the port is faithful: render_review_sheet(..., extras=False) must
reproduce, byte-for-byte, the donor's (build_h180_review_sheets.py) literal
output for a fixed synthetic input. The fixture data (tests/fixtures/) is
100% synthetic placeholder content, generated ONLY through the donor's own
render_card()/TEMPLATE with fake panel bodies — never real translation
content, which is gitignored/unpublished in its source repo and must never
land in this public repo.
"""
import json
from pathlib import Path

from csl_pyutil import render_review_sheet

FIXTURES = Path(__file__).parent / "fixtures"


def test_typology_style_sheet_byte_identical_to_donor():
    golden = (FIXTURES / "h180_typology_golden.html").read_text(encoding="utf-8")
    payload = json.loads((FIXTURES / "h180_typology_items.json").read_text(encoding="utf-8"))
    items = payload["items"]
    config = payload["config"]

    # convert panels back from JSON's list-of-lists to the tuple pairs render_card expects
    for it in items:
        it["panels"] = [tuple(p) for p in it["panels"]]
    config["filters"] = [tuple(f) for f in config["filters"]]

    out = render_review_sheet(items, config, extras=False)
    assert out == golden
