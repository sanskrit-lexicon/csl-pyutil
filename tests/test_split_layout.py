# -*- coding: utf-8 -*-
"""0.22.0 split_layout — two-column DE|RU chrome, store in details, voteBar mirror."""
import json
import re

import pytest

from csl_pyutil import render_review_sheet as _render_raw

from test_fixture_byte_identical import FIXTURES
from test_review_sheet import _config, _items, render_review_sheet


def _split_items():
    return [
        {
            "id": "L1", "filt": "a", "title": "ga", "question": "ok?",
            "panels": [],
            "left": '<div class="sense" data-pair="h0:1">gehen <span class="ins-chip chip" data-pair="h0:1">NWS<span class="chip-tip">wandern</span></span></div>',
            "right": '<div class="render-expanded" data-pair="h0:1">идти</div>',
            "store_markup": '<div class="anatomy">RAWSTORE</div>',
        },
        {
            "id": "L2", "filt": "b", "title": "two", "question": "second?",
            "panels": [],
            "left": '<div class="col-de-inner">DE2</div>',
            "right": '<div class="col-ru-inner">RU2</div>',
            "store_markup": '<div class="anatomy">RAW2</div>',
        },
    ]


def test_flag_off_keeps_980_and_has_no_card_split():
    out = render_review_sheet(_items(), _config())
    assert "card-split" not in out
    assert "main { max-width:980px" in out
    assert "body.split-layout" not in out


def test_extras_false_ignores_split_layout_flag():
    """Donor path must not see the flag — fixture stays byte-identical."""
    golden = (FIXTURES / "h180_typology_golden.html").read_text(encoding="utf-8")
    payload = json.loads((FIXTURES / "h180_typology_items.json").read_text(encoding="utf-8"))
    items = payload["items"]
    config = payload["config"]
    for it in items:
        it["panels"] = [tuple(p) for p in it["panels"]]
    config["filters"] = [tuple(f) for f in config["filters"]]
    config["split_layout"] = True
    out = _render_raw(items, config, extras=False)
    assert out == golden


def test_split_on_two_columns_no_980_on_main():
    out = render_review_sheet(_split_items(), _config(split_layout=True))
    assert 'class="card-split"' in out
    assert 'class="col-de"' in out
    assert 'class="col-ru"' in out
    assert "body.split-layout" in out
    assert "main { max-width:none" in out
    assert "main { max-width:980px" not in out
    assert "max-width: 900px" in out


def test_store_anatomy_only_inside_closed_details():
    out = render_review_sheet(_split_items(), _config(split_layout=True))
    # every anatomy occurrence sits inside a details element that is not open
    for m in re.finditer(r'<details class="store-details"[^>]*>.*?</details>', out, re.S):
        block = m.group(0)
        assert 'class="anatomy"' in block
        assert " open" not in block.split(">", 1)[0]
    outside = re.sub(r'<details class="store-details"[^>]*>.*?</details>', "", out, flags=re.S)
    assert 'class="anatomy"' not in outside
    assert "<details" in out


def test_missing_left_raises():
    items = _split_items()
    del items[0]["left"]
    with pytest.raises(ValueError, match="left"):
        render_review_sheet(items, _config(split_layout=True))


def test_vote_bar_mirror_js_keeps_hidden_controls():
    out = render_review_sheet(_split_items(), _config(split_layout=True))
    assert 'id="voteBar"' in out
    assert "function mirrorCard" in out
    assert "src.click()" in out
    assert "body.split-layout .card > .controls" in out
    assert 'class="controls"' in out  # still in the card DOM, just hidden


def test_chip_tooltip_not_title_attr():
    out = render_review_sheet(_split_items(), _config(split_layout=True))
    assert 'class="chip-tip"' in out
    assert "ins-chip" in out
    card = out.split("<main")[1].split("</main>")[0]
    assert 'title="wandern"' not in card
