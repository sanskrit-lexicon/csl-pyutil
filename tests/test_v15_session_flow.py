# -*- coding: utf-8 -*-
"""V15 (H2887) — the voting-session layer: the clock stops on export, and
`a`/`r`/`d` can no longer land on a card the reviewer is not looking at.

MG on the private sheet 16-08-2026: «Когда я сохраняю решения, таймер должен
останавливаться. Сейчас этого не происходит. Как ещё оптимизировать опыт
голосования?» Reading the code found two defects, the second unreported and
heavier: V12 stopped the clock in `handinBtn` only (so the PARTIAL exit stopped
it and the FULL one did not), and `activeIdx` — the target of the vote keys —
moved on arrow keys alone, with no scroll handler and no focus ring, while the
clock billed time to the card at the viewport centre.

These tests pin the contract: default ON for extras=True, absent from the donor
path, opt-out via config["session_flow"]=False leaving NO new identifier, the
pause carries a reason, a legacy record without one reads as manual, auto-rearm
never lifts a manual pause, one current card shared by clock and keys, and the
emitted script parses in six layer combinations.

Named V15, not the plan's V14: the export-context layer shipped as V14 the same
day, so this build takes the next free slot per the plan's ambiguity contract —
the same move H2854 made when H2858 had already taken V12.
"""
import re
import shutil
import subprocess

import pytest

from csl_pyutil import RU_UI_STRINGS
from csl_pyutil import render_review_sheet as _render_raw
from csl_pyutil.review_sheet import UI_STRINGS

from test_review_sheet import _config, _items, render_review_sheet

# Every identifier V15 introduces. `session_flow=False` must leave the document
# without a single one of them — the same absence contract test_timing_opt_out
# and test_facets_absent_leaves_document_untouched already rely on.
_FLOW_IDENTIFIERS = [
    "kbd-active", "flowUndoBtn", "flowToast", "flowProg", "flowBar", "flowEta",
    "__flowSync", "__flowPaint", "__flowAdvance", "__flowRearm", "__flowUndo",
    "FLOW_IDLE_SECONDS", "FLOW_PROGRESS", "FLOW_RESUMED", "pause_reason",
    "t-state",
]


def _script(doc):
    """The sheet's one inline script, without its tags."""
    body = doc.split("<script>", 1)[1].split("</script>", 1)[0]
    assert body.strip(), "empty script"
    return body


# --------------------------------------------------------------------- presence


def test_session_flow_on_by_default_with_extras():
    out = render_review_sheet(_items(), _config())
    assert 'id="flowUndoBtn"' in out
    assert 'id="flowToast"' in out
    assert ".card.kbd-active" in out
    assert "var FLOW_IDLE_SECONDS = 90;" in out


def test_session_flow_opt_out_leaves_no_identifier():
    out = render_review_sheet(_items(), _config(session_flow=False))
    for ident in _FLOW_IDENTIFIERS:
        assert ident not in out, "leftover V15 identifier: %r" % ident


def test_session_flow_absent_from_donor_path():
    out = _render_raw(_items(), _config(), extras=False)
    for ident in _FLOW_IDENTIFIERS:
        assert ident not in out, "V15 reached the donor fixture path: %r" % ident


def test_session_flow_rejects_non_bool():
    with pytest.raises(TypeError, match="session_flow"):
        render_review_sheet(_items(), _config(session_flow="yes"))


# ------------------------------------------------------- defect 1: clock stops


def test_download_and_save_stop_the_clock():
    """The reported defect. One capture-phase listener on `document` covers the
    plain download, the strict variant (which stopImmediatePropagation()s on its
    own element, so a listener bound to the BUTTON would never run) and the
    file-picker."""
    out = render_review_sheet(_items(), _config())
    assert "'#downloadBtn, #saveBtn, #handinBtn'" in out
    assert "__timePauseSet(true, 'export');" in out
    assert "}, true);" in out


def test_download_stops_the_clock_under_strict_review():
    out = render_review_sheet(_items(), _config(strict_review={"reviewer": "MG"}))
    assert "'#downloadBtn, #saveBtn, #handinBtn'" in out
    assert "__timePauseSet(true, 'export');" in out


def test_handin_now_names_its_pause_reason():
    """V12 stopped the clock with a bare `__timePauseSet(true)`. Under V15 an
    unnamed stop means `manual`, which auto-rearm must never lift — so the
    hand-in stop is renamed to `export` rather than left to default."""
    out = render_review_sheet(_items(), _config())
    assert "__timePauseSet(true); __pauseShow();" not in out
    assert "__timePauseSet(true, 'export'); __pauseShow();" in out


def test_manual_pause_button_still_reads_as_manual():
    """The ⏸ button keeps V12's single-argument call, and the reason defaults to
    `manual` — the argument the auto-rearm refuses to override."""
    out = render_review_sheet(_items(), _config())
    assert "__timePauseSet(!__timePaused)" in out
    assert "__timePauseReason = __timePaused ? (reason || 'manual') : null;" in out


def test_autorearm_never_lifts_a_manual_pause():
    out = render_review_sheet(_items(), _config())
    assert "if (__timePaused && __timePauseReason !== 'manual') {" in out


def test_legacy_timing_record_without_a_reason_reads_as_manual():
    """A record written before this layer has `paused` and no reason. A curator
    who paused yesterday must not come back to a clock that restarted itself."""
    out = render_review_sheet(_items(), _config())
    assert ("var __timePauseReason = __timePaused ? (__timing.pause_reason || 'manual') : null;"
            in out)


def test_idle_autopause_is_a_named_constant():
    out = render_review_sheet(_items(), _config())
    assert "var FLOW_IDLE_SECONDS = 90;" in out
    assert "__timePauseSet(true, 'idle');" in out
    assert "FLOW_IDLE_SECONDS * 1000" in out


def test_pause_reason_persists_in_the_same_timing_record():
    out = render_review_sheet(_items(), _config())
    assert "__timing.pause_reason = __timePauseReason;" in out
    assert "var TIME_KEY = STORE_KEY + ':timing';" in out


def test_clock_state_is_visible_in_the_chip():
    out = render_review_sheet(_items(), _config())
    assert '<span class="tstate" id="t-state"></span>' in out
    # the manual ⏸ button repaints through V12's own __pauseShow, so the label
    # must ride along with it or it goes stale exactly when it matters
    assert "__pauseShow = function () { __flowOrigPauseShow(); __flowClockShow(); };" in out
    assert "var FLOW_CLOCK_RUNNING = 'running';" in out
    assert "var FLOW_CLOCK_PAUSED = 'paused';" in out
    assert "var FLOW_CLOCK_IDLE = 'idle';" in out


def test_clock_machinery_absent_when_timing_is_off():
    """No clock to stop. `test_timing_opt_out` and `test_handin_survives_timing_off`
    assert the ABSENCE of the timing identifiers; V15 must not smuggle them back
    in through a runtime probe."""
    out = render_review_sheet(_items(), _config(timing=False))
    assert 'id="flowUndoBtn"' in out
    for ident in ("__timePauseSet", "__timeActiveId", "pause_reason", "t-state",
                  "FLOW_CLOCK_RUNNING", "time_total_seconds", "__timeFor"):
        assert ident not in out, "timing identifier leaked with timing=False: %r" % ident


def test_pause_show_only_called_when_the_handin_layer_defines_it():
    """`__pauseShow` lives in the V12 hand-in layer. With hand_in=False there is
    no such function, so V15 must not call it."""
    out = render_review_sheet(_items(), _config(hand_in=False))
    assert "__pauseShow" not in out
    assert "__timePauseSet(true, 'export');" in out


# ----------------------------------------------- defect 2: one "current card"


def test_one_current_card_shared_by_clock_and_keys():
    """With the clock on, the ring and the vote keys read V11's own
    `__timeActiveId()` — the two layers can no longer disagree."""
    out = render_review_sheet(_items(), _config())
    assert "var __flowCenterId = __timeActiveId;" in out


def test_current_card_defined_without_a_clock_too():
    out = render_review_sheet(_items(), _config(timing=False))
    assert "function __flowCenterId() {" in out
    assert "window.innerHeight / 2" in out


def test_scroll_moves_the_key_target():
    out = render_review_sheet(_items(), _config())
    assert "window.addEventListener('scroll', function () {" in out
    assert "__flowScrollTimer = setTimeout(function () { __flowScrollTimer = null; __flowSync(); }, 120);" in out
    assert "if (id) { var at = __flowIdxOf(id); if (at !== -1) activeIdx = at; }" in out


def test_focus_ring_marks_the_key_target():
    out = render_review_sheet(_items(), _config())
    assert ".card.kbd-active { outline:2px solid var(--accent);" in out
    assert "vis[activeIdx].classList.add('kbd-active');" in out


def test_ring_is_re_derived_after_a_filter_click():
    """Both bars reset `activeIdx` to 0 as they re-filter — without this the
    defect returns wearing a filter."""
    out = render_review_sheet(_items(), _config())
    assert "['filterbar'].forEach(function (barId) {" in out
    assert "setTimeout(__flowSync, 0)" in out


def test_facetbar_named_only_when_that_layer_is_on():
    out = render_review_sheet(
        _items(),
        _config(facets=[{"key": "k", "label": "K", "values": [("v", "V")]}]),
    )
    assert "['filterbar', 'facetbar'].forEach(function (barId) {" in out


# ------------------------------------------------------------------- rhythm


def test_vote_advances_to_the_next_undecided_card():
    out = render_review_sheet(_items(), _config())
    assert "function __flowFirstUndecided() {" in out
    assert "if (!(state[id] && state[id].decision)) return i;" in out
    assert "__flowAdvance();" in out


def test_undo_restores_the_previous_decision_including_none():
    out = render_review_sheet(_items(), _config())
    assert "__flowUndoStack.push({ id: id, prev: rec.decision || null });" in out
    assert "if (last.prev) state[last.id].decision = last.prev;" in out
    assert "else delete state[last.id].decision;" in out
    assert "if (e.key === 'z' || e.key === 'Z') { __flowUndo(); e.preventDefault(); return; }" in out


def test_undo_does_not_touch_the_clock():
    out = render_review_sheet(_items(), _config())
    undo = out.split("function __flowUndo() {", 1)[1].split("\n  var __flowUndoBtn", 1)[0]
    assert "__timePauseSet" not in undo
    assert "__flowRearm" not in undo


def test_progress_and_eta_are_wired_to_the_tally():
    out = render_review_sheet(_items(), _config())
    assert "var __flowOrigTally = tally;" in out
    assert "tally = function () { __flowOrigTally(); __flowProgress(); };" in out
    assert "return (secs.length >= 5 ? FLOW_ETA : FLOW_ETA_ROUGH).replace('{minutes}', minutes);" in out


def test_eta_absent_without_a_clock():
    out = render_review_sheet(_items(), _config(timing=False))
    assert "FLOW_ETA" not in out
    assert 'id="flowProgText"' in out


def test_resume_at_the_first_undecided_card():
    out = render_review_sheet(_items(), _config())
    assert "var FLOW_RESUMED = 'resumed at card {n} of {total}';" in out
    assert "__flowSay(FLOW_RESUMED.replace('{n}', at + 1).replace('{total}', vis.length));" in out


def test_note_edit_rearms_the_clock():
    out = render_review_sheet(_items(), _config())
    assert "noteChange = function (id, t) { __flowOrigNote(id, t); __flowRearm(); };" in out


# --------------------------------------------------------- neighbouring layers


def test_v15_carries_no_export_payload_literal():
    """`_add_timing` replace-alls `note: rec.note || ''` and `_add_export_context`
    replace-alls `sheet_id: SHEET_ID,`. V15 produces no payload, so it must carry
    neither — otherwise it gets instrumented a second time."""
    out = render_review_sheet(_items(), _config())
    flow = out.split("// --- V15 session flow (H2887)", 1)[1]
    assert "note: rec.note" not in flow
    assert "sheet_id: SHEET_ID," not in flow
    assert "time_seconds" not in flow


def test_v15_leaves_the_export_context_replace_all_intact():
    out = render_review_sheet(_items(), _config(context={"handoff": "H2887"}))
    assert "sheet_id: SHEET_ID," not in out.replace(
        "sheet_id: SHEET_ID, context: CONTEXT,", "")


def test_v15_survives_every_neighbouring_layer_at_once():
    out = render_review_sheet(
        _items(),
        _config(rating={"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4},
                reject_labels=[("acc", "Accuracy"), ("style", "Style")],
                strict_review={"reviewer": "MG"},
                context={"handoff": "H2887", "repo": "sanskrit-lexicon/csl-pyutil"},
                facets=[{"key": "k", "label": "K", "values": [("v", "V")]}],
                show_ids=True, save_as="C:/tmp/decisions.json"),
    )
    assert "var __flowOrigVote = vote;" in out
    assert "__timePauseSet(true, 'export');" in out
    assert out.count("<script>") == out.count("</script>")


# ------------------------------------------------------------------- strings


def test_every_new_string_is_a_ui_strings_key():
    out = render_review_sheet(_items(), _config())
    flow_keys = sorted(k for k in UI_STRINGS if k.startswith("flow_"))
    assert len(flow_keys) == 12
    for key in flow_keys:
        assert key in RU_UI_STRINGS, "no Russian for %r" % key
    assert "Undo</button>" in out


def test_new_strings_are_localizable_one_by_one():
    out = render_review_sheet(
        _items(),
        _config(ui_strings={
            "flow_undo_button": "Отменить",
            "flow_undo_title": "отменить последнее решение",
            "flow_progress": "решено {n} из {total}",
            "flow_resumed": "продолжили с карточки {n} из {total}",
            "flow_clock_idle": "простой",
        }),
    )
    assert "Отменить</button>" in out
    assert 'title="отменить последнее решение"' in out
    assert "var FLOW_PROGRESS = 'решено {n} из {total}';" in out
    assert "var FLOW_RESUMED = 'продолжили с карточки {n} из {total}';" in out
    assert "var FLOW_CLOCK_IDLE = 'простой';" in out
    assert "decided {n} of {total}" not in out


def test_ru_preset_scrubs_the_new_english_chrome():
    out = render_review_sheet(_items(), _config(ui_strings=RU_UI_STRINGS))
    for phrase in ("decided {n} of {total}", "about {minutes} min left",
                   "nothing to undo", "no decision", "resumed at card",
                   "undo the last decision", "&#8630; Undo<",
                   "var FLOW_CLOCK_RUNNING = 'running';",
                   "var FLOW_CLOCK_PAUSED = 'paused';",
                   "var FLOW_CLOCK_IDLE = 'idle';"):
        assert phrase not in out, "leftover English V15 chrome: %r" % phrase
    assert "решено {n} из {total}" in out
    assert "продолжили с карточки {n} из {total}" in out
    assert "var FLOW_CLOCK_IDLE = 'простой';" in out
    # The pause REASONS are internal state tokens, not chrome — they must
    # survive translation, or the state machine stops recognising itself.
    assert "__timePauseSet(true, 'idle');" in out
    assert "__timePauseSet(true, 'export');" in out


def test_placeholders_survive_the_russian_preset():
    for key, holders in (("flow_progress", ("{n}", "{total}")),
                         ("flow_eta", ("{minutes}",)),
                         ("flow_eta_rough", ("{minutes}",)),
                         ("flow_undo_said", ("{id}", "{decision}")),
                         ("flow_resumed", ("{n}", "{total}"))):
        for holder in holders:
            assert holder in RU_UI_STRINGS[key], "%s lost %s" % (key, holder)


def test_russian_strings_carry_no_apostrophe():
    """They land inside single-quoted JS literals."""
    for key, value in RU_UI_STRINGS.items():
        if key.startswith("flow_"):
            assert "'" not in value, "%s would break its JS literal" % key


# ------------------------------------------------------------------ JS parses

_NODE = shutil.which("node")

_LAYER_COMBOS = {
    "plain": {},
    "timing_off": {"timing": False},
    "strict": {"strict_review": {"reviewer": "MG"}},
    "rating_labels": {"rating": {"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4},
                      "reject_labels": [("acc", "Accuracy")]},
    "everything": {"rating": {"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4},
                   "reject_labels": [("acc", "Accuracy")],
                   "strict_review": {"reviewer": "MG"},
                   "context": {"handoff": "H2887"},
                   "facets": [{"key": "k", "label": "K", "values": [("v", "V")]}],
                   "show_ids": True, "save_as": "C:/tmp/d.json",
                   "ui_strings": RU_UI_STRINGS},
    "session_flow_off": {"session_flow": False},
}


@pytest.mark.skipif(_NODE is None, reason="node is not installed")
@pytest.mark.parametrize("combo", sorted(_LAYER_COMBOS))
def test_emitted_script_parses(combo, tmp_path):
    out = render_review_sheet(_items(), _config(**_LAYER_COMBOS[combo]))
    js = tmp_path / ("sheet_%s.js" % combo)
    js.write_text(_script(out), encoding="utf-8")
    proc = subprocess.run([_NODE, "--check", str(js)],
                          capture_output=True, text=True, encoding="utf-8")
    assert proc.returncode == 0, "%s: %s" % (combo, proc.stderr)


def test_script_has_no_unbalanced_tags_in_any_combo():
    for combo, overrides in _LAYER_COMBOS.items():
        out = render_review_sheet(_items(), _config(**overrides))
        assert out.count("<script>") == out.count("</script>") == 1, combo
        assert re.search(r"</body>\s*</html>", out), combo
