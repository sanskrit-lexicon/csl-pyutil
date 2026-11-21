# -*- coding: utf-8 -*-
"""V18 (MG 21-11-2026) — the vote-sheet header collapses to ONE line by default.

A generator's subtitle carries a paragraph and often a summary table; the
sticky header ate half a screen before the first card. The whole intro (h1 +
.sub) now folds into a collapsed <details class="intro-collapse"> whose
summary is the compact one line the ruling specifies. The HUD (✅/❌/⏸/⏱/◯
chips, pause, V17 progress) stays outside the fold — the existing scripts
address those ids — and the screening banner (H1649) below the header stays
fully visible.
"""
import pytest

from csl_pyutil import render_review_sheet as _render_raw
from csl_pyutil import render_review_sheet_packset

from test_review_sheet import _config, _items, _screening, render_review_sheet


def test_intro_collapses_to_one_line_by_default():
    out = render_review_sheet(
        _items(), _config(title="Правила членения сложных слов PWG: ратификация"))
    assert '<details class="intro-collapse">' in out
    # default state is COLLAPSED: no open attribute anywhere on the details
    assert '<details class="intro-collapse" open' not in out
    # one compact line: short title (up to the first ':') + card count
    assert ('<summary><span class="intro-tri">&#9656;</span> '
            'Правила членения сложных слов PWG (2 шт.)</summary>') in out


def test_title_without_colon_folds_nothing():
    out = render_review_sheet(_items(), _config(title="Plain sheet title"))
    assert "Plain sheet title (2 шт.)</summary>" in out


def test_note_kwarg_enriches_the_summary():
    out = _render_raw(_items(), _config(), extras=True, screening=_screening(),
                      intro_summary_note=", 8 правил")
    assert "(2 шт., 8 правил)</summary>" in out


def test_note_must_be_a_string():
    with pytest.raises(TypeError, match="intro_summary_note"):
        _render_raw(_items(), _config(), extras=True, screening=_screening(),
                    intro_summary_note=8)


def test_hud_ids_stay_outside_the_fold():
    """The timer/progress JS addresses the tally chips by id; folding them
    would break V11/V12/V15/V17 — the wrap must carry the intro div only."""
    out = render_review_sheet(_items(), _config())
    end = out.index("</details>")
    assert out.index('id="tally"') > end
    for chip in ('id="c-approve"', 'id="c-reject"', 'id="c-defer"',
                 'id="t-total"', 'id="t-state"', 'id="pauseBtn"',
                 'id="c-unvoted"', 'id="voteProg"'):
        assert out.index(chip) > end, chip


def test_folded_intro_keeps_its_exact_bytes():
    out = render_review_sheet(_items(), _config())
    d0 = out.index('<details class="intro-collapse">')
    d1 = out.index("</details>")
    # h1 and .sub move inside the fold, byte-identical: the sheet_id display,
    # the export-context chip and the count_suffix/generated_label localize
    # patterns all still match them where they lay.
    assert d0 < out.index("<h1>Test Sheet — 2 items</h1>") < d1
    assert d0 < out.index('<div class="sub">Generated 2026-07-14 &middot; '
                          'sheet_id <code>test-sheet_scope</code>') < d1


def test_screening_banner_stays_visible_outside_the_fold():
    # H1649 compliance surface: below the header, never collapsed.
    out = render_review_sheet(_items(), _config())
    assert out.index('class="screening-banner"') > out.index("</header>")


def test_donor_path_has_no_fold():
    out = _render_raw(_items(), _config(), extras=False)
    assert "intro-collapse" not in out
    assert '<header class="top">\n  <div>\n    <h1>' in out


def test_note_refused_on_donor_path():
    # the donor fixture must stay byte-identical; a silently-dropped note is
    # a build error instead (same rule as screening=).
    with pytest.raises(ValueError, match="intro_summary_note"):
        _render_raw(_items(), _config(), extras=False, intro_summary_note=", x")


def test_localized_count_word():
    out = render_review_sheet(
        _items(), _config(ui_strings={"intro_items_word": "items"}))
    assert "(2 items)</summary>" in out
    assert "шт." not in out


def test_print_keeps_full_context():
    out = render_review_sheet(_items(), _config())
    # a closed <details> is UA-hidden and CSS cannot open it: the handler
    # flips the attribute around the print and restores it after.
    assert "beforeprint" in out and "afterprint" in out
    assert "details.intro-collapse" in out  # @media print rule present
    assert out.count("<script>") == out.count("</script>") == 1


def test_packset_forwards_the_note_to_every_pack():
    items = [{"id": "L%02d" % i, "filt": "a", "title": "t", "question": "q",
              "panels": []} for i in range(12)]
    res = render_review_sheet_packset(
        items, _config(pack_size=10), extras=True, screening=_screening(n_human=12),
        intro_summary_note=", pack note")
    assert res["parent"] is not None
    assert len(res["packs"]) == 2
    for pack in res["packs"]:
        assert "(10 шт., pack note)</summary>" in pack or \
               "(2 шт., pack note)</summary>" in pack
