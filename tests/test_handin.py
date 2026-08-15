# -*- coding: utf-8 -*-
"""V12 (H2858) — the partial hand-in button and the clock pause.

MG, after one sitting on the BookIndex crosswalk gate (15-08-2026, 30 approve /
14 reject of 255 cards in 14 minutes): «Хочу поставить на паузу, остановить
таймер и остановить работу, сдать то что было. Но такой функции как сдать
сколько успел нет — а она нужна.» These tests pin the contract: default ON for
extras=True, absent from the donor fixture path, opt-out via
config["hand_in"]=False, the export marked partial, the strict all-votes gate
bypassed, and the pause control present only when there is a clock to pause.
"""
import json

import pytest

from test_review_sheet import _config, _items, render_review_sheet


def test_handin_on_by_default_with_extras():
    out = render_review_sheet(_items(), _config())
    assert 'id="handinBtn"' in out
    assert 'id="pauseBtn"' in out
    assert "_decisions_partial.json" in out
    assert "partial: true, complete: false" in out
    assert "undecided: items.length - decided" in out


def test_handin_opt_out():
    out = render_review_sheet(_items(), _config(hand_in=False))
    assert 'id="handinBtn"' not in out
    assert 'id="pauseBtn"' not in out
    assert "_decisions_partial.json" not in out


def test_handin_rejects_non_bool():
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(hand_in="yes"))


def test_handin_absent_from_donor_path():
    out = render_review_sheet(_items(), _config(), extras=False)
    assert "handinBtn" not in out
    assert "pauseBtn" not in out


def test_handin_binds_generated_once():
    """The core download handler builds its payload from a literal `generated`;
    the hand-in handler reads the same value through GENERATED."""
    cfg = _config()
    out = render_review_sheet(_items(), cfg)
    assert "var GENERATED = " + json.dumps(cfg["generated"]) + ";" in out
    assert "generated: GENERATED" in out


def test_handin_pause_freezes_the_v11_clock():
    out = render_review_sheet(_items(), _config())
    assert "var __timePaused = !!__timing.paused;" in out
    assert "if (document.hidden || __timePaused || dt <= 0 || dt > 4) return;" in out
    assert "__timePauseSet(!__timePaused)" in out


def test_handin_survives_timing_off():
    """No clock to pause — the button still exports, and neither the pause
    control nor any timing identifier is emitted (that absence is
    test_timing_opt_out's contract, which V12 must not break)."""
    out = render_review_sheet(_items(), _config(timing=False))
    assert 'id="handinBtn"' in out
    assert "_decisions_partial.json" in out
    assert 'id="pauseBtn"' not in out
    assert "__timeFor" not in out
    assert "time_total_seconds" not in out


def test_handin_bypasses_the_strict_all_votes_gate():
    """Strict blocks the FINAL download until every card is voted; the hand-in
    button is the sanctioned way out of a half-finished sitting, so it must not
    be routed through strictValidation()."""
    out = render_review_sheet(_items(), _config(strict_review={"reviewer": "MG"}))
    handin = out.split("var HANDIN_SAID")[1]
    assert "strictValidation()" not in handin
    assert "payload.reviewer = strictReviewer.value.trim();" in handin


def test_handin_carries_rating_and_reject_label_when_configured():
    out = render_review_sheet(
        _items(),
        _config(rating={"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4},
                reject_labels=[("acc", "Accuracy"), ("style", "Style")]),
    )
    handin = out.split("var HANDIN_SAID")[1]
    assert "item.rating = (rec.rating == null ? null : rec.rating);" in handin
    assert "item.reject_label = rec.reject_label || null;" in handin


def test_handin_omits_fields_the_sheet_has_no_layer_for():
    """The plain sheet has no rating and no reject-label picker, so the hand-in
    payload must not invent those fields."""
    handin = render_review_sheet(_items(), _config()).split("var HANDIN_SAID")[1]
    assert "item.rating" not in handin
    assert "item.reject_label" not in handin


def test_handin_item_not_caught_by_the_v11_item_surgery():
    """V11 rewrites the shared ``note: rec.note || ''`` literal everywhere it
    occurs. V12 assembles its item by assignment and instruments its own
    time_seconds, so the hand-in payload carries exactly one."""
    out = render_review_sheet(_items(), _config())
    handin = out.split("var HANDIN_SAID")[1]
    assert "note: rec.note" not in handin
    assert handin.count("time_seconds") == 1


def test_handin_strings_are_localizable():
    out = render_review_sheet(
        _items(),
        _config(ui_strings={
            "handin_button": "Сдать сколько успел",
            "handin_title": "остановить таймер и выгрузить уже проголосованное",
            "pause_title": "пауза — перерыв не считается работой",
            "handin_said": "сдано {n} из {total} — таймер остановлен",
        }),
    )
    assert "Сдать сколько успел" in out
    assert "Hand in what I got" not in out
    assert "остановить таймер и выгрузить уже проголосованное" in out
    assert "пауза — перерыв не считается работой" in out
    assert "var HANDIN_SAID = 'сдано {n} из {total} — таймер остановлен';" in out
