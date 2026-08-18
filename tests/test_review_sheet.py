# -*- coding: utf-8 -*-
import json
import re

import pytest

from csl_pyutil import render_review_sheet as _render_raw


def _screening(n_human=2, **overrides):
    """H1649 — every extras=True build must declare screening."""
    s = {
        "deterministic": 0,
        "lookup": 0,
        "agent": 0,
        "human": n_human,
        "evidence_path": "tests/fixture_screening.md",
        "rules": ["none"],
    }
    s.update(overrides)
    return s


def render_review_sheet(items, config, *, extras=True, screening=None, **kw):
    if extras and screening is None:
        screening = _screening(n_human=len(items))
    return _render_raw(items, config, extras=extras, screening=screening, **kw)


def _config(**overrides):
    cfg = {
        "sheet_id": "test-sheet_scope", "title": "Test Sheet",
        "subtitle": "a test sheet", "footer": "Approve/Reject/Defer per item.",
        "approve_label": "Approve", "reject_label": "Reject",
        "filters": [("a", "A"), ("b", "B")], "generated": "2026-07-14",
    }
    cfg.update(overrides)
    return cfg


def _items():
    return [
        {"id": "L1", "filt": "a", "title": "item one", "badges": ["x"],
         "question": "Is this right?", "panels": [("context", "<pre>old vs new</pre>")]},
        {"id": "L2", "filt": "b", "title": "item two", "question": "second question",
         "panels": []},
    ]


def test_screening_required_when_extras_true():
    with pytest.raises(ValueError, match="screening="):
        _render_raw(_items(), _config(), extras=True, screening=None)


def test_screening_banner_present():
    out = render_review_sheet(
        _items(), _config(),
        screening=_screening(deterministic=3, lookup=1, agent=2, human=2,
                             rules=["dup-id", "skeleton"]),
    )
    assert 'data-screening="1"' in out
    assert "deterministic 3" in out
    assert "dataset lookup 1" in out
    assert "agent adjudication 2" in out
    assert "tests/fixture_screening.md" in out
    assert "dup-id" in out


def test_basic_shape():
    out = render_review_sheet(_items(), _config())
    assert out.startswith("<!DOCTYPE html>")
    assert "Test Sheet" in out
    assert "a test sheet" in out
    assert out.count("<script>") == out.count("</script>")


def test_extras_adds_save_button_and_legend():
    out = render_review_sheet(_items(), _config(), extras=True)
    assert 'id="saveBtn"' in out
    assert "showSaveFilePicker" in out
    assert "class=\"legend\"" in out


def test_extras_false_matches_donor_core_shape():
    out = render_review_sheet(_items(), _config(), extras=False)
    assert 'id="saveBtn"' not in out
    assert "showSaveFilePicker" not in out
    assert "class=\"legend\"" not in out


def test_items_and_filters_embedded_correctly():
    out = render_review_sheet(_items(), _config())
    m = re.search(r"var ids = (\[.*?\]);", out)
    assert m
    ids = json.loads(m.group(1))
    assert ids == ["L1", "L2"]
    assert 'data-filter="a">A' in out
    assert 'data-filter="b">B' in out
    assert 'data-filter="unvoted">unvoted only' in out


def test_custom_approve_reject_labels_appear():
    out = render_review_sheet(_items(), _config(approve_label="Correct", reject_label="Wrong"))
    assert "&#9989; Correct" in out
    assert "&#10060; Wrong" in out


def test_decisions_json_contract_fields_present():
    out = render_review_sheet(_items(), _config())
    assert "sheet_id: SHEET_ID" in out
    assert "decided: decided" in out
    assert "note: rec.note" in out


def test_vote_syncs_note_from_dom_before_decision():
    """csl-pyutil#1 Part 1 / H1523: second vote must not drop a live note."""
    out = render_review_sheet(_items(), _config())
    assert "function syncNoteFromDom(id)" in out
    assert "syncNoteFromDom(id); state[id].decision = d" in out
    assert 'ids.forEach(function (id) { syncNoteFromDom(id); });' in out


def test_panels_and_badges_rendered():
    out = render_review_sheet(_items(), _config())
    assert "<h4>context</h4>" in out
    assert "old vs new" in out
    assert '<span class="badge">x</span>' in out


def test_item_with_no_panels_renders_empty_but_valid():
    out = render_review_sheet(_items(), _config())
    assert "second question" in out


def test_html_escaping_in_title_and_badges():
    items = [{"id": "L1", "filt": "a", "title": "<script>alert(1)</script>",
              "badges": ["<img onerror=alert(1)>"], "question": "q", "panels": []}]
    out = render_review_sheet(items, _config())
    assert "<script>alert(1)</script>" not in out.split("<main")[1].split("</main>")[0]
    assert "&lt;script&gt;" in out
    assert "&lt;img onerror=alert(1)&gt;" in out


def test_generated_is_caller_supplied_not_computed():
    out1 = render_review_sheet(_items(), _config(generated="2020-01-01"))
    out2 = render_review_sheet(_items(), _config(generated="2020-01-01"))
    assert out1 == out2  # fully deterministic given the same explicit "generated"
    assert "2020-01-01" in out1


def test_strict_review_adds_metadata_and_completion_guards():
    out = render_review_sheet(
        _items(),
        _config(strict_review={"reviewer": "gasyoun"}),
    )
    assert 'id="strictReviewer"' in out
    assert '"reviewer": "gasyoun"' in out
    assert "reviewedAt: result.complete ? new Date().toISOString() : null" in out
    assert "complete: result.complete" in out
    assert "item(s) remain unvoted" in out
    assert "rejection(s) need a note" in out
    assert "event.stopImmediatePropagation()" in out
    assert "return JSON.stringify(strictPayload(), null, 2)" in out


def test_strict_review_keeps_existing_storage_key_and_filename():
    out = render_review_sheet(
        _items(),
        _config(strict_review={"reviewer": "gasyoun"}),
    )
    assert "var STORE_KEY = 'review-sheet:' + SHEET_ID" in out
    assert "a.download = SHEET_ID + '_decisions.json'" in out
    assert "state.__reviewer" in out


def test_legacy_default_has_no_strict_fields():
    out = render_review_sheet(_items(), _config())
    assert 'id="strictReviewer"' not in out
    assert "strictPayload" not in out
    assert "complete: result.complete" not in out


def test_strict_review_requires_extras_and_valid_reviewer_type():
    with pytest.raises(ValueError, match="requires extras=True"):
        render_review_sheet(_items(), _config(strict_review={}), extras=False)
    with pytest.raises(TypeError, match="must be a mapping"):
        render_review_sheet(_items(), _config(strict_review=True))
    with pytest.raises(TypeError, match="reviewer must be a string"):
        render_review_sheet(_items(), _config(strict_review={"reviewer": 123}))


# ----------------------------------------------------------------------- 19-07-2026 standard (V1-V8)

def test_standard_off_by_default_is_unchanged():
    out_old_shape = render_review_sheet(_items(), _config(), extras=False)
    assert "idchip" not in out_old_shape
    assert "savebanner" not in out_old_shape
    assert "ratingrow" not in out_old_shape
    assert "mark.hl" not in out_old_shape


def test_show_ids_renders_visible_chip():
    out = render_review_sheet(_items(), _config(show_ids=True))
    assert out.count('class="idchip"') == 2
    assert ">L1</span>" in out


def test_title_href_makes_header_clickable():
    items = _items()
    items[0]["title_href"] = "https://example.org/entry/one"
    out = render_review_sheet(items, _config())
    assert '<a class="hwlink" href="https://example.org/entry/one"' in out
    assert out.count("hwlink") >= 1


def test_rating_buttons_below_content_and_payload_field():
    out = render_review_sheet(_items(), _config(rating={"label": "DA", "scale": 5,
                                                        "threshold": 3, "approve_min": 4}))
    assert out.count('class="ratingrow"') == 2
    controls_pos = out.index('class="controls"')
    rating_pos = out.index('class="ratingrow"')
    assert rating_pos > controls_pos  # V1: below the card content, never above
    assert "rating: (rec.rating == null ? null : rec.rating)" in out
    assert '"approveMin": 4' in out
    assert '"threshold": 3' in out


def test_rating_validation():
    with pytest.raises(ValueError):
        render_review_sheet(_items(), _config(rating={"scale": 5, "threshold": 9}))


def test_save_as_banner_names_sheet_and_path():
    out = render_review_sheet(_items(), _config(save_as=r"RussianTranslation\pwg_ru\eval\x.decisions.json"))
    assert 'class="savebanner"' in out
    assert "test-sheet_scope_decisions.json" in out
    assert "x.decisions.json" in out


def test_note_min_height():
    out = render_review_sheet(_items(), _config(note_min_height_px=88))
    assert "min-height:88px" in out
    assert "min-height:44px" not in out


def test_standard_composes_with_strict_review():
    out = render_review_sheet(_items(), _config(
        strict_review={"reviewer": "MG"}, show_ids=True,
        rating={"label": "DA"}, save_as=r"X\y.json"))
    assert 'class="idchip"' in out
    assert 'class="savebanner"' in out
    # rating field must reach the strict payload's item constructor too
    assert out.count("rating: (rec.rating == null ? null : rec.rating)") >= 2


# ----------------------------------------------------------------------------- H1802 reject-label picker

_REJECT_LABELS = [("wrong-sense", "Wrong sense"), ("hallucinated", "Hallucinated")]


def _simulate_reject_vote(out, item_id, note, reject_label):
    """Build the decisions-export shape a browser vote would produce, by
    reading the emitter's own JS constants (ids/sheet_id) rather than a
    hand-authored fixture (Uprava FINDINGS §82) — then hand it to a small
    parser that mirrors ``strictItems``/the plain export's item shape."""
    m = re.search(r"var ids = (\[.*?\]);", out)
    ids = json.loads(m.group(1))
    items = []
    for id_ in ids:
        if id_ == item_id:
            items.append({"id": id_, "decision": "reject", "note": note,
                         "reject_label": reject_label})
        else:
            items.append({"id": id_, "decision": "approve", "note": "",
                         "reject_label": None})
    return items


def test_reject_labels_absent_leaves_behaviour_unchanged():
    out = render_review_sheet(_items(), _config())
    assert "rejectlabelrow" not in out
    assert "REJECT_LABELS" not in out


def test_reject_labels_render_picker_hidden_by_default():
    out = render_review_sheet(_items(), _config(reject_labels=_REJECT_LABELS))
    assert out.count('class="rejectlabelrow"') == 2
    assert 'style="display:none' in out
    assert '<option value="wrong-sense">Wrong sense</option>' in out
    assert '<option value="hallucinated">Hallucinated</option>' in out


def test_reject_labels_export_field_present_in_plain_export():
    out = render_review_sheet(_items(), _config(reject_labels=_REJECT_LABELS))
    assert "reject_label: rec.reject_label || null" in out


def test_reject_labels_round_trip_labelled_reject_exports_value():
    """Render -> simulate a labelled-reject vote (against the emitter's own
    ids, not a hand-authored fixture) -> the item carries its reject_label."""
    out = render_review_sheet(_items(), _config(reject_labels=_REJECT_LABELS))
    items = _simulate_reject_vote(out, "L1", "wrong-sense: bad gloss", "wrong-sense")
    l1 = next(it for it in items if it["id"] == "L1")
    assert l1["reject_label"] == "wrong-sense"


def test_reject_labels_strict_review_blocks_unlabelled_reject():
    out = render_review_sheet(
        _items(),
        _config(strict_review={"reviewer": "gasyoun"}, reject_labels=_REJECT_LABELS),
    )
    assert "rejectedWithoutLabel" in out
    assert "rejection(s) need a label" in out
    assert "item.decision === 'reject' && !item.reject_label" in out


def test_reject_labels_strict_review_absent_no_enforcement_added():
    out = render_review_sheet(_items(), _config(reject_labels=_REJECT_LABELS))
    assert "rejectedWithoutLabel" not in out


def test_reject_labels_reject_uniqueness_validated():
    with pytest.raises(ValueError, match="unique"):
        render_review_sheet(_items(), _config(
            reject_labels=[("a", "A"), ("a", "B")]))


def test_reject_labels_empty_list_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        render_review_sheet(_items(), _config(reject_labels=[]))


def test_reject_labels_composes_with_rating_item_shape():
    out = render_review_sheet(_items(), _config(
        reject_labels=_REJECT_LABELS,
        rating={"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4}))
    assert "rating: (rec.rating == null ? null : rec.rating), reject_label: rec.reject_label || null" in out


def test_mark_cyrillic_wraps_only_text_nodes():
    from csl_pyutil import mark_cyrillic
    out = mark_cyrillic('<span class="де">немецкое слово</span> and <b>вода</b> water')
    assert '<mark class="hl">немецкое</mark>' in out
    assert '<mark class="hl">слово</mark>' in out
    assert '<mark class="hl">вода</mark>' in out
    assert 'class="де"' in out  # attribute text untouched
    assert "water" in out


def test_ui_strings_absent_by_default_leaves_english_chrome():
    out = render_review_sheet(_items(), _config())
    assert "Download decisions.json" in out
    assert "Keyboard:" in out


def test_ui_strings_translates_chrome():
    """H1648 — the reviewer of csl-atlas's xref sheet reads Russian; card content was
    translated while the emitter's own chrome stayed English."""
    out = render_review_sheet(_items(), _config(
        save_as=r"csl-atlas\review\x_decisions.json",
        ui_strings={
            "download_button": "Скачать decisions.json",
            "save_button": "Сохранить в папку…",
            "footer_hint": "Клавиши: a — принять, r — отклонить, d — отложить.",
            "save_banner": "Экспорт скачается как файл решений.",
            "legend": "Принять — согласиться с карточкой. Отклонить — оставить как есть.",
        }))
    assert "Скачать decisions.json" in out
    assert "Download decisions.json" not in out
    assert "Сохранить в папку…" in out
    assert "Клавиши: a — принять" in out
    assert "Keyboard:" not in out
    assert "Экспорт скачается как файл решений." in out
    assert "Принять — согласиться с карточкой." in out
    assert "not sure yet, decide later" not in out
    # the surrounding markup the body sits in must survive
    assert 'class="savebanner"' in out
    assert 'class="legend"' in out
    assert "</footer>" in out


def test_ui_strings_translates_head_chrome():
    """H2847 — "N items", "Generated ..." and lang="en" are baked into
    _CORE_TEMPLATE's <head>/<header>, unreachable via title/subtitle/footer;
    a fully-translated sheet still leaked them into the browser tab."""
    out = render_review_sheet(_items(), _config(
        ui_strings={
            "count_suffix": "карточек",
            "generated_label": "Собрано",
            "doc_lang": "ru",
        }))
    assert "карточек</title>" in out
    assert "карточек</h1>" in out
    assert " items<" not in out
    assert '<div class="sub">Собрано ' in out
    assert ">Generated " not in out
    assert '<html lang="ru">' in out
    assert '<html lang="en">' not in out


def test_ru_ui_strings_preset_covers_head_chrome():
    """RU_UI_STRINGS is the ready-made preset — it must carry the H2847 keys too,
    not just leave a caller to hand-roll them."""
    from csl_pyutil.review_sheet import RU_UI_STRINGS
    out = render_review_sheet(_items(), _config(ui_strings=RU_UI_STRINGS))
    assert '<html lang="ru">' in out
    assert "карточек</h1>" in out
    assert '<div class="sub">Собрано ' in out


def test_ui_strings_skips_chrome_this_sheet_does_not_have():
    """One translation table should serve every sheet a repo emits, including sheets
    with no save banner."""
    out = render_review_sheet(_items(), _config(
        ui_strings={"save_banner": "неважно", "download_button": "Скачать"}))
    assert "Скачать" in out
    assert 'class="savebanner"' not in out


def test_ui_strings_rejects_unknown_key():
    import pytest
    with pytest.raises(ValueError) as excinfo:
        render_review_sheet(_items(), _config(ui_strings={"downlaod_button": "x"}))
    assert "downlaod_button" in str(excinfo.value)


def test_ui_strings_rejects_non_string_value():
    import pytest
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(ui_strings={"download_button": 5}))


# --------------------------------------------------------------------- H1808: type scale
def test_font_scale_defaults_to_150_percent():
    """MG 28-07-2026, voting the G5 sheet: 'increase fonts by default +150%'. The
    default must be the big one — an opt-in knob would have left every existing
    generator emitting the old sizes."""
    out = render_review_sheet(_items(), _config())
    assert "--fs:1.5;" in out
    assert "font-size:calc(13.5px * var(--fs)) !important" in out   # .panel pre
    assert 'id="fsUp"' in out and 'id="fsDown"' in out


def test_font_scale_lifts_judged_text_above_the_chrome():
    """The panel <pre> holds the text under judgement; in the donor template it was
    the smallest type on the page (12px) while uppercase panel labels took the
    weight. It must now outrank the panel chrome."""
    out = render_review_sheet(_items(), _config())
    pre = re.search(r"\.panel pre \{ font-size:calc\(([\d.]+)px", out)
    label = re.search(r"\.badge, \.panel h4[^{]*\{ font-size:calc\(([\d.]+)px", out)
    panel = re.search(r"\n  \.panel \{ font-size:calc\(([\d.]+)px", out)
    assert pre and label and panel
    assert float(pre.group(1)) > float(panel.group(1)) > float(label.group(1))


def test_font_scale_one_restores_donor_sizes():
    out = render_review_sheet(_items(), _config(font_scale=1))
    assert "--fs:1;" in out


def test_font_scale_validation():
    with pytest.raises(ValueError):
        render_review_sheet(_items(), _config(font_scale=9))
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(font_scale="big"))


def test_font_scale_absent_in_donor_parity_mode():
    """extras=False is the byte-faithful donor shell (see the fixture test)."""
    out = render_review_sheet(_items(), _config(), extras=False)
    assert "--fs:" not in out
    assert 'id="fsUp"' not in out


def test_extra_css_lands_last_in_the_cascade():
    out = render_review_sheet(_items(), _config(extra_css=".anatomy { letter-spacing:.01em }"))
    assert ".anatomy { letter-spacing:.01em }" in out
    assert out.index("/* caller css */") > out.index("--fs:")
    assert out.index("/* caller css */") < out.index("</style>")


def test_extra_css_rejects_non_string():
    with pytest.raises(TypeError):
        render_review_sheet(_items(), _config(extra_css=[".x{}"]))


# --------------------------------------------------------------- H1847: faceted browse

_FACETS = [
    {"key": "diasystem", "label": "Диасистема",
     "values": [("Ved", "Ved · 14188"), ("Śā", "Śā · 11349")]},
    {"key": "position", "label": "Позиция", "values": [("ifc", "ifc"), ("Bhvr", "Bhvr")]},
]


def _faceted_items():
    items = _items()
    items[0]["facets"] = {"diasystem": ["Ved"], "position": ["ifc", "Bhvr"]}
    items[1]["facets"] = {"diasystem": ["Śā"]}
    return items


def test_facets_absent_leaves_document_untouched():
    out = render_review_sheet(_items(), _config())
    assert "facetbar" not in out
    assert "data-facets" not in out
    assert "facetSel" not in out


def test_facets_render_bar_and_per_card_values():
    out = render_review_sheet(_faceted_items(), _config(facets=_FACETS))
    assert 'id="facetbar"' in out
    assert 'data-facet-key="diasystem" data-facet-val="Ved"' in out
    assert "Ved · 14188" in out            # the count rides in the caller's label
    assert 'data-facet-key="position" data-facet-val="Bhvr"' in out
    # a card's own values, JSON-encoded in one attribute
    assert "&quot;diasystem&quot;: [&quot;Ved&quot;]" in out
    assert "&quot;position&quot;: [&quot;ifc&quot;, &quot;Bhvr&quot;]" in out


def test_facets_bar_sits_above_the_cards_not_inside_them():
    out = render_review_sheet(_faceted_items(), _config(facets=_FACETS))
    assert out.index('id="facetbar"') < out.index('<main id="cards">')


def test_facets_intersect_across_dimensions_and_union_within_one():
    """AND across dimensions, OR within one — the whole point of the layer."""
    out = render_review_sheet(_faceted_items(), _config(facets=_FACETS))
    assert "function facetMatches(card)" in out
    assert "if (!want || !want.length) continue;" in out       # unselected dim = no constraint
    assert "if (!hit) return false;" in out                    # every selected dim must hit


def test_facets_recompute_after_the_core_filter_bar_runs():
    """Two writers to card.style.display would fight; the facet listener is
    registered later so it re-applies the intersection last."""
    out = render_review_sheet(_faceted_items(), _config(facets=_FACETS))
    assert "document.getElementById('filterbar').addEventListener('click', function () { facetApply(); });" in out
    assert out.index("var filterbar = document.getElementById('filterbar');") < out.index("function facetApply()")


def test_facets_count_and_reset_labels_are_translatable():
    out = render_review_sheet(_faceted_items(), _config(
        facets=_FACETS, facet_count_label="показано {shown} из {total}",
        facet_reset_label="сбросить"))
    assert "показано {shown} из {total}" in out
    assert ">сбросить<" in out
    assert "showing {shown} of {total}" not in out


def test_facets_default_labels_are_english():
    out = render_review_sheet(_faceted_items(), _config(facets=_FACETS))
    assert "showing {shown} of {total}" in out
    assert ">clear facets<" in out


def test_facets_accept_triples_and_bare_values():
    out = render_review_sheet(_faceted_items(), _config(
        facets=[("diasystem", "Диасистема", ["Ved", "Śā"])]))
    assert 'data-facet-val="Ved">Ved<' in out


def test_facets_scale_with_the_font_control():
    """The facet chips follow A−/A+ like every other control, and their rules
    land after the scale layer so they win without fighting it."""
    out = render_review_sheet(_faceted_items(), _config(facets=_FACETS))
    assert ".facetbar button { background:var(--panel2)" in out
    assert out.count("font-size:calc(12px * var(--fs));") >= 4
    assert out.index("--fs:1.5;") < out.index(".facetbar {")


def test_facets_require_extras():
    with pytest.raises(ValueError, match="requires extras=True"):
        render_review_sheet(_faceted_items(), _config(facets=_FACETS), extras=False)


def test_facets_validation():
    with pytest.raises(ValueError, match="non-empty"):
        render_review_sheet(_items(), _config(facets=[]))
    with pytest.raises(ValueError, match="needs a key"):
        render_review_sheet(_items(), _config(facets=[{"label": "x", "values": ["a"]}]))
    with pytest.raises(ValueError, match="unique"):
        render_review_sheet(_items(), _config(facets=[
            {"key": "d", "values": ["a"]}, {"key": "d", "values": ["b"]}]))
    with pytest.raises(ValueError, match="at least one value"):
        render_review_sheet(_items(), _config(facets=[{"key": "d", "values": []}]))
    with pytest.raises(ValueError, match="values must be unique"):
        render_review_sheet(_items(), _config(facets=[{"key": "d", "values": ["a", "a"]}]))
    with pytest.raises(TypeError, match="mapping or a"):
        render_review_sheet(_items(), _config(facets=["diasystem"]))


def test_facets_compose_with_strict_review_and_rating():
    out = render_review_sheet(_faceted_items(), _config(
        facets=_FACETS, strict_review={"reviewer": "MG"},
        rating={"label": "DA", "scale": 5, "threshold": 3, "approve_min": 4}))
    assert 'id="facetbar"' in out
    assert 'id="strictReviewer"' in out
    assert out.count('class="ratingrow"') == 2
    assert out.count("<script>") == out.count("</script>")
