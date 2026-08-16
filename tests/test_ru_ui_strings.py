# -*- coding: utf-8 -*-
"""RU_UI_STRINGS (H2854 step 2, decision 8) — a ready-made preset so a sheet's
chrome goes Russian with one config line, no per-string bookkeeping in the
generator."""
from csl_pyutil import RU_UI_STRINGS
from csl_pyutil.review_sheet import UI_STRINGS

from test_review_sheet import _config, _items, render_review_sheet

# Chrome text a fully English-default render would contain; RU_UI_STRINGS must
# scrub every one of them (save_banner is deliberately out of scope — see the
# constant's docstring — and this test never passes save_as, so it never
# appears in the first place).
_ENGLISH_CHROME = [
    "Download decisions.json", "Save to folder", "Keyboard:", "&#9208; Defer<",
    "next/prev", "Approve</b> = accept", "Reject</b> = keep",
    "Defer</b> = not sure", "Reason</span>",
    "active time on this sheet", "Hand in what I got",
    "stop the clock and export the votes made so far",
    "pause the clock", "handed in {n} of {total}",
]


def test_ru_preset_covers_every_known_ui_strings_key_except_save_banner():
    assert set(UI_STRINGS) - set(RU_UI_STRINGS) == {"save_banner"}


def test_ru_preset_scrubs_all_english_chrome():
    out = render_review_sheet(
        _items(), _config(ui_strings=RU_UI_STRINGS,
                          rating={"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4},
                          reject_labels=[("acc", "Accuracy")]),
    )
    for phrase in _ENGLISH_CHROME:
        assert phrase not in out, "leftover English chrome: %r" % phrase
    assert "Скачать decisions.json" in out
    assert "Сдать что успел" in out


def test_ru_preset_values_are_known_keys():
    unknown = set(RU_UI_STRINGS) - set(UI_STRINGS)
    assert not unknown, "RU_UI_STRINGS has key(s) UI_STRINGS does not know: %s" % unknown
