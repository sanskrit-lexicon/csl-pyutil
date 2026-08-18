# -*- coding: utf-8 -*-
"""V17 — voting ergonomics, reported by MG after a real sitting (18-08-2026).

Voting pack 1 of the 320-card gold set surfaced four things, every one about
where the reviewer's eye already is:

  1. the submit controls sat in the HEADER, above the work, while the reviewer
     finishes at the BOTTOM;
  2. there was no real progress bar at the top — V15's was a 120px chip in that
     same toolbar;
  3. the ETA covered the current PAGE, but on a 32-pack sheet the question is
     how long the WHOLE instrument takes at the pace you are going;
  4. auto-advance scrolled the next card to the viewport CENTRE, so the card
     under judgement began half off the top of the screen.

The riskiest part is (1): relocation must not name a layer that is switched off,
or it breaks the absence contracts V12/V15/V16 each rely on. Hence build-time
`data-submit` tagging of the controls that are actually present, asserted below
in both directions.
"""
import re

import pytest

from csl_pyutil import RU_UI_STRINGS
from csl_pyutil.review_sheet import UI_STRINGS

from test_review_sheet import _config, _items, render_review_sheet


def _r(**cfg):
    return render_review_sheet(_items(), _config(**cfg))


# ------------------------------------------------------------------ progress bar

def test_progress_bar_rides_inside_the_sticky_header():
    """Injected before the toolbar it sat ~180px down at rest, below the header
    and the screening banner; and once scrolled, two sticky top:0 elements cover
    each other. Inside the header it is genuinely at the top, always."""
    out = _r()
    assert '<div class="voteprog" id="voteProg">' in out
    assert out.index('id="voteProg"') < out.index('</header>')


def test_progress_bar_spans_the_header_width():
    assert ".voteprog { flex:1 0 100%;" in _r()


def test_progress_counts_this_sheet_when_no_packset_total():
    out = _r()
    assert "var VOTE_TOTAL = 0;" in out


def test_progress_counts_the_whole_packset_when_told():
    out = _r(packset_total=320)
    assert "var VOTE_TOTAL = 320;" in out
    # counting the whole instrument means reading the SHARED record, not `ids`
    assert "function __voteDecidedAll()" in out


def test_packset_total_must_not_be_smaller_than_the_page():
    with pytest.raises(ValueError, match="packset_total"):
        _r(packset_total=1)


def test_packset_total_must_be_an_int():
    with pytest.raises(TypeError, match="packset_total"):
        _r(packset_total="320")


# ------------------------------------------------------------------ whole-set ETA

def test_eta_is_for_the_whole_set_and_says_so():
    out = _r(packset_total=320)
    assert "var VOTE_ETA = 'about {minutes} min left for all {total}';" in out
    assert "{total}" in re.search(r"var VOTE_ETA = '([^']*)';", out).group(1)


def test_eta_uses_the_shared_timing_record():
    """Per-card times accumulate across packs because TIME_KEY is keyed on
    sheet_id, so pack 1's pace predicts the whole sheet."""
    out = _r(packset_total=320)
    assert "function __voteSecs()" in out
    assert "__timing.per" in out


def test_eta_is_marked_rough_until_five_cards():
    out = _r(packset_total=320)
    assert "secs.length >= 5 ? VOTE_ETA : VOTE_ETA_ROUGH" in out


def test_eta_reports_completion_rather_than_a_time():
    assert "var VOTE_DONE = 'all {total} decided';" in _r()


# ------------------------------------------------------------------ footer controls

def test_submit_controls_are_tagged_and_moved():
    out = _r()
    assert '<div class="votebar" id="voteBar">' in out
    assert '<button data-submit="1" class="dl" id="downloadBtn">' in out
    assert "document.querySelectorAll('[data-submit]')" in out


def test_the_foot_bar_sits_after_the_cards_and_is_always_reachable():
    """Sticky to the BOTTOM, so 'at the foot' never means 'scroll 3000px to
    submit' on a long pack."""
    out = _r()
    assert out.index('id="voteBar"') > out.index("<main")
    assert ".votebar { position:sticky; bottom:0;" in out


def test_pause_stays_with_its_clock_chip():
    """The pause toggle drives the ⏱ readout in the header tally; separating a
    control from what it operates is worse than one tidy bar."""
    out = _r()
    assert 'data-submit="1" type="button" class="pausebtn"' not in out


def test_navigation_is_not_moved():
    """Filters are used BEFORE deciding; they stay at the top, untagged."""
    out = _r()
    filt = out.index('<div class="filterbar" id="filterbar">')
    assert 'data-submit="1" id="filterbar"' not in out
    assert filt < out.index('id="voteBar"')


def test_relocation_names_no_absent_layer():
    """The first draft listed ids in JS, so a sheet without facets still carried
    'facetbar' and a sheet without the inbox still carried 'inboxBtn'."""
    out = _r(session_flow=False, hand_in=False, timing=False)
    js = re.search(r"var VOTE_TOTAL[\s\S]*?__voteProgress\(\);", out).group(0)
    for absent in ("facetbar", "inboxBtn", "flowUndoBtn", "handinBtn", "strictReviewerWrap"):
        assert absent not in js, "%s named in the relocation JS" % absent


def test_absent_layers_leave_no_tag():
    """A switched-off layer contributes no TAG. (`handinBtn` still appears in the
    mobile stylesheet, which names it unconditionally and predates V17 — so the
    assertion is about the tag, not about the identifier.)"""
    out = _r(session_flow=False, hand_in=False)
    assert 'data-submit="1" type="button" class="dl flowundo"' not in out
    assert 'data-submit="1" class="dl handin"' not in out


# ------------------------------------------------------------------ scroll to top

def test_auto_advance_lands_on_the_top_of_the_card():
    out = _r()
    assert "block: 'center'" not in out
    assert "block:'center'" not in out
    assert "block: 'start'" in out or "block:'start'" in out


def test_cards_clear_the_sticky_strips():
    assert ".card { scroll-margin-top:96px; }" in _r()


def test_donor_path_keeps_centre_alignment():
    """`extras=False` reproduces a pre-H779 shell byte-for-byte; V17 must not
    reach it. This is the fixture that caught the first draft."""
    from csl_pyutil import render_review_sheet as raw
    out = raw(_items(), _config(), extras=False)
    assert "block:'center'" in out or "block: 'center'" in out
    assert "voteprog" not in out


# ------------------------------------------------------------------ opt out + i18n

def test_opt_out_leaves_no_identifier():
    out = _r(vote_ux=False)
    for ident in ("voteProg", "voteBar", "VOTE_TOTAL", "__voteProgress",
                  "data-submit", "voteprog", "votebar"):
        assert ident not in out


def test_vote_ux_must_be_a_bool():
    with pytest.raises(TypeError, match="vote_ux"):
        _r(vote_ux="yes")


def test_ru_translates_every_v17_string():
    out = _r(packset_total=320, ui_strings=RU_UI_STRINGS)
    assert "по всему листу" in out
    assert "мин на все" in out
    assert "across the whole sheet" not in out
    assert "min left for all" not in out


def test_v17_progress_does_not_collide_with_v15():
    """They are different readouts — V15's chip counts THIS pack (and now lives in
    the footer), V17's bar counts the whole sheet — so they must not share a
    string, or translating one would silently rewrite the other."""
    assert UI_STRINGS["vote_progress"] is not UI_STRINGS["flow_progress"]
    out = _r()
    assert "var FLOW_PROGRESS = 'decided {n} of {total}';" in out
    assert "var VOTE_PROGRESS = '{n} of {total} across the whole sheet';" in out


def test_every_v17_key_has_a_russian_value():
    keys = {k for k in UI_STRINGS if k.startswith("vote_")}
    assert keys
    assert keys <= set(RU_UI_STRINGS)
