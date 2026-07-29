# -*- coding: utf-8 -*-
"""anatomy — the raw-markup colouring lifted from csl-atlas under H1808.

The first four tests pin the behaviour csl-atlas's cdsl_anatomy.py already had,
so its re-export shim cannot regress; the rest cover what H1808 added for the
second caller (SanskritLexicography's G5 print-readiness sheet).
"""
import re

from csl_pyutil import anatomy


def test_markup_stays_visible_and_payload_is_coloured():
    """The tags ARE the anatomy — stripping them was never the point."""
    out = anatomy.highlight("{#anApta#} <ls>P. 6,4,57.</ls>")
    assert "&lt;ls&gt;" in out and "&lt;/ls&gt;" in out
    assert anatomy.PARTS["sanskrit"][0] in out
    assert anatomy.PARTS["citation"][0] in out
    assert "P. 6,4,57." in out


def test_target_form_is_outlined():
    out = anatomy.highlight("{#As#} und {#gam#}", target="As")
    assert "outline:1px solid #56b6c2" in out
    assert out.count("outline:1px solid #56b6c2") == 1


def test_accents_inside_a_sanskrit_form_are_marked():
    out = anatomy.highlight("{#a/gni#}")
    assert "#ff7b72" in out


def test_pipe_separator_and_unknown_tags_survive():
    out = anatomy.highlight('<hom>2.</hom> {#As#}¦ <div n="v">x</div>')
    assert "¦" in out
    assert "&lt;div n=&quot;v&quot;&gt;" in out


def test_ab_defaults_to_abbreviation_but_caller_can_ask_for_crossref():
    """PWG wraps EVERY abbreviation in <ab>; csl-atlas judges cross-references and
    wants the brighter treatment for the same tag."""
    plain = anatomy.highlight("<ab>caus.</ab>")
    assert anatomy.PARTS["abbreviation"][0] in plain
    xref = anatomy.highlight("<ab>Vgl.</ab>", tag_parts={"ab": "crossref"})
    assert anatomy.PARTS["crossref"][0] in xref


def test_plain_hook_reaches_text_the_markup_does_not_delimit():
    """NWS-layer cards carry citations as bare text with no <ls> around them —
    without a hook there is nothing for a caller to attach to."""
    seen = []

    def hook(chunk):
        seen.append(chunk)
        return "<b>%s</b>" % chunk if "165" in chunk else None

    out = anatomy.highlight("{#Adika#} ṚV(Sā) I 165, 11", plain_hook=hook)
    assert any("165" in s for s in seen)
    assert "<b> ṚV(Sā) I 165, 11</b>" in out


def test_plain_hook_returning_none_falls_through_to_default():
    out = anatomy.highlight("{#As#} so", plain_hook=lambda chunk: None)
    assert "so" in out
    assert anatomy._PLAIN in out


def test_payload_hook_can_replace_a_citation_with_a_link():
    def hook(part, inner, attrs):
        return '<a href="#">%s</a>' % inner if part == "citation" else None

    out = anatomy.highlight("<ls>HARṢAC. 126,9</ls> {#As#}", payload_hook=hook)
    assert '<a href="#">HARṢAC. 126,9</a>' in out
    assert "&lt;ls&gt;" in out          # the tag itself still shows


def test_container_carries_the_anatomy_class_for_the_type_scale():
    """The inline `font:` shorthand would otherwise pin the block at 12.5px while
    the rest of the sheet scales."""
    assert 'class="anatomy"' in anatomy.highlight("x")


def test_legend_can_be_restricted_and_extended():
    out = anatomy.legend_html(parts=["sanskrit", "citation"],
                              extra_chips=[("#abcdef", "диасистемная помета")])
    assert "санскритская форма" in out
    assert "ботаническое" not in out
    assert "диасистемная помета" in out


def test_html_in_the_record_is_escaped_not_executed():
    out = anatomy.highlight('{%<script>alert(1)</script>%}')
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_empty_record_is_a_valid_empty_block():
    out = anatomy.highlight("")
    assert out.startswith('<div class="anatomy"')
    assert re.search(r"</div>$", out)
