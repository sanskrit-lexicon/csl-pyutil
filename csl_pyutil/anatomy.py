# -*- coding: utf-8 -*-
"""anatomy — colour-code the anatomy of a raw CDSL dictionary record.

A CDSL record body is a dense mix of SGML-ish tags (``<s>``, ``<lex>``, ``<ls>``,
``<ab>``) and brace markers (``{#…#}``, ``{%…%}``) whose classes differ per
dictionary. Dumped verbatim into a review card it is a wall of punctuation, and a
reviewer cannot see which clause the judgement rests on (H1646: "add dictionary
entry anatomy markup, the bright colors for different part of entry").

This module keeps the markup fully VISIBLE — the tags are the anatomy, not noise
to be stripped — but dims the delimiters and colours the payload by part class, so
the shape of the entry reads at a glance.

Provenance: written for csl-atlas's xref sheet (H1646) as
``scripts/lib/cdsl_anatomy.py``, lifted here unchanged in behaviour under H1808
when a SECOND sheet generator (SanskritLexicography's G5 print-readiness lane)
turned out to need the same thing and had no way to reach it — MG, voting that
sheet: "why entry anatomy is missing again? It must be a hook". One canonical
copy in the shared emitter's package is that fix; csl-atlas's file is now a
re-export shim.

Prior art it deliberately reuses rather than re-derives:

* Part taxonomy and colour semantics — the ``/entry-anatomy`` skill
  (``entry_anatomy.py``'s ``PARTS`` / ``DICT_MAPS``), which segments a CDSL entry
  into headword · grammar · etymology · sense · citation · cross-reference.
* The raw-markup highlighting approach and dark palette —
  ``SanskritLexicography/EntryAnatomy/build_entry_anatomy.py`` ``raw_highlight()``
  + ``GENERIC_EXTRA_CSS``, whose colours already sit on a dark panel.

Colours are INLINE ``style=`` attributes, not a stylesheet: the output has to drop
into any panel body of any sheet, including callers that pass no ``extra_css``.
The container carries ``class="anatomy"`` so the emitter's type scale can still
reach it (the ``!important`` scale layer outranks the inline ``font`` shorthand).
"""
import html
import re

#: Part class -> (colour, human label, extra CSS). Dark-panel palette, matching the
#: review sheet's own --panel2 (#1e222b). Labels drive the rendered legend.
#: Labels are Russian: the surfaces rendering this legend are review sheets, whose
#: reviewer reads Russian (H1648). Keys stay English machine identifiers.
PARTS = {
    "sanskrit": ("#e6c07b", "санскритская форма", ""),
    "gloss": ("#98c379", "перевод / значение", "font-style:italic"),
    "citation": ("#e06c75", "ссылка на источник", ""),
    "grammar": ("#d19a66", "грамматическая помета", ""),
    "abbreviation": ("#c9a227", "сокращение (<ab>)", ""),
    "crossref": ("#56b6c2", "маркер перекрёстной ссылки (cf. / Vgl.)", "font-weight:600"),
    "etymology": ("#61afef", "этимология / когнат", ""),
    "language": ("#7aa2c9", "название языка", ""),
    "taxon": ("#c678dd", "ботаническое / зоологическое название", ""),
    "homonym": ("#b57edc", "номер омонима", ""),
    "structure": ("#7f8c9b", "разделитель значения / раздела", ""),
}

#: Paired content tags -> part class. ``<s>``/``<s1>``/``<s2>`` are MW's Sanskrit
#: spans; ``<is>`` is PWG's.
#:
#: ``<ab>`` defaults to ``abbreviation`` — in PWG it wraps EVERY abbreviation
#: (``caus.``, ``gerund.``, ``v. a.``), of which cf./Vgl. is one case. csl-atlas's
#: xref sheet judges cross-references specifically and wants the brighter
#: ``crossref`` treatment, so it passes ``tag_parts={"ab": "crossref"}``.
TAG_PARTS = {
    "s": "sanskrit", "s1": "sanskrit", "s2": "sanskrit", "is": "sanskrit",
    "ns": "gloss",
    "ls": "citation",
    "lex": "grammar",
    "ab": "abbreviation",
    "etym": "etymology",
    "lang": "language",
    "bot": "taxon", "zoo": "taxon",
    "hom": "homonym",
}

#: Brace markers -> part class. ``{#…#}`` Sanskrit, ``{%…%}`` gloss (PWG/AP90),
#: ``{@…@}`` a sense/section number.
BRACE_PARTS = {"#": "sanskrit", "%": "gloss", "@": "structure"}

_DELIM = "#5c6773"          # tag/brace delimiters — present but receded
_ACCENT = "#ff7b72"         # Vedic accent marks inside a Sanskrit form
_PIPE = "#e06c75"           # the ¦ head/body separator
_PLAIN = "#d8dce2"          # untagged running text

_SCANNER = re.compile(
    r"(?P<pair><(?P<tag>s1|s2|s|is|ns|ls|lex|ab|etym|lang|bot|zoo|hom)\b(?P<attrs>[^>]*)>"
    r"(?P<inner>.*?)</(?P=tag)>)"
    r"|(?P<brace>\{(?P<bk>[#%@])(?P<binner>.*?)(?P=bk)\})"
    r"|(?P<other><[^>]+>)"
    r"|(?P<pipe>¦)",
    re.DOTALL,
)

#: Vedic accent / length marks CDSL writes inside SLP1 forms. Stripped only when
#: comparing a form against the highlight target.
_ACCENT_CHARS = "/\\^~"


def _strip_accents(text):
    return "".join(ch for ch in text if ch not in _ACCENT_CHARS)


def _span(text, colour, extra="", title=None, escape=True):
    body = html.escape(text) if escape else text
    style = "color:%s" % colour
    if extra:
        style += ";" + extra
    attrs = ' title="%s"' % html.escape(title) if title else ""
    return '<span style="%s"%s>%s</span>' % (style, attrs, body)


def _sanskrit_body(inner, target_norm):
    """Colour a Sanskrit payload, marking accents and the highlight target."""
    colour, _label, extra = PARTS["sanskrit"]
    pieces = []
    for ch in inner:
        if ch in _ACCENT_CHARS:
            pieces.append(_span(ch, _ACCENT, "font-weight:700"))
        else:
            pieces.append(html.escape(ch))
    body = "".join(pieces)
    if target_norm and _strip_accents(inner).strip() == target_norm:
        # This span IS the form the card is asking about.
        return (
            '<span style="background:rgba(86,182,194,.22);outline:1px solid #56b6c2;'
            'border-radius:3px;padding:0 2px" title="цель перекрёстной ссылки, о которой спрашивает эта карточка">'
            + _span(body, colour, extra, escape=False)
            + "</span>"
        )
    return _span(body, colour, extra, escape=False)


def highlight(raw, target=None, *, tag_parts=None, plain_hook=None, payload_hook=None):
    """Return colour-coded HTML for one raw CDSL record body.

    ``target`` is the SLP1 form under judgement; every Sanskrit span in the
    record equal to it (ignoring accent marks) is outlined.

    ``tag_parts`` overrides the tag -> part mapping for this call (merged over
    ``TAG_PARTS``), e.g. ``{"ab": "crossref"}``.

    ``plain_hook(text) -> html`` is called for every UNTAGGED run. A caller uses
    it to reach content the markup does not delimit — bare citations, bracketed
    diasystem tags — and is responsible for escaping what it returns. Return
    ``None`` to fall through to the default plain rendering.

    ``payload_hook(part, inner, attrs) -> html`` is called for each tagged
    payload before it is coloured; a caller returns ready HTML (e.g. an ``<ls>``
    citation rendered as a source link) or ``None`` to fall through.
    """
    text = str(raw or "")
    target_norm = _strip_accents(str(target or "").strip()) or None
    parts_map = dict(TAG_PARTS)
    if tag_parts:
        parts_map.update(tag_parts)

    def plain(chunk):
        if plain_hook is not None:
            got = plain_hook(chunk)
            if got is not None:
                return got
        return _span(chunk, _PLAIN)

    out = []
    pos = 0
    for m in _SCANNER.finditer(text):
        if m.start() > pos:
            out.append(plain(text[pos:m.start()]))
        if m.group("pair"):
            tag, attrs, inner = m.group("tag"), m.group("attrs") or "", m.group("inner")
            part = parts_map.get(tag, "structure")
            colour, label, extra = PARTS[part]
            out.append(_span("<%s%s>" % (tag, attrs), _DELIM, title=label))
            hooked = payload_hook(part, inner, attrs) if payload_hook is not None else None
            if hooked is not None:
                out.append(hooked)
            elif part == "sanskrit":
                out.append(_sanskrit_body(inner, target_norm))
            else:
                out.append(_span(inner, colour, extra, title=label))
            out.append(_span("</%s>" % tag, _DELIM, title=label))
        elif m.group("brace"):
            bk, inner = m.group("bk"), m.group("binner")
            part = BRACE_PARTS.get(bk, "structure")
            colour, label, extra = PARTS[part]
            out.append(_span("{" + bk, _DELIM, title=label))
            if part == "sanskrit":
                out.append(_sanskrit_body(inner, target_norm))
            else:
                out.append(_span(inner, colour, extra, title=label))
            out.append(_span(bk + "}", _DELIM, title=label))
        elif m.group("other"):
            # <div n="v">, <info lex="m"/> and friends: structural, kept visible but quiet.
            out.append(_span(m.group("other"), _DELIM, title="structural markup"))
        else:
            out.append(_span("¦", _PIPE, "font-weight:700", title="headword / body separator"))
        pos = m.end()
    if pos < len(text):
        out.append(plain(text[pos:]))
    return (
        '<div class="anatomy" style="background:#20242a;border-radius:6px;padding:12px 14px;'
        'font:12.5px/1.9 Consolas,\'Cascadia Mono\',monospace;white-space:pre-wrap;'
        'word-break:break-word">' + "".join(out) + "</div>"
    )


def legend_html(parts=None, extra_chips=()):
    """A compact swatch legend for the part classes, for one place on the sheet.

    ``parts`` restricts (and orders) the classes shown — pass only the ones the
    sheet's dictionary actually uses. ``extra_chips`` appends caller chips as
    ``(colour, label)`` pairs, for conventions this module does not own.
    """
    keys = list(parts or PARTS)
    chips = []
    for key in keys:
        colour, label, extra = PARTS[key]
        chips.append(
            '<span style="display:inline-block;margin:0 10px 4px 0;white-space:nowrap">'
            '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
            'background:%s;margin-right:5px;vertical-align:baseline"></span>'
            '<span style="color:%s;%s">%s</span></span>' % (colour, colour, extra, html.escape(label))
        )
    chips.append(
        '<span style="display:inline-block;margin:0 10px 4px 0;white-space:nowrap">'
        '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
        'background:rgba(86,182,194,.22);outline:1px solid #56b6c2;margin-right:5px"></span>'
        '<span style="color:#56b6c2">цель перекрёстной ссылки</span></span>'
    )
    for colour, label in extra_chips:
        chips.append(
            '<span style="display:inline-block;margin:0 10px 4px 0;white-space:nowrap">'
            '<span style="display:inline-block;width:10px;height:10px;border-radius:2px;'
            'background:%s;margin-right:5px;vertical-align:baseline"></span>'
            '<span style="color:%s">%s</span></span>' % (colour, colour, html.escape(label))
        )
    return '<div style="font-size:12px;line-height:1.9">' + "".join(chips) + "</div>"
