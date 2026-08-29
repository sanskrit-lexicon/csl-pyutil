# -*- coding: utf-8 -*-
"""review_sheet — the shared render_review_sheet() HTML review/voting sheet emitter.

Ported byte-for-byte (core template + render_card + doc-assembly) from
SanskritLexicography/RussianTranslation/src/build_h180_review_sheets.py — the
richest of six independently hand-rolled review-sheet shells found across four
repos (H925). That donor's own docstring already describes itself as reusing
build_renou_pilot_sheet.py's pattern, generalized with a config-driven
approve/reject label, a filter bar, and per-card "panels" list — this port
keeps that exact generalization, changing nothing about the CORE template so a
byte-identical-output fixture test can prove the port is faithful.

extras=True (the default for new callers) additionally folds in what H779
(12-07-2026) mandated but no existing shell actually implemented: a
File-System-Access-API "Save to folder" auto-save control and a button-legend
footer. These are appended/inserted via targeted string surgery on stable
anchors in the core template, not by touching the core template itself — so
extras=False reproduces the donor's literal historical output exactly (see
tests/test_fixture_byte_identical.py), while extras=True is what real callers
should use.

One deliberate deviation from byte-for-byte donor fidelity: the download
button's `a.download` filename is `SHEET_ID + '_decisions.json'`, not the
donor's literal `'decisions.json'` — the generic name collided with every
other sheet's export in a flat Downloads/ folder, violating the org's
no-generic-filename convention (found 14-07-2026 auditing the H931 port; see
tests/fixtures/h180_typology_golden.html, regenerated to match).
"""
import html
import json
import re
import warnings

from csl_pyutil.evidence import PreflightError, PreflightWarning, preflight

__version__ = "0.23.0"

__all__ = ["render_review_sheet", "render_review_sheet_packset", "esc", "mark_cyrillic",
           "RU_UI_STRINGS"]


def esc(s):
    return html.escape("" if s is None else str(s))


_CYR_RUN = re.compile(u"[Ѐ-ӿ][Ѐ-ӿ́-]*")
_TAG_SPLIT = re.compile(r"(<[^>]+>)")


def mark_cyrillic(html_text):
    """Wrap every Cyrillic word-run in ``<mark class="hl">`` (V7 of the
    19-07-2026 review-sheet standard: the Russian words under judgment are
    color-highlighted so the eye lands on what is being reviewed). Operates
    only on text between tags, so existing markup is never corrupted. The
    matching ``mark.hl`` style ships with the standard CSS layer — callers
    just wrap their card HTML with this before passing it in."""
    parts = _TAG_SPLIT.split(html_text)
    for i, part in enumerate(parts):
        if part.startswith("<"):
            continue
        parts[i] = _CYR_RUN.sub(lambda m: '<mark class="hl">%s</mark>' % m.group(0), part)
    return "".join(parts)


# ----------------------------------------------------------------------------- core template
# Ported verbatim from build_h180_review_sheets.py's TEMPLATE — do not reformat
# or "clean up" whitespace/quoting here; a byte-identical fixture test depends
# on this string matching the donor exactly.
_CORE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="dark">
<title>%(title)s — %(n)d items</title>
<style>
  :root { color-scheme: dark; --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --text:#e6e6e6; --muted:#9aa0aa;
          --accent:#5b8cff; --ok:#3fb950; --bad:#f85149; --defer:#d29922; --border:#2a2f3a; }
  * { box-sizing: border-box; }
  body { background:var(--bg); color:var(--text); font-family:-apple-system,Segoe UI,Roboto,sans-serif;
         margin:0; padding:0 0 120px 0; }
  header.top { position:sticky; top:0; z-index:10; background:var(--panel); border-bottom:1px solid var(--border);
               padding:14px 20px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;}
  header.top h1 { font-size:16px; margin:0; }
  header.top .sub { color:var(--muted); font-size:12px; max-width:760px; }
  .tally { display:flex; gap:14px; font-size:13px; }
  .tally span.count { font-weight:700; }
  .tally .approve { color:var(--ok); } .tally .reject { color:var(--bad); }
  .tally .defer { color:var(--defer); } .tally .unvoted { color:var(--muted); }
  .toolbar { padding:10px 20px; display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  button.dl { background:var(--accent); color:#fff; border:none; padding:8px 14px; border-radius:6px;
              cursor:pointer; font-size:13px; }
  button.dl:hover { opacity:.9; }
  .filterbar { display:flex; gap:6px; flex-wrap:wrap; }
  .filterbar button { background:var(--panel2); border:1px solid var(--border); color:var(--text);
                       padding:6px 10px; border-radius:14px; font-size:12px; cursor:pointer; }
  .filterbar button.active { border-color:var(--accent); color:var(--accent); }
  main { max-width:980px; margin:0 auto; padding:10px 20px; }
  .card { background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:16px;
          margin-bottom:16px; }
  .card.voted-approve { border-left:4px solid var(--ok); }
  .card.voted-reject { border-left:4px solid var(--bad); }
  .card.voted-defer { border-left:4px solid var(--defer); }
  .card header { display:flex; justify-content:space-between; align-items:baseline; }
  .card .hw { font-size:18px; font-weight:700; }
  .badge { font-size:11px; background:var(--panel2); padding:2px 8px; border-radius:10px;
           margin-left:8px; color:var(--muted); }
  .question { margin:8px 0 12px; font-size:14px; }
  .panel { background:var(--panel2); border-radius:8px; padding:10px 12px; font-size:13px; margin-bottom:10px; }
  .panel h4 { margin:0 0 6px; font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); }
  .panel pre { white-space:pre-wrap; word-break:break-word; margin:0; font-size:12px; line-height:1.45; }
  .chip { display:inline-block; background:#263042; border-radius:5px; padding:2px 7px; margin:2px 3px 2px 0; font-size:12px; }
  .muted { color:var(--muted); font-style:italic; }
  .controls { display:flex; align-items:center; gap:8px; margin-top:4px; }
  button.vote { border:1px solid var(--border); background:var(--panel2); color:var(--text);
                padding:7px 12px; border-radius:6px; cursor:pointer; font-size:13px; }
  button.vote.approve.active { background:var(--ok); border-color:var(--ok); color:#04240b; }
  button.vote.reject.active { background:var(--bad); border-color:var(--bad); color:#2a0a08; }
  button.vote.defer.active { background:var(--defer); border-color:var(--defer); color:#2a1d02; }
  .vote-state { margin-left:6px; font-size:12px; color:var(--muted); }
  textarea.note { width:100%%; margin-top:10px; min-height:44px; background:#11141a !important; color:#e6e6e6 !important;
                  -webkit-text-fill-color:#e6e6e6; border:1px solid var(--border); border-radius:6px; padding:8px; font-size:13px;
                  font-family:inherit; resize:vertical; }
  textarea.note::placeholder { color:var(--muted); opacity:1; }
  footer.hint { max-width:980px; margin:20px auto; padding:0 20px; color:var(--muted); font-size:12px; }
  kbd { background:#263042; border-radius:4px; padding:1px 5px; font-size:11px; }
</style>
</head>
<body>
<header class="top">
  <div>
    <h1>%(title)s — %(n)d items</h1>
    <div class="sub">Generated %(generated)s &middot; sheet_id <code>%(sheet_id)s</code> &middot; %(subtitle)s</div>
  </div>
  <div class="tally" id="tally">
    <span class="approve">&#9989; <span class="count" id="c-approve">0</span></span>
    <span class="reject">&#10060; <span class="count" id="c-reject">0</span></span>
    <span class="defer">&#9208; <span class="count" id="c-defer">0</span></span>
    <span class="unvoted">&#9711; <span class="count" id="c-unvoted">%(n)d</span></span>
  </div>
</header>
<div class="toolbar">
  <button class="dl" id="downloadBtn">Download decisions.json</button>
  <div class="filterbar" id="filterbar">%(filters)s</div>
</div>
<main id="cards">
%(cards)s
</main>
<footer class="hint">%(footer)s Keyboard: <kbd>a</kbd> %(approve_label)s &middot; <kbd>r</kbd> %(reject_label)s
  &middot; <kbd>d</kbd> defer &middot; <kbd>&darr;</kbd>/<kbd>&uarr;</kbd> next/prev. Votes autosave to
  this browser's localStorage; click "Download decisions.json" when done (unvoted items export with
  decision:null).</footer>
<script>
(function () {
  var SHEET_ID = %(sheet_id_json)s;
  var STORE_KEY = 'review-sheet:' + SHEET_ID;
  var ids = %(ids_json)s;
  var state = {};
  try { state = JSON.parse(localStorage.getItem(STORE_KEY) || '{}') || {}; } catch (e) { state = {}; }
  function tally() {
    var c = { approve:0, reject:0, defer:0 };
    ids.forEach(function (id) { var v = state[id] && state[id].decision; if (v && c.hasOwnProperty(v)) c[v]++; });
    document.getElementById('c-approve').textContent = c.approve;
    document.getElementById('c-reject').textContent = c.reject;
    document.getElementById('c-defer').textContent = c.defer;
    document.getElementById('c-unvoted').textContent = ids.length - c.approve - c.reject - c.defer;
  }
  function applyCardUI(card) {
    var id = card.getAttribute('data-id'); var rec = state[id] || {};
    card.classList.remove('voted-approve','voted-reject','voted-defer');
    card.querySelectorAll('button.vote').forEach(function (b) { b.classList.toggle('active', b.getAttribute('data-vote') === rec.decision); });
    card.querySelector('.vote-state').textContent = rec.decision ? rec.decision : 'unvoted';
    if (rec.decision) card.classList.add('voted-' + rec.decision);
    var ta = card.querySelector('textarea.note'); if (rec.note && !ta.value) ta.value = rec.note;
  }
  function save() { localStorage.setItem(STORE_KEY, JSON.stringify(state)); tally(); }
  // H1523 residual / csl-pyutil#1 Part 1: always re-read the live textarea on vote
  // and before export so a second vote click (or a missed `input` event) cannot
  // drop a note that is still visible in the card.
  function syncNoteFromDom(id) {
    state[id] = state[id] || {};
    var card = document.querySelector('.card[data-id="' + id + '"]');
    if (!card) return;
    var ta = card.querySelector('textarea.note');
    if (ta) state[id].note = ta.value;
  }
  function vote(id, d) { syncNoteFromDom(id); state[id].decision = d; save(); }
  function noteChange(id, t) { state[id] = state[id] || {}; state[id].note = t; save(); }
  document.querySelectorAll('.card').forEach(function (card) {
    var id = card.getAttribute('data-id'); applyCardUI(card);
    card.querySelectorAll('button.vote').forEach(function (btn) {
      btn.addEventListener('click', function () { vote(id, btn.getAttribute('data-vote')); applyCardUI(card); });
    });
    var ta = card.querySelector('textarea.note'); ta.addEventListener('input', function () { noteChange(id, ta.value); });
  });
  tally();
  document.getElementById('downloadBtn').addEventListener('click', function () {
    ids.forEach(function (id) { syncNoteFromDom(id); });
    var decided = ids.filter(function (id) { return state[id] && state[id].decision; }).length;
    var payload = { sheet_id: SHEET_ID, generated: %(generated_json)s, decided: decided,
      items: ids.map(function (id) { var rec = state[id] || {}; return { id: id, decision: rec.decision || null, note: rec.note || '' }; }) };
    var blob = new Blob([JSON.stringify(payload, null, 2)], { type:'application/json' });
    var url = URL.createObjectURL(blob); var a = document.createElement('a');
    a.href = url; a.download = SHEET_ID + '_decisions.json'; document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  });
  var filterbar = document.getElementById('filterbar');
  filterbar.addEventListener('click', function (e) {
    var btn = e.target.closest('button[data-filter]'); if (!btn) return;
    filterbar.querySelectorAll('button').forEach(function (b) { b.classList.remove('active'); });
    btn.classList.add('active'); var f = btn.getAttribute('data-filter');
    document.querySelectorAll('.card').forEach(function (card) {
      var show = true;
      if (f === 'unvoted') { var id = card.getAttribute('data-id'); show = !(state[id] && state[id].decision); }
      else if (f !== 'all') { show = card.getAttribute('data-filt') === f; }
      card.style.display = show ? '' : 'none';
    });
  });
  var cardsEl = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var activeIdx = 0;
  function visibleCards() { return cardsEl.filter(function (c) { return c.style.display !== 'none'; }); }
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'TEXTAREA') return;
    var vis = visibleCards(); if (!vis.length) return;
    if (activeIdx >= vis.length) activeIdx = vis.length - 1;
    var card = vis[activeIdx]; var id = card.getAttribute('data-id');
    if (e.key === 'a') { vote(id, 'approve'); applyCardUI(card); }
    else if (e.key === 'r') { vote(id, 'reject'); applyCardUI(card); }
    else if (e.key === 'd') { vote(id, 'defer'); applyCardUI(card); }
    else if (e.key === 'ArrowDown') { activeIdx = Math.min(activeIdx + 1, vis.length - 1); vis[activeIdx].scrollIntoView({behavior:'smooth',block:'center'}); }
    else if (e.key === 'ArrowUp') { activeIdx = Math.max(activeIdx - 1, 0); vis[activeIdx].scrollIntoView({behavior:'smooth',block:'center'}); }
    else return;
    e.preventDefault();
  });
})();
</script>
</body>
</html>
'''


def _fmt_typology_chip(entry):
    """U7 (H2846) — a typology/classification label chip: the label plus its
    count on this card and its share of the sheet's population, never bare."""
    share_txt = "share unknown" if entry.get("share_unknown") else "%.0f%%" % (100 * entry["share"])
    return '<span class="badge badge-typology" title="U7: count + population share">%s (n=%s, %s)</span>' % (
        esc(entry["label"]), esc(entry["n"]), esc(share_txt))


def render_card(item, approve_label, reject_label, *, show_id=False, rating=None,
                reject_labels=None, split_layout=False):
    """Ported verbatim from build_h180_review_sheets.py — item shape:
    {"id", "filt", "title", "badges": [...], "question" (HTML), "panels":
    [(heading, html_body), ...], "note_placeholder" (optional), "title_href"
    (optional — V4 of the 19-07-2026 standard: the card header becomes a
    clickable link to the full source entry), "typology" (optional — U7 of
    the H2846 content standard: ``[{"label", "n", "share"}, ...]``, rendered
    as chips distinct from plain ``badges`` — see ``_check_typology_stats``)}.

    ``split_layout=True`` (opt-in, 0.22.0) renders ``item["left"]`` /
    ``item["right"]`` as a two-column grid and wraps ``item["store_markup"]``
    in a closed ``<details>``. ``panels`` may be empty in that mode. With
    ``show_id=False``, ``rating=None``, ``reject_labels=None``,
    ``split_layout=False`` and no ``title_href``/``typology`` the output is
    byte-identical to the v0.2.0 renderer (fixture contract)."""
    if split_layout:
        body = (
            '<div class="card-split">'
            '<div class="col-de">%s</div>'
            '<div class="col-ru">%s</div>'
            '</div>' % (item["left"], item["right"])
        )
        if item.get("store_markup"):
            body += (
                '<details class="store-details">'
                '<summary class="store-link">store markup — quote this in the note</summary>'
                '%s</details>' % item["store_markup"]
            )
        panel_src = item.get("panels") or ()
    else:
        panel_src = item["panels"]
        body = ""
    panels = body + "".join(
        '<div class="panel"><h4>%s</h4>%s</div>' % (esc(h4), pbody)
        for h4, pbody in panel_src)
    badges = "".join('<span class="badge">%s</span>' % esc(b) for b in item.get("badges", []))
    badges += "".join(_fmt_typology_chip(t) for t in item.get("typology", []))
    title_html = esc(item["title"])
    if item.get("title_href"):
        title_html = '<a class="hwlink" href="%s" target="_blank" rel="noopener">%s</a>' % (
            esc(item["title_href"]), title_html)
    idchip = ""
    if show_id:
        idchip = '<span class="idchip" title="card id — cite this id back when discussing this card">%s</span>' % esc(item["id"])
    rating_row = ""
    if rating is not None:
        btns = "".join('<button class="rate" data-rate="%d">%d</button>' % (v, v)
                       for v in range(1, rating["scale"] + 1))
        rating_row = ('\n    <div class="ratingrow"><span class="ratinglabel">%s</span>%s'
                      '<span class="rate-state">unrated</span></div>' % (esc(rating["label"]), btns))
    reject_label_row = ""
    if reject_labels:
        options = "".join('<option value="%s">%s</option>' % (esc(v), esc(l))
                          for v, l in reject_labels)
        reject_label_row = (
            '\n    <div class="rejectlabelrow" style="display:none;margin-top:8px">'
            '<span class="rejectlabellabel" style="font-size:12px;color:var(--muted);'
            'margin-right:6px">Reason</span>'
            '<select class="reject-label-select" style="background:#11141a;color:var(--text);'
            'border:1px solid var(--border);border-radius:6px;padding:6px 8px;font-size:13px">'
            '<option value="">— select —</option>%s</select></div>' % options)
    # H1847: a card's facet values ride as one JSON attribute rather than N
    # `data-facet-<key>` attributes — dimensions are caller-defined, and a
    # multi-valued dimension (a card carrying both `ifc` and `Bhvr`) has no
    # honest single-attribute encoding. Absent key => attribute absent => the
    # pre-H1847 byte-identical card.
    facet_attr = ""
    if item.get("facets"):
        facet_attr = " data-facets=\"%s\"" % esc(
            json.dumps({str(k): [str(v) for v in vals]
                        for k, vals in item["facets"].items()},
                       ensure_ascii=False, sort_keys=True))
    return '''
  <section class="card" data-id="%s" data-filt="%s"%s>
    <header><div class="hw">%s %s</div>%s</header>
    <div class="question">%s</div>
    %s
    <div class="controls">
      <button class="vote approve" data-vote="approve">&#9989; %s</button>
      <button class="vote reject" data-vote="reject">&#10060; %s</button>
      <button class="vote defer" data-vote="defer">&#9208; Defer</button>
      <span class="vote-state">unvoted</span>
    </div>%s%s
    <textarea class="note" placeholder="%s"></textarea>
  </section>''' % (esc(item["id"]), esc(item["filt"]), facet_attr, title_html, badges, idchip,
                   item["question"], panels, esc(approve_label), esc(reject_label),
                   reject_label_row, rating_row,
                   esc(item.get("note_placeholder", "free-text note (optional)")))


# ----------------------------------------------------------------------------- H779 extras
# Inserted via targeted string surgery on stable anchors in the core template
# (never by editing _CORE_TEMPLATE itself) — H779 (12-07-2026) mandated a
# File System Access API auto-save control and a button-legend footer that no
# existing hand-rolled shell actually implemented.
_SAVE_BUTTON = '<button class="dl" id="saveBtn" style="display:none;margin-left:8px">Save to folder…</button>'

_LEGEND_HTML = '''<div class="legend" style="max-width:980px;margin:0 auto 20px;padding:0 20px;color:var(--muted);font-size:12px">
  <b>Approve</b> = accept the proposed change/answer shown on the card (no separate "approve as-is" —
  approving means agreeing as written). <b>Reject</b> = keep the current entry/answer unchanged.
  <b>Defer</b> = not sure yet, decide later. The note field is for requesting a partial tweak instead
  of an outright reject.
</div>
'''

_AUTOSAVE_JS = '''
  var saveHandle = null, saveTimer = null;
  function exportPayload() {
    if (typeof syncNoteFromDom === 'function') {
      ids.forEach(function (id) { syncNoteFromDom(id); });
    }
    var decided = ids.filter(function (id) { return state[id] && state[id].decision; }).length;
    var nowIso = new Date().toISOString();
    return JSON.stringify({ sheet_id: SHEET_ID, generated: nowIso, reviewedAt: nowIso, decided: decided,
      items: ids.map(function (id) { var rec = state[id] || {}; return { id: id, decision: rec.decision || null, note: rec.note || '' }; }) }, null, 2);
  }
  function scheduleAutosave() {
    if (!saveHandle) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(function () {
      saveHandle.createWritable().then(function (w) {
        w.write(exportPayload()).then(function () { w.close(); });
      }).catch(function () {});
    }, 1000);
  }
  var _origSave = save;
  save = function () { _origSave(); scheduleAutosave(); };
  if (window.showSaveFilePicker) {
    var saveBtn = document.getElementById('saveBtn');
    saveBtn.style.display = '';
    saveBtn.addEventListener('click', function () {
      window.showSaveFilePicker({suggestedName: SHEET_ID + '_decisions.json'}).then(function (h) {
        saveHandle = h; scheduleAutosave();
      }).catch(function () {});
    });
  }
'''

_AUTOSAVE_EXPORT_FUNCTION = '''  function exportPayload() {
    if (typeof syncNoteFromDom === 'function') {
      ids.forEach(function (id) { syncNoteFromDom(id); });
    }
    var decided = ids.filter(function (id) { return state[id] && state[id].decision; }).length;
    var nowIso = new Date().toISOString();
    return JSON.stringify({ sheet_id: SHEET_ID, generated: nowIso, reviewedAt: nowIso, decided: decided,
      items: ids.map(function (id) { var rec = state[id] || {}; return { id: id, decision: rec.decision || null, note: rec.note || '' }; }) }, null, 2);
  }
'''

_STRICT_REVIEWER_HTML = '''<label id="strictReviewerWrap" style="display:flex;align-items:center;gap:6px;font-size:13px">
    Reviewer <input id="strictReviewer" type="text" autocomplete="name" style="background:#11141a;color:var(--text);border:1px solid var(--border);border-radius:6px;padding:7px 9px" />
  </label>
  <span id="strictReviewError" role="alert" style="color:var(--bad);font-size:12px"></span>'''


def _strict_review_js(policy):
    """Return the additive strict-export controller for a normalized policy."""
    return '''
  var STRICT_REVIEW = %s;
  var strictReviewer = document.getElementById('strictReviewer');
  var strictError = document.getElementById('strictReviewError');
  strictReviewer.value = state.__reviewer || STRICT_REVIEW.reviewer || '';
  function strictItems() {
    return ids.map(function (id) {
      var rec = state[id] || {};
      return { id: id, decision: rec.decision || null, note: rec.note || '' };
    });
  }
  function strictValidation() {
    var items = strictItems();
    var reviewer = strictReviewer.value.trim();
    var unvoted = STRICT_REVIEW.requireAllVotes ? items.filter(function (item) { return !item.decision; }) : [];
    var rejectedWithoutNote = STRICT_REVIEW.requireRejectNote ? items.filter(function (item) {
      return item.decision === 'reject' && !item.note.trim();
    }) : [];
    var errors = [];
    if (!reviewer) errors.push('reviewer is required');
    if (unvoted.length) errors.push(unvoted.length + ' item(s) remain unvoted');
    if (rejectedWithoutNote.length) errors.push(rejectedWithoutNote.length + ' rejection(s) need a note');
    return { reviewer: reviewer, items: items, complete: errors.length === 0, errors: errors };
  }
  function strictPayload() {
    var result = strictValidation();
    var decided = result.items.filter(function (item) { return !!item.decision; }).length;
    return { sheet_id: SHEET_ID, generated: %s, decided: decided,
      reviewer: result.reviewer, reviewedAt: result.complete ? new Date().toISOString() : null,
      complete: result.complete, items: result.items };
  }
  strictReviewer.addEventListener('input', function () {
    state.__reviewer = strictReviewer.value;
    strictError.textContent = '';
    save();
  });
  document.getElementById('downloadBtn').addEventListener('click', function (event) {
    event.preventDefault(); event.stopImmediatePropagation();
    var result = strictValidation();
    if (!result.complete) {
      strictError.textContent = result.errors.join('; ');
      if (!result.reviewer) strictReviewer.focus();
      return;
    }
    strictError.textContent = '';
    var blob = new Blob([JSON.stringify(strictPayload(), null, 2)], { type:'application/json' });
    var url = URL.createObjectURL(blob); var a = document.createElement('a');
    a.href = url; a.download = SHEET_ID + '_decisions.json'; document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  }, true);
''' % (json.dumps(policy), json.dumps(policy["generated"]))


def _add_strict_review(doc, policy):
    """Add strict review metadata and final-export validation without touching core."""
    toolbar_anchor = '<div class="filterbar" id="filterbar">'
    if toolbar_anchor not in doc:
        raise ValueError("review-sheet toolbar anchor is missing")
    doc = doc.replace(toolbar_anchor, _STRICT_REVIEWER_HTML + '\n  ' + toolbar_anchor, 1)

    autosave_export = _AUTOSAVE_EXPORT_FUNCTION
    if autosave_export not in doc:
        raise ValueError("strict_review requires extras=True auto-save support")
    doc = doc.replace(
        autosave_export,
        "  function exportPayload() {\n    return JSON.stringify(strictPayload(), null, 2);\n  }\n",
        1,
    )
    autosave_anchor = "\n  var saveHandle = null, saveTimer = null;"
    if autosave_anchor not in doc:
        raise ValueError("review-sheet auto-save anchor is missing")
    return doc.replace(autosave_anchor, _strict_review_js(policy) + autosave_anchor, 1)


# ----------------------------------------------------------------------------- 19-07-2026 standard (V1–V8)
# The org-wide review-sheet standard ratified from the h178_da vote's meta-note
# (SanskritLexicography/RussianTranslation/pwg_ru/H178_DA_VOTE_ISSUE_REGISTER_2026-07-19.md §2):
# V1/V5 rating buttons below the card content with approve-coupling, V3 visible
# card ids, V4 clickable card headers, V6 taller note box, V7 highlight style,
# V8 in-sheet sheet_id + save-path banner. All additive string surgery on the
# frozen core template, exactly like the H779 extras layer.

_STANDARD_CSS = '''  .idchip { font-family:ui-monospace,Consolas,monospace; font-size:11px; color:var(--muted);
            background:var(--panel2); border:1px solid var(--border); padding:2px 7px;
            border-radius:6px; user-select:all; }
  .card header { gap:10px; }
  .hw a.hwlink { color:inherit; text-decoration:underline dotted; text-underline-offset:3px; }
  .hw a.hwlink:hover { color:var(--accent); }
  mark.hl { background:#453407; color:#ffd75e; padding:0 2px; border-radius:3px; }
  .savebanner { max-width:980px; margin:10px auto 0; padding:8px 20px; font-size:12.5px; }
  .savebanner code { background:var(--panel2); border:1px solid var(--border); padding:1px 6px; border-radius:5px; }
  .ratingrow { display:flex; align-items:center; gap:6px; margin-top:10px; flex-wrap:wrap; }
  .ratinglabel { font-size:12px; color:var(--muted); margin-right:4px; }
  button.rate { border:1px solid var(--border); background:var(--panel2); color:var(--text);
                width:34px; padding:6px 0; border-radius:6px; cursor:pointer; font-size:13px; }
  button.rate.active { background:var(--accent); border-color:var(--accent); color:#fff; }
  button.rate.active.below { background:var(--defer); border-color:var(--defer); color:#2a1d02; }
  .rate-state { font-size:12px; color:var(--muted); margin-left:4px; }
  .badge-typology { border:1px solid var(--accent); color:var(--text); font-weight:600; }
'''

#: Type scale (H1808). MG, voting the G5 batch1v3 sheet 28-07-2026: "increase
#: fonts by default +150%%". The donor template's sizes were tuned for a dense
#: 2026-07 sheet and inverted the hierarchy — ``.panel pre``, the text actually
#: under judgement, was the SMALLEST type on the page (12px) while uppercase
#: panel labels and chrome took the visual weight. So this layer does two things:
#:
#: 1. routes every size through one ``--fs`` multiplier (default 1.5), which the
#:    A−/A+ control below re-points at runtime — one variable, whole page follows;
#: 2. lifts ``.panel pre`` off the floor (12 -> 13.5 base) so the judged text is
#:    the largest body type on a card, not the smallest.
#:
#: ``!important`` is deliberate, not cargo: the H779 legend and the H1646 anatomy
#: block carry INLINE ``font-size``/``font`` declarations, which a plain class
#: rule cannot outrank. One authoritative scale layer beats chasing each caller.
_FONT_SCALE_CSS = '''  :root { --fs:%(fs)s; }
  header.top h1 { font-size:calc(16px * var(--fs)) !important; }
  header.top .sub { font-size:calc(12px * var(--fs)) !important; }
  .tally, button.dl, button.vote, button.rate, textarea.note, .reject-label-select,
  #strictReviewerWrap, #strictReviewerWrap input { font-size:calc(13px * var(--fs)) !important; }
  .filterbar button, .fsctl button, .fsctl .fsval, .chip, .vote-state, .rate-state,
  .ratinglabel, .rejectlabellabel, footer.hint, div.legend,
  #strictReviewError { font-size:calc(12px * var(--fs)) !important; }
  .card .hw { font-size:calc(18px * var(--fs)) !important; }
  .badge, .panel h4, kbd, .idchip { font-size:calc(11px * var(--fs)) !important; }
  .question { font-size:calc(14px * var(--fs)) !important; }
  .panel { font-size:calc(13px * var(--fs)) !important; }
  .panel pre { font-size:calc(13.5px * var(--fs)) !important; line-height:1.55; }
  .panel .anatomy { font-size:calc(12.5px * var(--fs)) !important; }
  .savebanner { font-size:calc(12.5px * var(--fs)) !important; }
  .fsctl { display:flex; align-items:center; gap:4px; }
  .fsctl button { background:var(--panel2); border:1px solid var(--border); color:var(--text);
                  padding:6px 10px; border-radius:14px; cursor:pointer; line-height:1; }
  .fsctl .fsval { color:var(--muted); min-width:3.4em; text-align:center; }
'''

_FONT_SCALE_HTML = ('<div class="fsctl" title="text size — persists in this browser">'
                    '<button type="button" id="fsDown" aria-label="smaller text">A&minus;</button>'
                    '<span class="fsval" id="fsVal"></span>'
                    '<button type="button" id="fsUp" aria-label="larger text">A+</button></div>\n  ')

_FONT_SCALE_JS = '''
  var FS_KEY = STORE_KEY + ':fs', FS_DEFAULT = %(fs)s;
  function fsGet() {
    var v = parseFloat(localStorage.getItem(FS_KEY));
    return (isFinite(v) && v >= 0.7 && v <= 3) ? v : FS_DEFAULT;
  }
  function fsApply(v) {
    document.documentElement.style.setProperty('--fs', String(v));
    document.getElementById('fsVal').textContent = Math.round(v * 100) + '%%';
  }
  function fsSet(v) {
    v = Math.min(3, Math.max(0.7, Math.round(v * 10) / 10));
    localStorage.setItem(FS_KEY, String(v)); fsApply(v);
  }
  fsApply(fsGet());
  document.getElementById('fsDown').addEventListener('click', function () { fsSet(fsGet() - 0.1); });
  document.getElementById('fsUp').addEventListener('click', function () { fsSet(fsGet() + 0.1); });
'''


def _add_font_scale(doc, scale):
    """Scale layer + the A−/A+ toolbar control. Appended after the core template,
    so _CORE_TEMPLATE (and its byte-identical fixture) stays untouched."""
    doc = doc.replace("</style>", _FONT_SCALE_CSS % {"fs": ("%g" % scale)} + "</style>", 1)
    anchor = '<div class="filterbar"'
    if anchor not in doc:
        raise ValueError("review-sheet filterbar anchor is missing")
    doc = doc.replace(anchor, _FONT_SCALE_HTML + anchor, 1)
    return doc.replace("})();\n</script>",
                       _FONT_SCALE_JS % {"fs": ("%g" % scale)} + "})();\n</script>", 1)


# ----------------------------------------------------------------------------- mobile layer (H2854 step 2)
# Decision 12 (plan): a plain @media block, always-emitted for every
# extras=True sheet, no JS, no opt-out — a curator voting from a phone should
# not need a config flag to get tappable controls. Sizes are left in absolute
# px (not routed through --fs) since ≥44px is a touch-target floor, not a
# type-scale preference.
_MOBILE_CSS = '''  @media (max-width: 640px) {
    header.top { padding: 10px 14px; flex-direction: column; align-items: stretch; }
    header.top h1 { font-size: 15px; }
    .tally { gap: 8px; font-size: 11px; }
    .toolbar { padding: 8px 14px; }
    main { padding: 8px 12px; }
    .card { padding: 12px; }
    .filterbar { flex-wrap: wrap; }
    button.dl, button.vote, button.rate, .fsctl button, #saveBtn, #handinBtn, #pauseBtn {
      min-height: 44px; min-width: 44px; padding: 10px 14px;
    }
    .controls { flex-wrap: wrap; }
    .panel { padding: 8px 10px; }
    textarea.note { min-height: 60px; }
  }
'''


def _add_mobile_css(doc):
    return doc.replace("</style>", _MOBILE_CSS + "</style>", 1)


# ----------------------------------------------------------------------------- H1847 facets
# The core filter bar is ONE dimension, single-select (`data-filt`) — enough for
# a stratum, useless for browsing by a tag vocabulary. The G5 sheet's cards carry
# NWS sense tags in three independent slots (diasystem × domain × position in the
# compound), and the census that measured them (SanskritLexicography
# `src/nws_tag_census.py`, 48,214 senses) ends by noting that a reviewer deciding
# whether a tag is worth a facet needs its counts — i.e. the census's own point
# was to feed a facet bar that did not exist yet.
#
# So: N caller-defined dimensions, multi-select WITHIN a dimension (OR) and
# intersected ACROSS dimensions (AND) — «все ведийские смыслы, стоящие в конце
# сложного слова» is one click each, not a scroll. Additive on the same stable
# anchors as every other layer; a caller that passes no `facets` gets the
# byte-identical pre-H1847 document.
#: Sizes route through the same `--fs` multiplier as the rest of the page — the
#: layer is injected AFTER `_add_font_scale`, so these land later in the cascade
#: and outrank it, which is why they can use `var(--fs)` without `!important`
#: chasing. Keeping them here (not in the always-emitted scale layer) is what
#: makes a facet-less sheet byte-identical to the pre-H1847 document.
_FACET_CSS = '''  .facetbar { max-width:980px; margin:0 auto; padding:4px 20px 0;
              font-size:calc(12px * var(--fs)); }
  .facetrow { display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; margin-bottom:6px; }
  .facetrow .facetlabel { color:var(--muted); min-width:9em; font-size:calc(12px * var(--fs)); }
  .facetbar button { background:var(--panel2); border:1px solid var(--border); color:var(--text);
                     padding:4px 9px; border-radius:14px; cursor:pointer;
                     font-size:calc(12px * var(--fs)); }
  .facetbar button.active { border-color:var(--accent); color:var(--accent); }
  .facetbar button.facetreset { border-style:dashed; }
  .facetcount { color:var(--muted); padding:2px 0 6px; font-size:calc(12px * var(--fs)); }
'''


def _facet_html(facets, count_label, reset_label):
    rows = []
    for dim in facets:
        chips = "".join(
            '<button type="button" data-facet-key="%s" data-facet-val="%s">%s</button>'
            % (esc(dim["key"]), esc(v), esc(l)) for v, l in dim["values"])
        rows.append('<div class="facetrow"><span class="facetlabel">%s</span>%s</div>'
                    % (esc(dim["label"]), chips))
    reset = ('<div class="facetrow"><span class="facetlabel"></span>'
             '<button type="button" class="facetreset" data-facet-reset="1">%s</button>'
             '<span class="facetcount" id="facetcount"></span></div>' % esc(reset_label))
    return ('<div class="facetbar" id="facetbar">\n  %s\n  %s\n</div>\n'
            % ("\n  ".join(rows), reset))


def _facet_js(count_label):
    return '''
  var FACET_COUNT = %s;
  var facetSel = {};
  function facetBaseVisible(card) {
    var bar = document.getElementById('filterbar');
    var act = bar ? bar.querySelector('button.active') : null;
    var f = act ? act.getAttribute('data-filter') : 'all';
    if (f === 'unvoted') { var id = card.getAttribute('data-id'); return !(state[id] && state[id].decision); }
    if (f && f !== 'all') { return card.getAttribute('data-filt') === f; }
    return true;
  }
  function facetCardValues(card) {
    var raw = card.getAttribute('data-facets');
    if (!raw) return {};
    try { return JSON.parse(raw) || {}; } catch (e) { return {}; }
  }
  function facetMatches(card) {
    var have = facetCardValues(card);
    for (var k in facetSel) {
      if (!Object.prototype.hasOwnProperty.call(facetSel, k)) continue;
      var want = facetSel[k];
      if (!want || !want.length) continue;
      var mine = have[k] || [];
      var hit = false;
      for (var i = 0; i < want.length; i++) { if (mine.indexOf(want[i]) !== -1) { hit = true; break; } }
      if (!hit) return false;
    }
    return true;
  }
  function facetApply() {
    var shown = 0;
    document.querySelectorAll('.card').forEach(function (card) {
      var show = facetBaseVisible(card) && facetMatches(card);
      card.style.display = show ? '' : 'none';
      if (show) shown++;
    });
    var out = document.getElementById('facetcount');
    if (out) out.textContent = FACET_COUNT.replace('{shown}', shown).replace('{total}', ids.length);
    activeIdx = 0;
  }
  var facetbar = document.getElementById('facetbar');
  facetbar.addEventListener('click', function (e) {
    var reset = e.target.closest('button[data-facet-reset]');
    if (reset) {
      facetSel = {};
      facetbar.querySelectorAll('button[data-facet-key]').forEach(function (b) { b.classList.remove('active'); });
      facetApply();
      return;
    }
    var btn = e.target.closest('button[data-facet-key]'); if (!btn) return;
    var k = btn.getAttribute('data-facet-key'), v = btn.getAttribute('data-facet-val');
    facetSel[k] = facetSel[k] || [];
    var at = facetSel[k].indexOf(v);
    if (at === -1) { facetSel[k].push(v); btn.classList.add('active'); }
    else { facetSel[k].splice(at, 1); btn.classList.remove('active'); }
    facetApply();
  });
  // The core filter bar writes card.style.display from ONE dimension; this
  // listener is registered later, so it runs after and re-applies the
  // intersection instead of letting the two writers fight.
  document.getElementById('filterbar').addEventListener('click', function () { facetApply(); });
  facetApply();
''' % json.dumps(count_label, ensure_ascii=False)


def _normalize_facets(facets):
    """Validate + normalize the caller's facet dimensions to
    ``[{"key", "label", "values": [(value, label), ...]}]``. ``None`` passes
    through, so the whole layer stays opt-in."""
    if facets is None:
        return None
    if not isinstance(facets, (list, tuple)) or not facets:
        raise ValueError("facets must be a non-empty list of dimensions")
    out, seen = [], set()
    for dim in facets:
        if isinstance(dim, dict):
            key, label, values = dim.get("key"), dim.get("label"), dim.get("values")
        else:
            try:
                key, label, values = dim
            except (TypeError, ValueError):
                raise TypeError("each facet must be a mapping or a (key, label, values) triple")
        if not key:
            raise ValueError("every facet dimension needs a key")
        key = str(key)
        if key in seen:
            raise ValueError("facet keys must be unique; %r repeats" % key)
        seen.add(key)
        if not values:
            raise ValueError("facet %r must list at least one value" % key)
        pairs, vseen = [], set()
        for v in values:
            if isinstance(v, (list, tuple)):
                val, vlabel = (list(v) + [None])[:2]
            else:
                val, vlabel = v, None
            val = str(val)
            if val in vseen:
                raise ValueError("facet %r values must be unique; %r repeats" % (key, val))
            vseen.add(val)
            pairs.append((val, str(vlabel) if vlabel is not None else val))
        out.append({"key": key, "label": str(label if label is not None else key),
                    "values": pairs})
    return out


def _add_facets(doc, facets, count_label, reset_label):
    doc = doc.replace("</style>", _FACET_CSS + "</style>", 1)
    anchor = '<main id="cards">'
    if anchor not in doc:
        raise ValueError("review-sheet cards anchor is missing")
    doc = doc.replace(anchor, _facet_html(facets, count_label, reset_label) + anchor, 1)
    return doc.replace("})();\n</script>", _facet_js(count_label) + "})();\n</script>", 1)


def _add_extra_css(doc, css):
    """Caller-supplied CSS, last in the cascade. Its absence is why
    csl-atlas's cdsl_anatomy had to inline every colour (H1646)."""
    return doc.replace("</style>", "  /* caller css */\n" + css.rstrip() + "\n</style>", 1)


_RATING_ITEM_OLD = "{ id: id, decision: rec.decision || null, note: rec.note || '' }"
_RATING_ITEM_NEW = ("{ id: id, decision: rec.decision || null, note: rec.note || '', "
                    "rating: (rec.rating == null ? null : rec.rating) }")


def _rating_js(rating):
    return '''
  var RATING = %s;
  function ratingCardById(id) {
    var found = null;
    document.querySelectorAll('.card').forEach(function (c) { if (c.getAttribute('data-id') === id) found = c; });
    return found;
  }
  function applyRatingUI(card) {
    var id = card.getAttribute('data-id'); var rec = state[id] || {};
    var v = (rec.rating == null ? null : rec.rating);
    card.querySelectorAll('button.rate').forEach(function (b) {
      var bv = parseInt(b.getAttribute('data-rate'), 10);
      b.classList.toggle('active', v !== null && bv === v);
      b.classList.toggle('below', v !== null && bv === v && v < RATING.threshold);
    });
    var st = card.querySelector('.rate-state');
    if (st) st.textContent = (v === null ? 'unrated'
      : RATING.label + ' ' + v + '/' + RATING.scale + (v < RATING.threshold ? ' — below approval threshold (' + RATING.threshold + ')' : ''));
  }
  function setRating(id, v) { state[id] = state[id] || {}; state[id].rating = v; save(); }
  document.querySelectorAll('.card').forEach(function (card) {
    var id = card.getAttribute('data-id');
    card.querySelectorAll('button.rate').forEach(function (btn) {
      btn.addEventListener('click', function () { setRating(id, parseInt(btn.getAttribute('data-rate'), 10)); applyRatingUI(card); });
    });
    applyRatingUI(card);
  });
  var _ratingOrigVote = vote;
  vote = function (id, d) {
    _ratingOrigVote(id, d);
    if (d === 'approve') {
      var rec = state[id] || {};
      if (rec.rating == null || rec.rating < RATING.approveMin) { state[id].rating = RATING.approveMin; save(); }
      var card = ratingCardById(id); if (card) applyRatingUI(card);
    }
  };
''' % json.dumps(rating)


# ----------------------------------------------------------------------------- H1802 reject-label picker
# The G6 MQM vote (H1796) showed 5/6 rejects failing to put the correct typology
# label as the first word of the free-text note — an unenforceable prose
# convention. This adds a config-driven required single-select control that
# replaces the convention with an actual field, additive on the same stable
# anchors as rating/standard, so a caller that passes nothing gets the
# byte-identical pre-H1802 document.
_REJECT_LABEL_ITEM_OLD = "{ id: id, decision: rec.decision || null, note: rec.note || '' }"
_REJECT_LABEL_ITEM_NEW = ("{ id: id, decision: rec.decision || null, note: rec.note || '', "
                          "reject_label: rec.reject_label || null }")
_REJECT_LABEL_ITEM_WITH_RATING_OLD = _RATING_ITEM_NEW
_REJECT_LABEL_ITEM_WITH_RATING_NEW = (
    _RATING_ITEM_NEW[:-2] + ", reject_label: rec.reject_label || null }")


def _reject_label_js(reject_labels):
    return '''
  var REJECT_LABELS = %s;
  function applyRejectLabelUI(card) {
    var row = card.querySelector('.rejectlabelrow'); if (!row) return;
    var id = card.getAttribute('data-id'); var rec = state[id] || {};
    row.style.display = rec.decision === 'reject' ? '' : 'none';
    var sel = row.querySelector('select'); if (sel) sel.value = rec.reject_label || '';
  }
  function setRejectLabel(id, v) { state[id] = state[id] || {}; state[id].reject_label = v || null; save(); }
  document.querySelectorAll('.card').forEach(function (card) {
    var id = card.getAttribute('data-id');
    var sel = card.querySelector('.rejectlabelrow select');
    if (sel) sel.addEventListener('change', function () { setRejectLabel(id, sel.value); applyRejectLabelUI(card); });
    applyRejectLabelUI(card);
  });
  var _origApplyCardUI = applyCardUI;
  applyCardUI = function (card) { _origApplyCardUI(card); applyRejectLabelUI(card); };
''' % json.dumps(reject_labels)


def _add_reject_labels(doc, reject_labels, *, strict=False):
    """Additive string surgery: item literals gain a ``reject_label`` field
    (wherever the shared literal currently appears — plain export, autosave
    export, and, when present, the strict-review item constructor); the
    strict-review completion gate additionally refuses a labelless reject the
    same way it already refuses a noteless one."""
    doc = doc.replace(_REJECT_LABEL_ITEM_OLD, _REJECT_LABEL_ITEM_NEW)
    doc = doc.replace(_REJECT_LABEL_ITEM_WITH_RATING_OLD, _REJECT_LABEL_ITEM_WITH_RATING_NEW)
    doc = doc.replace("})();\n</script>", _reject_label_js(reject_labels) + "})();\n</script>", 1)
    if strict:
        anchor = ("    if (rejectedWithoutNote.length) errors.push(rejectedWithoutNote.length"
                  " + ' rejection(s) need a note');\n")
        if anchor not in doc:
            raise ValueError("review-sheet strict-review anchor is missing")
        addition = (
            "    var rejectedWithoutLabel = STRICT_REVIEW.requireRejectNote ? items.filter(function (item) {\n"
            "      return item.decision === 'reject' && !item.reject_label;\n"
            "    }) : [];\n"
            "    if (rejectedWithoutLabel.length) errors.push(rejectedWithoutLabel.length"
            " + ' rejection(s) need a label');\n"
        )
        doc = doc.replace(anchor, anchor + addition, 1)
    return doc


# ----------------------------------------------------------------------------- V11 timing (H2840)
# MG, voting the BookIndex crosswalk gate 15-08-2026: «Нужно засекать внутри
# страницы сколько времени я трачу на страницу целиком и на каждый пункт по
# отдельности, тут и в остальных голосованиях.» So the sheet itself measures
# ACTIVE time (tab visible, machine awake) — total for the page and attributed
# per card — and ships both inside the decisions export, where the apply
# pipeline and later effort-calibration (the 🟢/🟡/🔴 «Труд» traffic light on
# the vote hub is currently a guess) can read real numbers instead.
#
# Mechanics: a 1 s tick accumulates wall time while the document is visible; a
# tick longer than 4 s means the tab was hidden or the machine slept and is
# discarded, never attributed. Each tick's second goes to the card whose visible
# area is closest to the viewport's vertical centre — the card being read — so
# skimming past N cards costs each of them only the seconds they actually held
# the centre. Totals persist in localStorage next to the votes (surviving
# reload/resume, like the votes themselves) and export as integer seconds:
# top-level ``time_total_seconds``, per item ``time_seconds``. Additive string
# surgery on the same stable anchors as every other layer; ``extras=False``
# (donor fixture) never gets it, and ``config["timing"] = False`` opts a sheet
# out.
_TIMING_CSS = '''  .tally .time { color:var(--muted); }
'''

_TIMING_HTML = ('<span class="time" title="active time on this sheet (while the tab is visible)">'
                '&#9201; <span class="count" id="t-total">0:00</span></span>\n    ')

_TIMING_JS = '''
  var TIME_KEY = STORE_KEY + ':timing';
  var __timing = { total: 0, per: {} };
  try {
    var __t0 = JSON.parse(localStorage.getItem(TIME_KEY) || 'null');
    if (__t0 && typeof __t0.total === 'number') __timing = __t0;
  } catch (e) {}
  if (!__timing.per) __timing.per = {};
  function __timeFor(id) { return Math.round(__timing.per[id] || 0); }
  function __timeTotal() { return Math.round(__timing.total || 0); }
  function __timeFmt(s) {
    s = Math.round(s); var m = Math.floor(s / 60);
    return (m >= 60 ? Math.floor(m / 60) + ':' + ('0' + (m - Math.floor(m / 60) * 60)).slice(-2) : m)
      + ':' + ('0' + (s - m * 60)).slice(-2);
  }
  function __timeShow() {
    var el = document.getElementById('t-total');
    if (el) el.textContent = __timeFmt(__timing.total);
  }
  var __timeLast = Date.now(), __timeDirty = 0;
  var __timeCards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  function __timeActiveId() {
    var mid = window.innerHeight / 2, best = null, bestd = Infinity;
    for (var i = 0; i < __timeCards.length; i++) {
      var c = __timeCards[i];
      if (c.style.display === 'none') continue;
      var r = c.getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) continue;
      var center = (Math.max(r.top, 0) + Math.min(r.bottom, window.innerHeight)) / 2;
      var d = Math.abs(center - mid);
      if (d < bestd) { bestd = d; best = c; }
    }
    return best ? best.getAttribute('data-id') : null;
  }
  function __timeFlush() {
    try { localStorage.setItem(TIME_KEY, JSON.stringify(__timing)); } catch (e) {}
  }
  // V12 (H2858): the clock is stoppable. `paused` rides in the same persisted
  // record as the totals, so a reviewer who pauses and closes the tab does not
  // come back to a clock that ran all night.
  var __timePaused = !!__timing.paused;
  function __timePauseSet(v) {
    __timePaused = !!v; __timing.paused = __timePaused; __timeLast = Date.now(); __timeFlush();
  }
  setInterval(function () {
    var now = Date.now(), dt = (now - __timeLast) / 1000;
    __timeLast = now;
    if (document.hidden || __timePaused || dt <= 0 || dt > 4) return;
    __timing.total += dt;
    var id = __timeActiveId();
    if (id) __timing.per[id] = (__timing.per[id] || 0) + dt;
    __timeDirty += dt;
    if (__timeDirty >= 5) { __timeDirty = 0; __timeFlush(); }
    __timeShow();
  }, 1000);
  document.addEventListener('visibilitychange', function () { __timeLast = Date.now(); });
  window.addEventListener('beforeunload', __timeFlush);
  __timeShow();
'''

_TIMING_ITEM_OLD = "note: rec.note || ''"
_TIMING_ITEM_NEW = "note: rec.note || '', time_seconds: __timeFor(id)"
_TIMING_PAYLOAD_OLD = "decided: decided,"
_TIMING_PAYLOAD_NEW = "decided: decided, time_total_seconds: __timeTotal(),"


def _add_timing(doc):
    """V11 — active-time metering, applied LAST so the item-literal surgery
    catches every variant the earlier layers (rating, reject_label, strict)
    already produced around the shared ``note`` field."""
    doc = doc.replace("</style>", _TIMING_CSS + "</style>", 1)
    tally_anchor = '<span class="unvoted">'
    if tally_anchor not in doc:
        raise ValueError("review-sheet tally anchor is missing")
    doc = doc.replace(tally_anchor, _TIMING_HTML + tally_anchor, 1)
    doc = doc.replace(_TIMING_ITEM_OLD, _TIMING_ITEM_NEW)
    doc = doc.replace(_TIMING_PAYLOAD_OLD, _TIMING_PAYLOAD_NEW)
    return doc.replace("})();\n</script>", _TIMING_JS + "})();\n</script>", 1)


# ----------------------------------------------------------------------------- V12 hand-in (H2858)
# MG, after one sitting on the BookIndex crosswalk gate (15-08-2026, 30 ✅ / 14 ❌
# of 255, 14 min): «Хочу поставить на паузу, остановить таймер и остановить
# работу, сдать то что было. Но такой функции как сдать сколько успел нет — а
# она нужна.» Mechanically the plain download button always exported partial
# work (unvoted items carry `decision: null`), but nothing in the sheet SAID so:
# a button labelled "Download decisions.json" reads as the finish line, and in a
# strict sheet it is one — the strict handler refuses to export until every card
# is voted. So a reviewer who runs out of time has no sanctioned way to stop.
#
# V12 gives that stop two controls:
#
# * ⏸ next to the ⏱ chip — freezes the V11 clock, so a pause is not billed as
#   review time. The paused flag persists with the totals.
# * "Hand in what I got" — flushes the notes, stops the clock, and exports the
#   same decisions payload marked `partial: true` with `undecided: N`, under a
#   `_decisions_partial.json` filename so it cannot be mistaken for a finished
#   sheet. It deliberately BYPASSES the strict all-votes gate (that gate exists
#   to stop a sheet being *closed* half-done, not to trap a reviewer's work in a
#   browser) while still carrying `complete: false` and the reviewer id.
#
# Nothing is dropped: the votes stay in localStorage, so the sitting can resume,
# and the applier is already partial-safe — a `null` decision is never applied.
_HANDIN_CSS = '''  .dl.handin { background:#243447; }
  .tally .pausebtn { background:none; border:1px solid var(--border); color:var(--muted);
                     border-radius:6px; padding:0 6px; margin-left:4px; cursor:pointer;
                     font-size:inherit; font-family:inherit; line-height:1.6; }
  .tally .pausebtn.on { color:#ffd479; border-color:#ffd479; }
  .tally .time.paused { opacity:.45; }
  .handin-said { color:var(--muted); font-size:12px; margin-left:10px; }
'''

_HANDIN_BUTTON = ('<button class="dl handin" id="handinBtn" title="stop the clock and export '
                  'the votes made so far; the rest stay saved in this browser">'
                  'Hand in what I got</button>'
                  '<span class="handin-said" id="handinSaid"></span>')

_PAUSE_BUTTON = ('<button type="button" class="pausebtn" id="pauseBtn" '
                 'title="pause the clock — a break is not review time">&#9208;</button>\n    ')

def _handin_js(*, timing, rating_on, reject_labels_on, strict_on):
    """The hand-in controller, emitted for exactly the layers this sheet has.

    Deliberately NOT written with `typeof RATING`/`typeof __timeTotal` guards:
    the emitter already knows which layers are on, and a guard would put those
    identifiers into every document — including the ones whose contract is that
    the identifier is absent (`test_timing_opt_out`,
    `test_reject_labels_absent_leaves_behaviour_unchanged`). Knowing at build
    time keeps each sheet's script to what that sheet actually has.

    The item is assembled by assignment rather than as one object literal, so it
    never contains V11's `note: rec.note || ''` surgery target — this layer
    instruments its own `time_seconds` and must not be rewritten a second time
    whichever order the layers run in.
    """
    pause = '''
  var __pauseBtn = document.getElementById('pauseBtn');
  function __pauseShow() {
    __pauseBtn.classList.toggle('on', __timePaused);
    __pauseBtn.innerHTML = __timePaused ? '&#9654;' : '&#9208;';
    var chip = document.querySelector('.tally .time');
    if (chip) chip.classList.toggle('paused', __timePaused);
  }
  __pauseBtn.addEventListener('click', function () { __timePauseSet(!__timePaused); __pauseShow(); });
  __pauseShow();
''' if timing else ""
    stop_clock = "    __timePauseSet(true); __pauseShow();\n" if timing else ""
    per_item = "      item.time_seconds = __timeFor(id);\n" if timing else ""
    if rating_on:
        per_item += "      item.rating = (rec.rating == null ? null : rec.rating);\n"
    if reject_labels_on:
        per_item += "      item.reject_label = rec.reject_label || null;\n"
    total = "    payload.time_total_seconds = __timeTotal();\n" if timing else ""
    reviewer = "    payload.reviewer = strictReviewer.value.trim();\n" if strict_on else ""
    return '''
  var HANDIN_SAID = 'handed in {n} of {total} — clock stopped, the rest stay saved in this browser';
  var __handinBtn = document.getElementById('handinBtn');
  var __handinSaid = document.getElementById('handinSaid');
''' + pause + '''  __handinBtn.addEventListener('click', function () {
    ids.forEach(function (id) { syncNoteFromDom(id); });
''' + stop_clock + '''    var items = ids.map(function (id) {
      var rec = state[id] || {};
      var item = { id: id, decision: rec.decision || null };
      item.note = rec.note || '';
''' + per_item + '''      return item;
    });
    var decided = items.filter(function (it) { return !!it.decision; }).length;
    var payload = { sheet_id: SHEET_ID, generated: GENERATED, decided: decided,
      partial: true, complete: false, undecided: items.length - decided, items: items };
''' + total + reviewer + '''    var blob = new Blob([JSON.stringify(payload, null, 2)], { type:'application/json' });
    var url = URL.createObjectURL(blob); var a = document.createElement('a');
    a.href = url; a.download = SHEET_ID + '_decisions_partial.json';
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
    __handinSaid.textContent = HANDIN_SAID.replace('{n}', decided).replace('{total}', items.length);
  });
'''


def _add_handin(doc, generated_json, *, timing, rating_on, reject_labels_on, strict_on):
    """V12 — the partial hand-in + clock pause. Applied after V11, so the pause
    control can drive the clock that layer installed; with ``timing=False`` the
    pause control is not emitted at all (there is nothing to pause) and the
    hand-in button still exports."""
    doc = doc.replace("</style>", _HANDIN_CSS + "</style>", 1)
    dl_anchor = '<button class="dl" id="downloadBtn">Download decisions.json</button>'
    if dl_anchor not in doc:
        raise ValueError("review-sheet download button anchor is missing")
    doc = doc.replace(dl_anchor, dl_anchor + _HANDIN_BUTTON, 1)
    if timing:
        tally_anchor = '<span class="unvoted">'
        if tally_anchor not in doc:
            raise ValueError("review-sheet tally anchor is missing")
        doc = doc.replace(tally_anchor, _PAUSE_BUTTON + tally_anchor, 1)
    # The core download handler builds its payload from a literal `generated`; the
    # hand-in handler needs the same value, so bind it once as a named constant.
    gen_anchor = "  var STORE_KEY = 'review-sheet:' + SHEET_ID;"
    if gen_anchor not in doc:
        raise ValueError("review-sheet store-key anchor is missing")
    doc = doc.replace(gen_anchor, gen_anchor + "\n  var GENERATED = " + generated_json + ";", 1)
    js = _handin_js(timing=timing, rating_on=rating_on,
                    reject_labels_on=reject_labels_on, strict_on=strict_on)
    return doc.replace("})();\n</script>", js + "})();\n</script>", 1)


# ----------------------------------------------------------------------------- V15 session flow (H2887)
# MG, curating the private sheet 16-08-2026: «Когда я сохраняю решения, таймер
# должен останавливаться. Сейчас этого не происходит. Как ещё оптимизировать
# опыт голосования?» Reading the code rather than the symptom found TWO defects,
# the second heavier than the reported one:
#
# 1. **The clock does not stop on export.** V12 (H2858) wrote `__timePauseSet(true)`
#    into the `handinBtn` handler ONLY. The main `downloadBtn` (plain and under
#    `strict_review`) and the `saveBtn` file-picker leave the clock running, so the
#    semantics are inside out: the PARTIAL exit stops the clock, the FULL one does not.
# 2. **Silent misvote — vote-data corruption.** `a`/`r`/`d` target `vis[activeIdx]`,
#    and `activeIdx` moved on ARROW KEYS ONLY: there was no scroll handler and no
#    focus ring. Scroll to card 40 with the mouse, press `a`, and the vote lands on
#    whatever card the arrows last pointed at, off-screen, with no warning — while
#    V11's clock bills the time to the card at the viewport centre (`__timeActiveId()`).
#    Two layers disagreeing about "the current card" is how a vote silently lands on
#    the wrong row.
#
# V15 is the opt-out layer that fixes both and adds the rhythm the same interview
# asked for (12 forks, `/ask` 16-08-2026): one "current card" shared by the clock and
# the keys, a visible ring on it, a pause STATE (running | manual | export | idle)
# instead of a bare boolean, auto-rearm on any sign of continued voting, a 90 s idle
# auto-pause, auto-advance to the next undecided card, undo, a progress bar with a
# median-based ETA, and resume-at-the-first-undecided on load.
#
# Named **V15**, not the plan's "V14": V14 shipped the same day as the export-context
# layer, so this build takes the next free slot per the plan's ambiguity contract
# (take the default, log it) rather than colliding with a released feature — exactly
# what H2854 did when the plan's "V12" was already taken by H2858.
#
# Two constraints this layer is written around, both already paid for by H2858:
#
# * **Never probe a neighbouring layer with `typeof`.** The emitter knows at build
#   time which layers are on; `test_timing_opt_out` / `test_handin_survives_timing_off`
#   assert the ABSENCE of those identifiers from the document. So every clock-touching
#   line here is emitted only when `config["timing"]` is on, and every `__pauseShow()`
#   call only when `config["hand_in"]` is on too (that is the layer that defines it).
# * **Never repeat the shared `note: rec.note || ''` literal**, which `_add_timing`
#   rewrites wherever it finds it. This layer produces no export payload at all, so
#   it carries neither that literal nor `sheet_id: SHEET_ID,` (V14's replace-all target).
#
# One logged default the interview did not decide: the implementation layer says
# "autosave is an export too", but the debounced autosave writes after EVERY vote
# once a file handle is armed — pausing the clock there would leave it frozen for
# the whole sitting, one second after each vote. So the clock stops on the export
# GESTURES (Download / Save to folder… / Hand in what I got) and not on the
# background autosave writes those gestures schedule.
_FLOW_IDLE_SECONDS = 90

_FLOW_CSS = '''  .card.kbd-active { outline:2px solid var(--accent); outline-offset:3px; }
  .tally .tstate { color:var(--muted); font-size:.85em; margin-left:4px; }
  .tally .tstate.idle { color:var(--defer); }
  .flowprog { display:inline-flex; align-items:center; gap:8px; color:var(--muted); font-size:12px; }
  .flowprog .bar { display:inline-block; width:120px; height:6px; border-radius:3px;
                   background:var(--panel2); border:1px solid var(--border); overflow:hidden; }
  .flowprog .bar i { display:block; height:6px; background:var(--accent); width:0; }
  .dl.flowundo { background:#243447; }
  .flowtoast { position:fixed; left:50%; bottom:24px; transform:translateX(-50%);
               background:var(--panel2); border:1px solid var(--border); color:var(--text);
               padding:8px 14px; border-radius:8px; font-size:13px; z-index:50;
               opacity:0; pointer-events:none; transition:opacity .18s; }
  .flowtoast.on { opacity:1; }
'''

_FLOW_HTML = ('<button type="button" class="dl flowundo" id="flowUndoBtn" '
              'title="undo the last decision (z)">&#8630; Undo</button>\n  '
              '<span class="flowprog" id="flowProg">'
              '<span class="bar"><i id="flowBar"></i></span>'
              '<span id="flowProgText"></span><span id="flowEta"></span></span>\n  ')

_FLOW_TOAST_HTML = '<div class="flowtoast" id="flowToast" role="status"></div>\n'

#: The clock state machine V15 installs over V12's bare boolean. `pause_reason`
#: rides in the SAME persisted `TIME_KEY` record as `paused`, so it survives a
#: closed tab; a record written before this layer has no reason at all and is
#: read back as **manual** — a curator who paused yesterday must not find the
#: clock has restarted itself overnight.
_FLOW_PAUSE_STATE_OLD = '''  var __timePaused = !!__timing.paused;
  function __timePauseSet(v) {
    __timePaused = !!v; __timing.paused = __timePaused; __timeLast = Date.now(); __timeFlush();
  }
'''
_FLOW_PAUSE_STATE_NEW = '''  var __timePaused = !!__timing.paused;
  // V15 (H2887): a legacy record carries `paused` and no reason — read it as
  // manual, so an auto-rearm can never lift a pause the curator set by hand.
  var __timePauseReason = __timePaused ? (__timing.pause_reason || 'manual') : null;
  function __timePauseSet(v, reason) {
    __timePaused = !!v;
    __timing.paused = __timePaused;
    __timePauseReason = __timePaused ? (reason || 'manual') : null;
    __timing.pause_reason = __timePauseReason;
    __timeLast = Date.now(); __timeFlush();
  }
'''
_FLOW_HANDIN_STOP_OLD = "    __timePauseSet(true); __pauseShow();\n"
_FLOW_HANDIN_STOP_NEW = "    __timePauseSet(true, 'export'); __pauseShow();\n"


def _session_flow_js(*, timing, pause_ui, facets_on):
    """The V15 controller, emitted for exactly the layers this sheet has."""
    pause_show = "    __pauseShow();\n" if pause_ui else ""
    # `facetbar` is named only when that layer is on — a facet-less sheet's
    # contract is that the identifier is absent from the document entirely
    # (test_facets_absent_leaves_document_untouched), the same shape as
    # test_timing_opt_out. Build-time knowledge again, never a runtime probe.
    bar_ids = "'filterbar', 'facetbar'" if facets_on else "'filterbar'"
    if timing:
        center = "  var __flowCenterId = __timeActiveId;\n"
    else:
        # No clock on this sheet, so no `__timeActiveId` to borrow — the same
        # nearest-to-viewport-centre rule, written out once here. Either way the
        # sheet has exactly ONE definition of "the current card".
        center = '''  function __flowCenterId() {
    var mid = window.innerHeight / 2, best = null, bestd = Infinity;
    var vis = visibleCards();
    for (var i = 0; i < vis.length; i++) {
      var r = vis[i].getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) continue;
      var c = (Math.max(r.top, 0) + Math.min(r.bottom, window.innerHeight)) / 2;
      var d = Math.abs(c - mid);
      if (d < bestd) { bestd = d; best = vis[i]; }
    }
    return best ? best.getAttribute('data-id') : null;
  }
'''
    if timing:
        clock = '''  function __flowClockShow() {
    var el = document.getElementById('t-state');
    if (!el) return;
    var label = FLOW_CLOCK_RUNNING;
    if (__timePaused) label = (__timePauseReason === 'idle') ? FLOW_CLOCK_IDLE : FLOW_CLOCK_PAUSED;
    el.textContent = label;
    el.classList.toggle('idle', !!__timePaused && __timePauseReason === 'idle');
  }
''' + ('''  // The V12 ⏸ button drives the clock straight through __timePauseSet, so the
  // three-state label has to ride along with V12's own repaint or it goes stale
  // the moment the curator pauses by hand.
  var __flowOrigPauseShow = __pauseShow;
  __pauseShow = function () { __flowOrigPauseShow(); __flowClockShow(); };
''' if pause_ui else "") + '''  var __flowIdleTimer = null;
  function __flowIdleArm() {
    clearTimeout(__flowIdleTimer);
    __flowIdleTimer = setTimeout(function () {
      if (__timePaused) return;
      __timePauseSet(true, 'idle');
''' + pause_show + '''      __flowClockShow();
    }, FLOW_IDLE_SECONDS * 1000);
  }
  function __flowRearm() {
    if (__timePaused && __timePauseReason !== 'manual') {
      __timePauseSet(false);
''' + pause_show + '''    }
    __flowClockShow();
    __flowIdleArm();
  }
  // The export GESTURES, caught in the capture phase on `document` so this runs
  // before any handler bound to the buttons themselves — including the strict
  // layer's, which calls stopImmediatePropagation() on its own element.
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest || !t.closest('#downloadBtn, #saveBtn, #handinBtn')) return;
    __timePauseSet(true, 'export');
''' + pause_show + '''    __flowClockShow();
  }, true);
  ['keydown', 'pointerdown', 'scroll'].forEach(function (evt) {
    document.addEventListener(evt, function () { __flowRearm(); }, true);
  });
'''
        eta = '''  function __flowEtaText(decided, total) {
    var secs = [];
    ids.forEach(function (id) {
      if (!(state[id] && state[id].decision)) return;
      var s = __timing.per[id] || 0;
      if (s > 0) secs.push(s);
    });
    if (!secs.length) return '';
    secs.sort(function (a, b) { return a - b; });
    var mid = Math.floor(secs.length / 2);
    var med = (secs.length % 2) ? secs[mid] : (secs[mid - 1] + secs[mid]) / 2;
    var left = Math.max(0, total - decided);
    if (!left) return '';
    var minutes = Math.max(1, Math.round(med * left / 60));
    return (secs.length >= 5 ? FLOW_ETA : FLOW_ETA_ROUGH).replace('{minutes}', minutes);
  }
'''
        eta_call = '''    var etaEl = document.getElementById('flowEta');
    if (etaEl) etaEl.textContent = __flowEtaText(n, total);
'''
        init_clock = "  __flowClockShow();\n  __flowIdleArm();\n"
        clock_strings = ('''  var FLOW_IDLE_SECONDS = ''' + str(_FLOW_IDLE_SECONDS) + ''';
  var FLOW_ETA = 'about {minutes} min left';
  var FLOW_ETA_ROUGH = 'about {minutes} min left (rough)';
  var FLOW_CLOCK_RUNNING = 'running';
  var FLOW_CLOCK_PAUSED = 'paused';
  var FLOW_CLOCK_IDLE = 'idle';
''')
    else:
        clock = "  function __flowRearm() {}\n"
        eta = ""
        eta_call = ""
        init_clock = ""
        # A sheet with no clock has no idle threshold, no ETA and no clock
        # state to name; emitting the constants anyway would put timing chrome
        # into a document whose contract is that it has none.
        clock_strings = ""
    return '''
  // --- V15 session flow (H2887) ---------------------------------------------
''' + clock_strings + '''  var FLOW_PROGRESS = 'decided {n} of {total}';
  var FLOW_UNDO_SAID = 'undo: {id} back to {decision}';
  var FLOW_UNDO_EMPTY = 'nothing to undo';
  var FLOW_UNDO_NONE = 'no decision';
  var FLOW_RESUMED = 'resumed at card {n} of {total}';
  var __flowToast = document.getElementById('flowToast');
  var __flowToastTimer = null;
  function __flowSay(text) {
    if (!__flowToast) return;
    __flowToast.textContent = text;
    __flowToast.classList.add('on');
    clearTimeout(__flowToastTimer);
    __flowToastTimer = setTimeout(function () { __flowToast.classList.remove('on'); }, 2600);
  }
''' + center + '''  function __flowIdxOf(id) {
    var vis = visibleCards();
    for (var i = 0; i < vis.length; i++) {
      if (vis[i].getAttribute('data-id') === id) return i;
    }
    return -1;
  }
  function __flowCardById(id) {
    var found = null;
    cardsEl.forEach(function (c) { if (c.getAttribute('data-id') === id) found = c; });
    return found;
  }
  // The visible ring IS the target of a/r/d — that identity is the whole point
  // of this layer, so nothing may move `activeIdx` without repainting.
  function __flowPaint() {
    cardsEl.forEach(function (c) { c.classList.remove('kbd-active'); });
    var vis = visibleCards();
    if (!vis.length) return;
    if (activeIdx >= vis.length) activeIdx = vis.length - 1;
    if (activeIdx < 0) activeIdx = 0;
    vis[activeIdx].classList.add('kbd-active');
  }
  function __flowSync() {
    var id = __flowCenterId();
    if (id) { var at = __flowIdxOf(id); if (at !== -1) activeIdx = at; }
    __flowPaint();
  }
  var __flowScrollTimer = null;
  window.addEventListener('scroll', function () {
    if (__flowScrollTimer) return;
    __flowScrollTimer = setTimeout(function () { __flowScrollTimer = null; __flowSync(); }, 120);
  });
  // Both bars reset `activeIdx` to 0 as they re-filter; re-derive it from the
  // viewport on the next tick, or defect 2 returns wearing a filter.
  [''' + bar_ids + '''].forEach(function (barId) {
    var bar = document.getElementById(barId);
    if (bar) bar.addEventListener('click', function () { setTimeout(__flowSync, 0); });
  });
''' + clock + '''  var __flowUndoStack = [];
  function __flowUndo() {
    var last = __flowUndoStack.pop();
    if (!last) { __flowSay(FLOW_UNDO_EMPTY); return; }
    state[last.id] = state[last.id] || {};
    if (last.prev) state[last.id].decision = last.prev;
    else delete state[last.id].decision;
    save();
    var card = __flowCardById(last.id);
    if (card) {
      applyCardUI(card);
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      var at = __flowIdxOf(last.id);
      if (at !== -1) activeIdx = at;
      __flowPaint();
    }
    __flowSay(FLOW_UNDO_SAID.replace('{id}', last.id)
      .replace('{decision}', last.prev || FLOW_UNDO_NONE));
  }
  var __flowUndoBtn = document.getElementById('flowUndoBtn');
  if (__flowUndoBtn) __flowUndoBtn.addEventListener('click', __flowUndo);
  function __flowFirstUndecided() {
    var vis = visibleCards();
    for (var i = 0; i < vis.length; i++) {
      var id = vis[i].getAttribute('data-id');
      if (!(state[id] && state[id].decision)) return i;
    }
    return -1;
  }
  function __flowAdvance() {
    var at = __flowFirstUndecided();
    if (at === -1) { __flowPaint(); return; }
    activeIdx = at;
    visibleCards()[at].scrollIntoView({ behavior: 'smooth', block: 'center' });
    __flowPaint();
  }
  function __flowDecided() {
    var n = 0;
    ids.forEach(function (id) { if (state[id] && state[id].decision) n++; });
    return n;
  }
''' + eta + '''  function __flowProgress() {
    var n = __flowDecided(), total = ids.length;
    var txt = document.getElementById('flowProgText');
    if (txt) txt.textContent = FLOW_PROGRESS.replace('{n}', n).replace('{total}', total);
    var bar = document.getElementById('flowBar');
    if (bar) bar.style.width = (total ? Math.round(100 * n / total) : 0) + '%';
''' + eta_call + '''  }
  var __flowOrigTally = tally;
  tally = function () { __flowOrigTally(); __flowProgress(); };
  var __flowOrigVote = vote;
  vote = function (id, d) {
    var rec = state[id] || {};
    __flowUndoStack.push({ id: id, prev: rec.decision || null });
    if (__flowUndoStack.length > 100) __flowUndoStack.shift();
    __flowOrigVote(id, d);
    __flowRearm();
    __flowAdvance();
  };
  var __flowOrigNote = noteChange;
  noteChange = function (id, t) { __flowOrigNote(id, t); __flowRearm(); };
  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'TEXTAREA') return;
    if (e.key === 'z' || e.key === 'Z') { __flowUndo(); e.preventDefault(); return; }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') __flowPaint();
  });
  __flowProgress();
  __flowSync();
''' + init_clock + '''  (function () {
    if (!__flowDecided()) return;
    var at = __flowFirstUndecided();
    if (at === -1) return;
    var vis = visibleCards();
    activeIdx = at;
    vis[at].scrollIntoView({ block: 'center' });
    __flowPaint();
    __flowSay(FLOW_RESUMED.replace('{n}', at + 1).replace('{total}', vis.length));
  })();
'''


def _add_session_flow(doc, *, timing, pause_ui, facets_on):
    """V15 — applied AFTER V11 timing and V12 hand-in (it drives both) and before
    V14 export context (which replace-alls a payload literal this layer never
    contains)."""
    doc = doc.replace("</style>", _FLOW_CSS + "</style>", 1)
    toolbar_anchor = '<div class="filterbar"'
    if toolbar_anchor not in doc:
        raise ValueError("review-sheet filterbar anchor is missing")
    doc = doc.replace(toolbar_anchor, _FLOW_HTML + toolbar_anchor, 1)
    if "</body>" not in doc:
        raise ValueError("review-sheet body anchor is missing")
    doc = doc.replace("</body>", _FLOW_TOAST_HTML + "</body>", 1)
    if timing:
        if _FLOW_PAUSE_STATE_OLD not in doc:
            raise ValueError("review-sheet pause-state anchor is missing")
        doc = doc.replace(_FLOW_PAUSE_STATE_OLD, _FLOW_PAUSE_STATE_NEW, 1)
        state_anchor = '<span class="count" id="t-total">0:00</span></span>'
        if state_anchor not in doc:
            raise ValueError("review-sheet timing chip anchor is missing")
        doc = doc.replace(
            state_anchor,
            '<span class="count" id="t-total">0:00</span>'
            '<span class="tstate" id="t-state"></span></span>', 1)
        # V12 stopped the clock with no reason; under V15 a bare stop means
        # `manual`, which auto-rearm must never lift — so name it.
        doc = doc.replace(_FLOW_HANDIN_STOP_OLD, _FLOW_HANDIN_STOP_NEW, 1)
    js = _session_flow_js(timing=timing, pause_ui=pause_ui, facets_on=facets_on)
    return doc.replace("})();\n</script>", js + "})();\n</script>", 1)


def _add_standard(doc, *, save_as=None, sheet_id=None, note_min_height_px=None, rating=None):
    """Apply the 19-07-2026 standard layers. Each is independent surgery on a
    stable core-template anchor; nothing here touches _CORE_TEMPLATE itself."""
    doc = doc.replace("</style>", _STANDARD_CSS + "</style>", 1)
    if note_min_height_px is not None:
        doc = doc.replace("textarea.note { width:100%; margin-top:10px; min-height:44px;",
                          "textarea.note { width:100%; margin-top:10px; min-height:"
                          + str(int(note_min_height_px)) + "px;", 1)
    if save_as:
        banner_anchor = '<div class="toolbar">'
        banner = ('<div class="savebanner">&#128229; Your export downloads as '
                  "<code>%s_decisions.json</code> &rarr; save it to <code>%s</code> "
                  "(the <code>sheet_id</code> inside the file is <code>%s</code> — that is how a later "
                  "session knows which sheet these decisions belong to).</div>\n"
                  % (esc(sheet_id), esc(save_as), esc(sheet_id)))
        if banner_anchor not in doc:
            raise ValueError("review-sheet toolbar anchor is missing")
        doc = doc.replace(banner_anchor, banner + banner_anchor, 1)
    if rating is not None:
        doc = doc.replace(_RATING_ITEM_OLD, _RATING_ITEM_NEW)
        doc = doc.replace("})();\n</script>", _rating_js(rating) + "})();\n</script>", 1)
    return doc


def _add_extras(doc):
    doc = doc.replace(
        '<button class="dl" id="downloadBtn">Download decisions.json</button>',
        '<button class="dl" id="downloadBtn">Download decisions.json</button>' + _SAVE_BUTTON,
    )
    doc = doc.replace("</footer>\n<script>", "</footer>\n" + _LEGEND_HTML + "<script>")
    doc = doc.replace("})();\n</script>", _AUTOSAVE_JS + "})();\n</script>")
    return doc


#: The emitter's own chrome — the strings a caller cannot reach through `title` /
#: `subtitle` / `footer` / `approve_label` / `reject_label`. Keys are stable
#: identifiers; values are the English defaults as they appear in the rendered doc.
#: A caller passes `config["ui_strings"] = {key: replacement}` to translate them.
#:
#: Added for H1648: csl-atlas's xref sheet is reviewed in Russian, and its card
#: content was fully translated while the toolbar button, keyboard hint, save banner
#: and vote legend stayed English — instructions the reviewer still has to read.
#: Localising by post-processing the emitted HTML in each caller would put the same
#: brittle literals in every repo, so the mapping lives here with the strings.
#: Keys are stable identifiers; each maps to how that chrome is found in the rendered
#: document. A plain string is a literal replaced everywhere it occurs. A compiled
#: pattern must expose a ``body`` group — only that group is replaced, so the
#: surrounding markup (the div, its inline style) survives untouched.
UI_STRINGS = {
    # Toolbar buttons — literal, and `download_button` deliberately also rewrites the
    # quoted mention of the same label inside the footer hint.
    "download_button": "Download decisions.json",
    "save_button": "Save to folder…",
    # Everything after the caller's own `footer` text, up to </footer>: the keyboard
    # legend and the localStorage/export note.
    "footer_hint": re.compile(r"(?P<body>Keyboard:.*?)(?=</footer>)", re.DOTALL),
    # The V8 save-path banner body (present only when `save_as` is passed).
    "save_banner": re.compile(
        r'(?P<pre><div class="savebanner">)(?P<body>.*?)(?P<post></div>)', re.DOTALL),
    # The H779 approve/reject/defer explanation (present only when extras=True).
    "legend": re.compile(
        r'(?P<pre><div class="legend" style="[^"]*">)(?P<body>.*?)(?P<post>\n</div>)', re.DOTALL),
    # Per-card chrome (H1889). Both are emitted by render_card() once per card, so
    # they are the only two visible strings a fully translated sheet could not
    # reach — H1887 hit exactly this and deliberately refused to patch it with
    # per-caller post-processing on the emitted HTML, which is the anti-pattern
    # UI_STRINGS exists to kill. Anchored on the surrounding markup rather than
    # replaced as bare words, because "Defer"/"Reason" also occur in the legend
    # and in caller-supplied card text.
    "defer_button": re.compile(
        r'(?P<pre><button class="vote defer" data-vote="defer">&#9208; )(?P<body>Defer)'
        r'(?P<post></button>)'),
    "reject_reason_label": re.compile(
        r'(?P<pre><span class="rejectlabellabel"[^>]*>)(?P<body>Reason)(?P<post></span>)'),
    # V11 timing chip tooltip (present unless config["timing"] is False).
    "timing_title": re.compile(
        r'(?P<pre><span class="time" title=")'
        r'(?P<body>active time on this sheet \(while the tab is visible\))(?P<post>">)'),
    # V12 hand-in (present unless config["hand_in"] is False): the button label,
    # the two tooltips, and the sentence the sheet says back after a hand-in.
    # That sentence is assembled in JS, so it lives as one template literal with
    # {n}/{total} placeholders — a translation keeps the placeholders and needs
    # no JS of its own.
    "handin_button": "Hand in what I got",
    "handin_title": re.compile(
        r'(?P<pre>id="handinBtn" title=")(?P<body>stop the clock and export the votes made so '
        r'far; the rest stay saved in this browser)(?P<post>">)'),
    "pause_title": re.compile(
        r'(?P<pre>id="pauseBtn" title=")'
        r'(?P<body>pause the clock — a break is not review time)(?P<post>">)'),
    "handin_said": re.compile(
        r"(?P<pre>var HANDIN_SAID = ')(?P<body>[^']*)(?P<post>';)"),
    # V15 session flow (present unless config["session_flow"] is False). The
    # toast/progress/ETA sentences are assembled in JS, so each lives as one
    # single-quoted literal with {n}/{total}/{minutes}/{id}/{decision}
    # placeholders — a translation keeps the placeholders and needs no JS.
    # `flow_eta*` and `flow_clock_*` are emitted only when config["timing"] is
    # on; a sheet without a clock simply never matches those patterns.
    "flow_undo_button": re.compile(
        r'(?P<pre>id="flowUndoBtn" title="[^"]*">&#8630; )(?P<body>Undo)(?P<post></button>)'),
    "flow_undo_title": re.compile(
        r'(?P<pre>id="flowUndoBtn" title=")(?P<body>undo the last decision \(z\))(?P<post>">)'),
    "flow_progress": re.compile(
        r"(?P<pre>var FLOW_PROGRESS = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_eta": re.compile(
        r"(?P<pre>var FLOW_ETA = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_eta_rough": re.compile(
        r"(?P<pre>var FLOW_ETA_ROUGH = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_undo_said": re.compile(
        r"(?P<pre>var FLOW_UNDO_SAID = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_undo_empty": re.compile(
        r"(?P<pre>var FLOW_UNDO_EMPTY = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_undo_none": re.compile(
        r"(?P<pre>var FLOW_UNDO_NONE = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_resumed": re.compile(
        r"(?P<pre>var FLOW_RESUMED = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_clock_running": re.compile(
        r"(?P<pre>var FLOW_CLOCK_RUNNING = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_clock_paused": re.compile(
        r"(?P<pre>var FLOW_CLOCK_PAUSED = ')(?P<body>[^']*)(?P<post>';)"),
    "flow_clock_idle": re.compile(
        r"(?P<pre>var FLOW_CLOCK_IDLE = ')(?P<body>[^']*)(?P<post>';)"),
    # V16 inbox (H2991) — present only when config["github_inbox"] is passed and
    # config["personal_data"] is not True. As with handin_said, the status
    # sentences are assembled in JS, so each is one single-quoted literal whose
    # {n}/{pack}/{url}/{code}/{why} placeholders a translation keeps verbatim.
    "inbox_button": "Save to GitHub",
    "inbox_title": re.compile(
        r'(?P<pre>id="inboxBtn" title=")(?P<body>push this pack\'s ids and verdicts to '
        r'the public vote inbox)(?P<post>">)'),
    # V17 voting ergonomics (present unless config["vote_ux"] is False). Assembled
    # in JS, so each is one single-quoted literal keeping its {n}/{total}/{minutes}
    # placeholders — a translation needs no JS of its own.
    "vote_progress": re.compile(
        r"(?P<pre>var VOTE_PROGRESS = ')(?P<body>[^']*)(?P<post>';)"),
    "vote_eta": re.compile(
        r"(?P<pre>var VOTE_ETA = ')(?P<body>[^']*)(?P<post>';)"),
    "vote_eta_rough": re.compile(
        r"(?P<pre>var VOTE_ETA_ROUGH = ')(?P<body>[^']*)(?P<post>';)"),
    "vote_done": re.compile(
        r"(?P<pre>var VOTE_DONE = ')(?P<body>[^']*)(?P<post>';)"),
    "inbox_pulling": re.compile(
        r"(?P<pre>var INBOX_PULLING = ')(?P<body>[^']*)(?P<post>';)"),
    "inbox_hydrated": re.compile(
        r"(?P<pre>var INBOX_HYDRATED = ')(?P<body>[^']*)(?P<post>';)"),
    "inbox_saved": re.compile(
        r"(?P<pre>var INBOX_SAVED = ')(?P<body>[^']*)(?P<post>';)"),
    "inbox_disabled": re.compile(
        r"(?P<pre>var INBOX_DISABLED = ')(?P<body>[^']*)(?P<post>';)"),
    "inbox_code": re.compile(
        r"(?P<pre>var INBOX_CODE = ')(?P<body>[^']*)(?P<post>';)"),
    "inbox_failed": re.compile(
        r"(?P<pre>var INBOX_FAILED = ')(?P<body>[^']*)(?P<post>';)"),
    # H2847: three bare English chrome words baked straight into
    # _CORE_TEMPLATE's <head>/<header> — never reachable via title/subtitle/
    # footer/approve_label/reject_label, so a fully-translated sheet still
    # showed "N items", "Generated ..." and lang="en" in the browser tab.
    "count_suffix": re.compile(
        r"(?P<pre>\d )(?P<body>items)(?P<post></(?:title|h1)>)"),
    "generated_label": re.compile(
        r'(?P<pre><div class="sub">)(?P<body>Generated)(?P<post> )'),
    "doc_lang": re.compile(
        r'(?P<pre><html lang=")(?P<body>en)(?P<post>">)'),
    "filter_all": re.compile(
        r'(?P<pre><button data-filter="all" class="active">)(?P<body>all)'
        r'(?P<post></button>)'),
    "filter_unvoted": re.compile(
        r'(?P<pre><button data-filter="unvoted">)(?P<body>unvoted only)'
        r'(?P<post></button>)'),
    # 0.22.0 split_layout — present only when config["split_layout"] is True.
    "store_summary": re.compile(
        r'(?P<pre><summary class="store-link">)(?P<body>store markup — quote this in the note)'
        r'(?P<post></summary>)'),
}


#: Ready-made Russian preset (H2854 step 2, decision 8) — enable a whole sheet's
#: chrome with one line, ``config["ui_strings"] = RU_UI_STRINGS`` (merge in
#: overrides with ``RU_UI_STRINGS | {...}``, Python 3.9+, or
#: ``dict(RU_UI_STRINGS, **overrides)``). Covers every ``UI_STRINGS`` key that
#: exists as of this release (12, not the plan's original 8 — H2858 landed the
#: same day and added four V12 hand-in/pause keys the plan predates; the ramp
#: rule this build follows is "translate whatever UI_STRINGS holds now", so a
#: future layer that adds a 13th key is the thing that goes stale, not this one).
#:
#: Deliberately excluded: ``save_banner``. Unlike every other key, its default
#: body is not constant chrome — ``_add_standard`` bakes the caller's actual
#: ``sheet_id``/``save_as`` values into that HTML before ``_localize`` ever
#: runs, so a fixed replacement string would silently drop them rather than
#: translate them. A generator that passes ``config["save_as"]`` under
#: ``RU_UI_STRINGS`` and wants that banner translated too supplies its own
#: ``save_banner`` override built from its actual values:
#: ``RU_UI_STRINGS | {"save_banner": "... %s ..." % (sheet_id, save_as, sheet_id)}``.
#: ``footer_hint``'s a/r/d legend below is the same shape in miniature (the
#: caller's ``approve_label``/``reject_label`` text is baked in too) but is low
#: stakes enough — it is a keyboard-shortcut hint, not a data field a later
#: session parses — that this preset accepts the approximation of translating
#: the shortcut key's ACTION ("одобрить"/"отклонить"/"отложить") rather than
#: echoing back the caller's exact button wording.
RU_UI_STRINGS = {
    "download_button": "Скачать decisions.json",
    "save_button": "Сохранить в папку…",
    "footer_hint": (
        'Клавиши: <kbd>a</kbd> одобрить &middot; <kbd>r</kbd> отклонить &middot; '
        '<kbd>d</kbd> отложить &middot; <kbd>&darr;</kbd>/<kbd>&uarr;</kbd> дальше/назад. '
        'Голоса сохраняются автоматически в localStorage браузера; нажмите '
        '«Скачать decisions.json», когда закончите (непроголосованные пункты '
        'экспортируются с decision:null).'
    ),
    "legend": (
        '<b>Одобрить</b> — принять предложенное изменение/ответ на карточке как есть '
        '(нет отдельного «одобрить как есть» — одобрение значит согласие с написанным). '
        '<b>Отклонить</b> — оставить текущую запись/ответ без изменений. '
        '<b>Отложить</b> — пока не уверен(а), решить позже. Поле заметки — для запроса '
        'частичной правки вместо полного отклонения.'
    ),
    "defer_button": "Отложить",
    "reject_reason_label": "Причина",
    "timing_title": "активное время на этом листе (пока вкладка видима)",
    "handin_button": "Сдать что успел(а)",
    "handin_title": (
        'остановить таймер и экспортировать сделанные голоса; остальное останется '
        'сохранённым в этом браузере'
    ),
    "pause_title": "поставить таймер на паузу — перерыв не считается временем ревью",
    "handin_said": "сдано {n} из {total} — таймер остановлен, остальное сохранено в этом браузере",
    # V15 session flow (H2887). Placeholders are preserved verbatim, as in
    # handin_said. No apostrophes: these land inside single-quoted JS literals.
    "flow_undo_button": "Отменить",
    "flow_undo_title": "отменить последнее решение (z)",
    "flow_progress": "решено {n} из {total}",
    "flow_eta": "осталось ≈{minutes} мин",
    "flow_eta_rough": "осталось ≈{minutes} мин (оценка грубая)",
    "flow_undo_said": "отменено: {id} → {decision}",
    "flow_undo_empty": "отменять нечего",
    "flow_undo_none": "решения не было",
    "flow_resumed": "продолжили с карточки {n} из {total}",
    "flow_clock_running": "идут",
    "flow_clock_paused": "пауза",
    "flow_clock_idle": "простой",
    # V16 inbox (H2991). No apostrophes: these land inside single-quoted JS literals.
    "inbox_button": "Сохранить в GitHub",
    "inbox_title": "отправить id и вердикты этого пакета в публичный ящик голосов",
    # V17 (MG 18-08-2026). Placeholders preserved verbatim.
    "vote_progress": "{n} из {total} по всему листу",
    "vote_eta": "≈{minutes} мин на все {total}",
    "vote_eta_rough": "≈{minutes} мин на все {total} (оценка грубая)",
    "vote_done": "все {total} решены",
    "inbox_pulling": "подтягиваю голоса…",
    "inbox_hydrated": "подтянуто {n} голос(ов) с GitHub",
    "inbox_saved": "пакет {pack} сохранён в GitHub",
    "inbox_disabled": "нет OAuth client_id / релея device-flow — используйте «Скачать decisions.json»",
    "inbox_code": "откройте {url} и введите код {code}",
    "inbox_failed": "сохранить в GitHub не удалось: {why}",
    "count_suffix": "карточек",
    "generated_label": "Собрано",
    "doc_lang": "ru",
    "filter_all": "все",
    "filter_unvoted": "только непроголосованные",
    "store_summary": "разметка store — цитировать в заметке",
}


def _localize(doc, ui_strings):
    """Replace emitter chrome with caller-supplied translations.

    Surgery on the finished document, in the same additive style as `_add_extras` /
    `_add_standard`: a caller that passes nothing gets a byte-identical document, so the
    fixture contract is untouched.

    Unknown keys raise — a silently-ignored typo would ship an English string to a
    reviewer who asked for a translated sheet, which is the exact failure this prevents.
    A key whose chrome is absent from *this* sheet (no `save_as`, `extras=False`) is
    skipped, so one translation table can serve every sheet a repo emits.
    """
    if not ui_strings:
        return doc
    if not isinstance(ui_strings, dict):
        raise TypeError("ui_strings must be a mapping")
    unknown = sorted(set(ui_strings) - set(UI_STRINGS))
    if unknown:
        raise ValueError(
            "unknown ui_strings key(s): %s; known keys: %s"
            % (", ".join(unknown), ", ".join(sorted(UI_STRINGS)))
        )
    for key, replacement in ui_strings.items():
        if not isinstance(replacement, str):
            raise TypeError("ui_strings[%r] must be a string" % key)
        pattern = UI_STRINGS[key]
        if isinstance(pattern, str):
            doc = doc.replace(pattern, replacement)
            continue

        def _swap_body(match, _new=replacement):
            text = match.group(0)
            start, end = match.span("body")
            return text[: start - match.start()] + _new + text[end - match.start():]

        doc = pattern.sub(_swap_body, doc)
    return doc


def _normalize_screening(screening):
    """H1649 — screening block: counts + evidence path + rules applied.

    Required shape (all keys required; counts are non-negative ints)::

        {
          "deterministic": int,   # (a) structure-only checks
          "lookup": int,          # (b) existing dataset resolved the card
          "agent": int,           # (c) agent adjudication with cited evidence
          "human": int,           # (d) still rendered for a human
          "evidence_path": str,   # path/URL of the evidence file
          "rules": list[str],     # short names of rules applied
        }

    Only (d) cards should be in ``items``; the banner states what was taken
    off the reviewer's plate.
    """
    if not isinstance(screening, dict):
        raise TypeError("screening must be a mapping")
    required = ("deterministic", "lookup", "agent", "human", "evidence_path", "rules")
    missing = [k for k in required if k not in screening]
    if missing:
        raise ValueError("screening missing key(s): %s" % ", ".join(missing))
    out = {}
    for k in ("deterministic", "lookup", "agent", "human"):
        v = screening[k]
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise TypeError("screening[%r] must be a non-negative int" % k)
        out[k] = v
    ep = screening["evidence_path"]
    if not isinstance(ep, str) or not ep.strip():
        raise ValueError("screening['evidence_path'] must be a non-empty string")
    out["evidence_path"] = ep.strip()
    rules = screening["rules"]
    if not isinstance(rules, (list, tuple)) or any(not isinstance(r, str) for r in rules):
        raise TypeError("screening['rules'] must be a list of strings")
    out["rules"] = list(rules)
    return out


def _screening_banner_html(screening):
    """Sticky banner above the filter bar stating what screening removed."""
    s = screening
    total_screened = s["deterministic"] + s["lookup"] + s["agent"]
    rules = ", ".join(esc(r) for r in s["rules"]) if s["rules"] else "—"
    return (
        '<aside class="screening-banner" role="status" data-screening="1">'
        "<strong>Screening (H1649)</strong> — only human-required cards are below. "
        "Off the plate: "
        '<span class="sc-a">deterministic %d</span> · '
        '<span class="sc-b">dataset lookup %d</span> · '
        '<span class="sc-c">agent adjudication %d</span> '
        "(total screened %d). "
        "Human cards: <span class=\"sc-d\">%d</span>. "
        'Evidence: <code>%s</code>. Rules: %s.'
        "</aside>"
        % (
            s["deterministic"], s["lookup"], s["agent"], total_screened,
            s["human"], esc(s["evidence_path"]), rules,
        )
    )


_SCREENING_CSS = """
  .screening-banner { margin: 0 20px 12px; padding: 10px 14px; border-radius: 8px;
    border: 1px solid var(--accent); background: #152033; font-size: 12px; line-height: 1.45;
    color: var(--text); max-width: 980px; }
  .screening-banner code { font-size: 11px; color: var(--accent); }
  .screening-banner .sc-d { color: var(--defer); font-weight: 700; }
"""


# ----------------------------------------------------------------------------- H1889 V9/V10
# V1–V8 + H1808 are entirely PRESENTATION. A sheet can be green on every one of
# them and still (a) ask a human to re-derive a conclusion the repo already holds
# on disk, or (b) not be a decision at all. Measured on the sheet that triggered
# this (H1887, 29-07-2026): 191 of 200 cards already had a machine verdict, a
# named rule and cited evidence from the same inputs, none of it rendered; 69 of
# 200 were not disagreements. MG ruled both must BLOCK on write, not warn — the
# H1808 legibility hook warns, and that is why the anatomy defect came back a
# second time.
_V9_NO_MANIFEST = (
    "render_review_sheet(sheet_id=%r) was called with no manifest= (V9, H1889), so "
    "nothing checked whether this sheet asks a human what the repo already answers. "
    "Build a csl_pyutil.evidence.EvidenceManifest, declare_joined() every artifact "
    "keyed on these row ids, declare_omitted()/declare_omitted_path() the rest with a "
    "reason, and pass manifest=. This is a migration ramp for the pre-H1889 "
    "generators, not a permanent posture: it becomes an error in csl-pyutil 1.0.0. "
    "Escalate it today with -W error::csl_pyutil.evidence.PreflightWarning."
)

_PREFLIGHT_KEYS = ("allow_slp1_tokens", "overlap_threshold", "skip_prior_art")


# ----------------------------------------------------------------------------- meta generator (H2854 step 1)
# The vote hub's weekly CI staleness check (gasyoun.github.io) needs a way to
# tell, from a published sheet's HTML alone, which csl-pyutil version rendered
# it — without any repo-side bookkeeping. A <meta name="generator"> tag is the
# standard place static-site tooling already puts this, so the check is a
# one-line string compare against the latest GitHub release tag, no parsing.
# extras=True only: the donor byte-identical path (extras=False) never gets it.
def _add_generator_meta(doc):
    anchor = '<meta name="color-scheme" content="dark">'
    if anchor not in doc:
        raise ValueError("review-sheet color-scheme meta anchor is missing")
    tag = '\n<meta name="generator" content="csl-pyutil/%s">' % __version__
    return doc.replace(anchor, anchor + tag, 1)


# ----------------------------------------------------------------------------- V14 export context (H2707 gate lesson)
# MG, handing in a partial of the BookIndex crosswalk sheet (16-08-2026):
# «почему в скачанном .json нет главного, H2707 для опознания к кому он
# принадлежит?» — a decisions.json that names only its sheet_id forces the
# human (and any later session) to remember which handoff/repo/apply-command
# the file belongs to. config["context"] is a small JSON mapping (recommended
# keys: handoff, repo, apply_with — free-form) that (a) rides verbatim as
# "context" in EVERY export payload — download, autosave, strict, hand-in —
# and (b) is shown in the header next to sheet_id, so both the file and the
# page answer "чей это лист". Additive string surgery on the finished
# document, applied AFTER all payload-producing layers so one replace_all
# covers them; extras=True only — the donor byte-identical path never gets it.
def _add_export_context(doc, context):
    payload_anchor = "sheet_id: SHEET_ID,"
    if payload_anchor not in doc:
        raise ValueError("review-sheet export payload anchor is missing")
    doc = doc.replace(payload_anchor, "sheet_id: SHEET_ID, context: CONTEXT,")
    var_anchor_start = "  var SHEET_ID = "
    i = doc.find(var_anchor_start)
    if i < 0:
        raise ValueError("review-sheet SHEET_ID declaration anchor is missing")
    line_end = doc.index(";\n", i) + 1
    doc = (doc[:line_end]
           + "\n  var CONTEXT = %s;" % json.dumps(context, ensure_ascii=False)
           + doc[line_end:])
    # header shows the same identity the file will carry
    label = esc(" · ".join("%s %s" % (k, v) for k, v in context.items()))
    probe = doc.find("sheet_id <code>")
    if probe >= 0:
        close = doc.index("</code>", probe) + len("</code>")
        doc = doc[:close] + " &middot; <code>%s</code>" % label + doc[close:]
    return doc


# ----------------------------------------------------------------------------- V13 identity gate (H2854 step 2)
# MG, gating the BookIndex crosswalk sheets (H2841/H2842): a card that names an
# internal id (acc001, ch04, …) without also naming the human identity behind
# it lets a reviewer vote on a bare token — the acc001 lesson. V9/V10 already
# gate a sheet's right to exist on evidence-reuse and non-decision share; this
# gate is the same shape (deterministic, PreflightError, PreflightWarning ramp)
# for identity: every internal-id regex match in a card's question must have a
# labels[] entry, and that label text must itself appear in the same question —
# proving the card actually SAYS what the id means, not just holds a mapping
# somewhere the reviewer never sees. Named V13, not the plan's "V12": H2858
# (merged same day) already claimed V12 for the partial hand-in + pause layer,
# so this build defaults to the next free slot per the plan's ambiguity
# contract (decision 14, default+log) rather than colliding with a shipped
# feature.
_V13_NO_IDENTITY_GATE = (
    "render_review_sheet(sheet_id=%r) was called with extras=True and no "
    "config['identity_gate'] (V13, H2854), so nothing checked whether every "
    "internal id a card's question mentions also names its real-world identity "
    "before a reviewer votes (the acc001 lesson, H2841/H2842). Pass "
    "config['identity_gate'] = {'patterns': [regex, ...], 'labels': {match: "
    "label, ...}}. This is a migration ramp for the pre-H2854 generators, not a "
    "permanent posture: it becomes an error in csl-pyutil 1.0.0. Escalate it "
    "today with -W error::csl_pyutil.review_sheet.PreflightWarning."
)

_TAG_STRIP = re.compile(r"<[^>]+>")


def _check_identity(items, gate, sheet_id, extras):
    """V13 — deterministic identity gate, no heuristics.

    ``gate['patterns']`` is a list of regex strings run against each item's
    ``question`` with tags stripped (so markup around an id cannot dodge the
    match). Every distinct match across all patterns must have a
    ``gate['labels'][match]`` entry, and that label's text must itself occur in
    the same stripped question — a mapping the reviewer never sees does not
    count. A match with no label, or a label absent from the question, is a
    ``PreflightError`` finding naming the card id. ``gate=None`` skips the
    check entirely for ``extras=False`` (donor fidelity) and warns for
    ``extras=True`` (the same migration-ramp shape as V9's manifest warning).
    """
    if gate is None:
        if extras:
            warnings.warn(_V13_NO_IDENTITY_GATE % sheet_id,
                          PreflightWarning, stacklevel=3)
        return
    if not isinstance(gate, dict):
        raise TypeError("config['identity_gate'] must be a mapping")
    patterns = gate.get("patterns")
    labels = gate.get("labels")
    if not patterns:
        raise ValueError(
            "config['identity_gate']['patterns'] must be a non-empty list of regex strings")
    if not isinstance(labels, dict):
        raise TypeError("config['identity_gate']['labels'] must be a mapping")
    compiled = [re.compile(p) for p in patterns]
    findings = []
    for it in items:
        text = _TAG_STRIP.sub(" ", it.get("question") or "")
        matched = set()
        for rx in compiled:
            matched.update(m.group(0) for m in rx.finditer(text))
        for match in sorted(matched):
            label = labels.get(match)
            if label is None:
                findings.append(
                    "%s: internal id %r matched in the question but has no "
                    "config['identity_gate']['labels'] entry" % (it.get("id"), match))
            elif label not in text:
                findings.append(
                    "%s: internal id %r maps to label %r, but that label text "
                    "does not appear in the card's question"
                    % (it.get("id"), match, label))
    if findings:
        raise PreflightError(findings)


def _check_non_decisions(items, threshold):
    """V10 — a sheet that is mostly non-decisions must not be written.

    The CALLER supplies the classifier (only it knows its domain) by setting
    ``item["machine_resolvable"] = True`` on every card its own pre-filter already
    resolved; the emitter only enforces the threshold. The default is 0.0 — a
    machine-resolvable card has no business on a human's plate at all — and a
    caller who genuinely wants slack passes a fraction.
    """
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise TypeError("non_decision_share must be a number in 0..1")
    threshold = float(threshold)
    if not (0.0 <= threshold <= 1.0):
        raise ValueError("non_decision_share must lie within 0..1")
    flagged = [str(it["id"]) for it in items if it.get("machine_resolvable")]
    if not items or not flagged:
        return
    share = len(flagged) / float(len(items))
    if share > threshold:
        raise PreflightError([
            "NON-DECISIONS: %d of %d card(s) (%.1f%%) are flagged machine_resolvable by "
            "the caller's own pre-filter, over the %.1f%% allowed by "
            "config['non_decision_share'] (e.g. %s). Resolve them in the pipeline and "
            "render only what still needs a human — the screening block is where the "
            "resolved ones get reported."
            % (len(flagged), len(items), 100 * share, 100 * threshold,
               ", ".join(flagged[:5]))
        ])


def _check_typology_stats(items):
    """U7 (H2846) — a typology / classification label rendered on a card must
    carry, beside the label, its count on this card AND its share of the
    whole population the sheet draws from. The v2 re-glue card asked a
    reviewer to approve a typology whose distribution was invisible on the
    card (1,534 restatements / 250 additions / 1 correction measured but not
    shown — a reviewer reading only chips over-weights the rare class). A
    generator opts in per item via ``item["typology"] = [{"label", "n",
    "share"}, ...]``; ``share`` may be omitted only when the entry sets
    ``"share_unknown": True`` — silence is never permitted. Items with no
    ``typology`` key are unaffected (additive, like V10/V13)."""
    findings = []
    for it in items:
        entries = it.get("typology")
        if not entries:
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                findings.append("%s: typology entries must be mappings" % it.get("id"))
                continue
            label = entry.get("label")
            if not label:
                findings.append("%s: typology entry missing 'label'" % it.get("id"))
                label = "<unlabeled>"
            if entry.get("n") is None:
                findings.append("%s: typology label %r missing count n=" % (it.get("id"), label))
            if entry.get("share") is None and not entry.get("share_unknown"):
                findings.append(
                    "%s: typology label %r missing share= (pass share_unknown=True if the "
                    "population share is genuinely unknown — silence is not permitted)"
                    % (it.get("id"), label))
    if findings:
        raise PreflightError(findings)


def _evidence_gate(doc, manifest, config, extras):
    """V9 — run the H1887 preflight against the FINISHED document and raise before
    a single byte reaches the caller. Absent manifest: warn loudly with the reason."""
    opts = config.get("preflight") or {}
    if not isinstance(opts, dict):
        raise TypeError("config['preflight'] must be a mapping")
    unknown = sorted(set(opts) - set(_PREFLIGHT_KEYS))
    if unknown:
        raise ValueError("unknown config['preflight'] key(s): %s; known keys: %s"
                         % (", ".join(unknown), ", ".join(_PREFLIGHT_KEYS)))
    if manifest is None:
        if extras:
            warnings.warn(_V9_NO_MANIFEST % config.get("sheet_id"),
                          PreflightWarning, stacklevel=3)
        return doc
    preflight(manifest, doc,
              allow_slp1_tokens=tuple(opts.get("allow_slp1_tokens", ())),
              overlap_threshold=float(opts.get("overlap_threshold", 0.5)),
              skip_prior_art=bool(opts.get("skip_prior_art", False)))
    return doc



# ----------------------------------------------------------------------------- V17 voting ergonomics (MG 18-08-2026)
# Reported after a real sitting on pack 1 of the 320-card gold set. Every item is
# about where the reviewer's eye already is:
#
#   * the submit controls lived in the HEADER, above the cards — the reviewer
#     finishes at the BOTTOM and had to scroll back up to hand in;
#   * V15's progress bar was a 120px chip in that same toolbar, easy to miss;
#   * the ETA described the current PAGE. On a 32-pack sheet the reviewer's real
#     question is how long the WHOLE instrument will take at the pace they are
#     going — and because every pack shares one localStorage record AND one
#     timing record, that is answerable from this page without loading another;
#   * auto-advance scrolled the next card to the viewport CENTRE, leaving the top
#     of the card under judgement off the top of the screen.
#
# The controls are selected STRUCTURALLY (everything in the toolbar that is not
# navigation) rather than by a list of ids. An id list would name `inboxBtn`,
# `flowUndoBtn` and friends in every document, breaking the absence contracts
# that V12/V15/V16 each rely on — "opt out and not one identifier remains".
_V17_CSS = '''  .voteprog { flex:1 0 100%; order:99; background:var(--panel);
              border-top:1px solid var(--border); margin:6px -20px -14px; padding:8px 20px;
              display:flex; align-items:center; gap:12px; font-size:12px; color:var(--muted); }
  .voteprog .bar { flex:1 1 auto; height:8px; border-radius:4px; background:var(--panel2);
                   border:1px solid var(--border); overflow:hidden; }
  .voteprog .bar i { display:block; height:100%; width:0; background:var(--ok); transition:width .2s; }
  .voteprog b { color:var(--text); font-weight:700; }
  .voteprog .eta { white-space:nowrap; }
  .votebar { position:sticky; bottom:0; z-index:9; background:var(--panel);
             border-top:1px solid var(--border); padding:10px 20px; margin-top:24px;
             display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
  .votebar .spacer { flex:1 1 auto; }
  .card { scroll-margin-top:96px; }
  @media (max-width: 640px) { .voteprog { padding:6px 12px; } .votebar { padding:8px 12px; } }
'''

_V17_PROGRESS_HTML = ('<div class="voteprog" id="voteProg">'
                      '<span id="voteProgText"></span>'
                      '<span class="bar"><i id="voteProgBar"></i></span>'
                      '<span class="eta" id="voteProgEta"></span></div>\n')

_V17_BAR_HTML = '<div class="votebar" id="voteBar"><span class="spacer"></span></div>\n'


def _v17_js(packset_total):
    """Whole-instrument progress + the submit controls moved to the foot.

    The controls are relocated at RUNTIME rather than emitted somewhere else, so
    every layer's build-time anchors (``downloadBtn``, the toolbar, the payload
    sites) keep pointing at exactly what they always pointed at. This module's
    history is largely a list of layers breaking each other by moving markup; a
    DOM move after load cannot do that.
    """
    return '''
  var VOTE_TOTAL = %(total)s;
  var VOTE_PROGRESS = '{n} of {total} across the whole sheet';
  var VOTE_ETA = 'about {minutes} min left for all {total}';
  var VOTE_ETA_ROUGH = 'about {minutes} min left for all {total} (rough)';
  var VOTE_DONE = 'all {total} decided';
  (function () {
    var bar = document.getElementById('voteBar');
    if (!bar) return;
    // The build tagged exactly the submit controls this document actually has.
    // Navigation (filters, facets, the type-scale control) is untagged and stays
    // on top, where it is used BEFORE deciding.
    var moved = document.querySelectorAll('[data-submit]');
    for (var i = 0; i < moved.length; i++) bar.appendChild(moved[i]);
  })();
  // One record backs every pack of a packset — STORE_KEY and TIME_KEY are keyed
  // on sheet_id, not on the pack — so this page can count and time the WHOLE
  // instrument without loading a single other pack.
  function __voteDecidedAll() {
    var n = 0;
    for (var k in state) {
      if (Object.prototype.hasOwnProperty.call(state, k) && state[k] && state[k].decision) n++;
    }
    return n;
  }
  function __voteSecs() {
    var per = (typeof __timing !== 'undefined' && __timing && __timing.per) ? __timing.per : null;
    var out = [];
    if (!per) return out;
    for (var k in per) {
      if (!Object.prototype.hasOwnProperty.call(per, k)) continue;
      if (!(state[k] && state[k].decision)) continue;
      if (per[k] > 0) out.push(per[k]);
    }
    return out;
  }
  function __voteEta(decided, total) {
    var left = Math.max(0, total - decided);
    if (!left) return VOTE_DONE.replace('{total}', total);
    var secs = __voteSecs();
    if (!secs.length) return '';
    secs.sort(function (a, b) { return a - b; });
    var mid = Math.floor(secs.length / 2);
    var med = (secs.length %% 2) ? secs[mid] : (secs[mid - 1] + secs[mid]) / 2;
    var minutes = Math.max(1, Math.round(med * left / 60));
    return (secs.length >= 5 ? VOTE_ETA : VOTE_ETA_ROUGH)
      .replace('{minutes}', minutes).replace('{total}', total);
  }
  function __voteProgress() {
    var total = VOTE_TOTAL || ids.length;
    var n = VOTE_TOTAL ? __voteDecidedAll() : ids.filter(function (id) {
      return state[id] && state[id].decision; }).length;
    if (n > total) n = total;
    var t = document.getElementById('voteProgText');
    if (t) t.innerHTML = VOTE_PROGRESS.replace('{n}', '<b>' + n + '</b>')
                                      .replace('{total}', '<b>' + total + '</b>');
    var b = document.getElementById('voteProgBar');
    if (b) b.style.width = (total ? Math.round(100 * n / total) : 0) + '%%';
    var e = document.getElementById('voteProgEta');
    if (e) e.textContent = __voteEta(n, total);
  }
  var __voteOrigTally = tally;
  tally = function () { __voteOrigTally(); __voteProgress(); };
  __voteProgress();
''' % {"total": json.dumps(packset_total or 0)}


#: The submit controls, as they appear in the finished document. Each is tagged
#: ONLY when present, so a sheet built without that layer carries no trace of it —
#: the absence contracts (`session_flow=False` etc.) are byte-level assertions.
_V17_SUBMIT_ANCHORS = (
    '<button class="dl" id="downloadBtn">',
    '<button class="dl" id="saveBtn"',
    '<button type="button" class="dl handin" id="handinBtn"',
    '<button class="dl handin" id="handinBtn"',
    '<button type="button" class="dl flowundo" id="flowUndoBtn"',
    '<button type="button" class="dl inbox" id="inboxBtn"',
    '<span class="inboxnote" id="inboxNote"',
    '<label id="strictReviewerWrap"',
    '<span id="strictReviewError"',
)
#: The pause toggle is deliberately NOT here: it drives the clock chip in the
#: header tally, and separating a control from the readout it operates is a
#: worse trade than the tidiness of having every button in one bar.


def _tag_submit_controls(doc):
    """Mark the submit controls this document actually carries."""
    n = 0
    for anchor in _V17_SUBMIT_ANCHORS:
        if anchor not in doc:
            continue
        head, rest = anchor.split(" ", 1)
        doc = doc.replace(anchor, head + ' data-submit="1" ' + rest, 1)
        n += 1
    return doc, n


# ----------------------------------------------------------------------------- split_layout (0.22.0)
# Opt-in two-column DE|RU chrome. extras=False never sees this flag (donor
# fixture). When True: wide main, independent-scroll columns, store anatomy
# behind a closed <details>, current-card vote controls mirrored into the
# existing V17 #voteBar (clicks write the hidden original, not the clone).
_SPLIT_LAYOUT_CSS = '''  body.split-layout main { max-width: none; padding: 10px 16px; }
  body.split-layout footer.hint { max-width: none; padding: 0 16px; }
  body.split-layout .savebanner { max-width: none; }
  body.split-layout .legend { max-width: none !important; }
  body.split-layout .facetbar { max-width: none; }
  .card-split { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: stretch; }
  .col-de, .col-ru { min-height: 0; overflow: auto; max-height: calc(100vh - 220px); }
  body.split-layout .card > .controls,
  body.split-layout .card > textarea.note,
  body.split-layout .card > .ratingrow,
  body.split-layout .card > .rejectlabelrow { display: none !important; }
  body.split-layout .votebar, body.split-layout #voteBar {
    position: fixed; bottom: 0; left: 0; right: 0; z-index: 20; margin-top: 0;
  }
  body.split-layout { padding-bottom: 160px; }
  .store-details { margin-top: 10px; font-size: 13px; }
  .store-details summary.store-link { cursor: pointer; color: var(--accent); }
  .pair-hl { outline: 2px solid var(--accent); background: #1a2744; border-radius: 6px; }
  .ins-chip { position: relative; display: inline-block; cursor: help; }
  .ins-chip .chip-tip {
    display: none; position: absolute; left: 0; top: 100%; z-index: 30;
    max-width: min(42vw, 520px); white-space: pre-wrap; word-break: break-word;
    background: #11141a; border: 1px solid var(--border); border-radius: 8px;
    padding: 8px 10px; color: var(--text); font-size: 12px; font-weight: 400;
    box-shadow: 0 8px 24px #0008;
  }
  .ins-chip:hover .chip-tip, .ins-chip.pinned .chip-tip { display: block; }
  .split-mirror { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1 1 auto; }
  .split-mirror textarea.note { min-width: 240px; flex: 1 1 240px; margin-top: 0; min-height: 44px; }
  @media (max-width: 900px) {
    .card-split { grid-template-columns: 1fr; }
    .col-de, .col-ru { max-height: none; }
  }
'''

_SPLIT_LAYOUT_JS = r'''
  (function splitLayout() {
    var bar = document.getElementById('voteBar');
    function refreshMirror(wrap, card) {
      if (!wrap || !card) return;
      var rec = state[card.getAttribute('data-id')] || {};
      wrap.querySelectorAll('button.vote').forEach(function (b) {
        b.classList.toggle('active', b.getAttribute('data-vote') === rec.decision);
      });
      var vs = wrap.querySelector('.vote-state');
      if (vs) vs.textContent = rec.decision ? rec.decision : 'unvoted';
      var ta = wrap.querySelector('textarea.note');
      var srcTa = card.querySelector('textarea.note');
      if (ta && srcTa && document.activeElement !== ta) ta.value = srcTa.value;
      wrap.querySelectorAll('button.rate').forEach(function (b) {
        var src = card.querySelector('button.rate[data-rate="' + b.getAttribute('data-rate') + '"]');
        if (src) b.className = src.className;
      });
    }
    function mirrorCard(card) {
      if (!bar || !card) return;
      var id = card.getAttribute('data-id');
      var old = bar.querySelector('.split-mirror');
      if (old && old.getAttribute('data-mirror-id') === id) {
        refreshMirror(old, card);
        return;
      }
      if (old) old.remove();
      var wrap = document.createElement('div');
      wrap.className = 'split-mirror';
      wrap.setAttribute('data-mirror-id', id);
      function forwardClick(src) {
        var c = src.cloneNode(true);
        c.addEventListener('click', function (e) {
          e.preventDefault();
          src.click();
          refreshMirror(wrap, card);
        });
        return c;
      }
      var controls = card.querySelector('.controls');
      if (controls) {
        controls.querySelectorAll('button.vote').forEach(function (b) { wrap.appendChild(forwardClick(b)); });
        var st = controls.querySelector('.vote-state');
        if (st) wrap.appendChild(st.cloneNode(true));
      }
      var rating = card.querySelector('.ratingrow');
      if (rating) {
        rating.querySelectorAll('button.rate').forEach(function (b) { wrap.appendChild(forwardClick(b)); });
      }
      var srcTa = card.querySelector('textarea.note');
      if (srcTa) {
        var ta = document.createElement('textarea');
        ta.className = 'note';
        ta.setAttribute('placeholder', srcTa.getAttribute('placeholder') || '');
        ta.value = srcTa.value;
        ta.addEventListener('input', function () {
          srcTa.value = ta.value;
          srcTa.dispatchEvent(new Event('input', { bubbles: true }));
        });
        wrap.appendChild(ta);
      }
      var spacer = bar.querySelector('.spacer');
      if (spacer) bar.insertBefore(wrap, spacer);
      else bar.insertBefore(wrap, bar.firstChild);
      refreshMirror(wrap, card);
    }
    var current = null;
    function pickCard() {
      var cards = document.querySelectorAll('.card');
      var mid = window.innerHeight / 2;
      var best = null, bestDist = Infinity;
      for (var i = 0; i < cards.length; i++) {
        var r = cards[i].getBoundingClientRect();
        if (r.bottom < 0 || r.top > window.innerHeight) continue;
        var visible = Math.min(r.bottom, window.innerHeight) - Math.max(r.top, 0);
        var dist = Math.abs(r.top - mid);
        if (visible >= 0.4 * r.height && dist < bestDist) {
          best = cards[i]; bestDist = dist;
        }
      }
      if (!best) {
        for (var j = 0; j < cards.length; j++) {
          var r2 = cards[j].getBoundingClientRect();
          var d2 = Math.abs(r2.top - mid);
          if (d2 < bestDist) { best = cards[j]; bestDist = d2; }
        }
      }
      return best;
    }
    function sync() {
      var card = pickCard();
      if (card) current = card;
      if (current) mirrorCard(current);
    }
    if (typeof IntersectionObserver === 'function') {
      var io = new IntersectionObserver(function () { sync(); }, { threshold: [0, 0.4, 1] });
      document.querySelectorAll('.card').forEach(function (c) { io.observe(c); });
    }
    window.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();
    var _apply = applyCardUI;
    applyCardUI = function (card) {
      _apply(card);
      var m = bar && bar.querySelector('.split-mirror');
      if (m && m.getAttribute('data-mirror-id') === card.getAttribute('data-id')) {
        refreshMirror(m, card);
      }
    };
    document.addEventListener('click', function (e) {
      var chip = e.target.closest('.ins-chip');
      if (chip) {
        if (chip.classList.contains('pinned')) chip.classList.remove('pinned');
        else {
          document.querySelectorAll('.ins-chip.pinned').forEach(function (x) { x.classList.remove('pinned'); });
          chip.classList.add('pinned');
        }
        e.stopPropagation();
        return;
      }
      if (!e.target.closest('.chip-tip')) {
        document.querySelectorAll('.ins-chip.pinned').forEach(function (x) { x.classList.remove('pinned'); });
      }
      var pairEl = e.target.closest('[data-pair]');
      if (!pairEl) return;
      var card = pairEl.closest('.card');
      if (!card) return;
      var pair = pairEl.getAttribute('data-pair');
      card.querySelectorAll('.pair-hl').forEach(function (n) { n.classList.remove('pair-hl'); });
      card.querySelectorAll('[data-pair="' + pair + '"]').forEach(function (n) { n.classList.add('pair-hl'); });
      var col = pairEl.closest('.col-de, .col-ru');
      var other = card.querySelector(col && col.classList.contains('col-de') ? '.col-ru' : '.col-de');
      if (other) {
        var tgt = other.querySelector('[data-pair="' + pair + '"]');
        if (tgt && tgt.scrollIntoView) tgt.scrollIntoView({ block: 'nearest' });
      }
    });
  })();
'''


def _add_split_layout(doc):
    """Wide two-column chrome + vote-bar mirror. extras=True only."""
    if "<body>" not in doc:
        raise ValueError("review-sheet body anchor is missing")
    doc = doc.replace("<body>", '<body class="split-layout">', 1)
    doc = doc.replace(
        "  main { max-width:980px; margin:0 auto; padding:10px 20px; }",
        "  main { max-width:none; margin:0 auto; padding:10px 16px; }",
        1,
    )
    doc = doc.replace(
        "  footer.hint { max-width:980px; margin:20px auto; padding:0 20px; color:var(--muted); font-size:12px; }",
        "  footer.hint { max-width:none; margin:20px auto; padding:0 16px; color:var(--muted); font-size:12px; }",
        1,
    )
    if "</style>" in doc:
        doc = doc.replace("</style>", _SPLIT_LAYOUT_CSS + "</style>", 1)
    return doc.replace("})();\n</script>", _SPLIT_LAYOUT_JS + "})();\n</script>", 1)


def _add_vote_ux(doc, packset_total):
    """Install V17 on a finished document (after every other DOM layer)."""
    doc, _tagged = _tag_submit_controls(doc)
    if "</style>" in doc:
        doc = doc.replace("</style>", _V17_CSS + "</style>", 1)
    # Inside the header, not before the toolbar: the header is already
    # `position:sticky; top:0`, so riding in it puts the bar genuinely at the top
    # and avoids two sticky-top:0 elements covering each other on scroll.
    if "</header>" in doc:
        doc = doc.replace("</header>", _V17_PROGRESS_HTML + "</header>", 1)
    else:
        anchor = '<div class="toolbar">'
        if anchor not in doc:
            raise ValueError("review-sheet toolbar anchor is missing")
        doc = doc.replace(anchor, _V17_PROGRESS_HTML + anchor, 1)
    foot_anchor = '<footer class="hint">'
    if foot_anchor in doc:
        doc = doc.replace(foot_anchor, _V17_BAR_HTML + foot_anchor, 1)
    else:
        doc = doc.replace("</main>", "</main>\n" + _V17_BAR_HTML, 1)
    # Auto-advance lands on the TOP of the card rather than its middle. Done HERE,
    # on the finished document, and never in the core template: `extras=False`
    # reproduces a pre-H779 shell byte-for-byte, and that fixture is exactly what
    # caught this being changed at the source.
    doc = doc.replace("block: 'center'", "block: 'start'")
    doc = doc.replace("block:'center'", "block:'start'")
    doc = doc.replace("})();\n</script>", _v17_js(packset_total) + "})();\n</script>", 1)
    return doc


# ----------------------------------------------------------------------------- V16 packs + GitHub inbox (H2991)
# W3 track B. Two problems, one layer:
#
#   * A 320-card sheet is one HTML file and one sitting. Splitting it into packs
#     of 10 gives the curator a unit they can finish, while the votes stay in ONE
#     localStorage record — parent and packs share `sheet_id`, so STORE_KEY is
#     the same string on gasyoun.github.io and pack 2 already knows what pack 1
#     decided.
#   * A vote that lives only in one browser is lost when that browser is. The
#     inbox layer pushes ids+verdicts to a public repo and pulls them back on
#     load, so a second machine resumes the same sitting.
#
# MEASURED 18-08-2026 — GitHub's OAuth device endpoints are not CORS-enabled.
# `OPTIONS https://github.com/login/device/code` with `Origin: https://gasyoun.
# github.io` returns 404 and NO `Access-Control-Allow-Origin`; the POST likewise
# comes back without one. A static page can therefore SEND the device-code
# request and never READ the reply — this is GitHub hardening the OAuth
# endpoints against browser-based token theft, not an outage to wait out. The
# `api.github.com` half is fine: the hydrate GET answers
# `Access-Control-Allow-Origin: *`, and the contents PUT preflight answers 204
# allowing `Authorization`. So B3 and the write itself work from the page; only
# TOKEN ACQUISITION needs a CORS-capable relay that forwards to github.com and
# echoes the headers back. `github_inbox["device_url"]` is where that relay goes.
# Empty (the default) leaves the button disabled with an honest tooltip rather
# than shipping a control that cannot succeed. No `client_secret` is involved at
# any point — device flow does not use one, which is why a relay stays safe to
# run without secrets.
_PACK_SIZE_DEFAULT = 10
_INBOX_REPO_DEFAULT = "gasyoun/vote-inbox"

_INBOX_CSS = '''  .dl.inbox { background:#2d6a4f; }
  .dl.inbox[disabled] { background:var(--panel2); color:var(--muted); cursor:not-allowed; border:1px solid var(--border); }
  .inboxnote { color:var(--muted); font-size:12px; }
  .inboxcode { font-family:ui-monospace,Consolas,monospace; font-size:16px; letter-spacing:.12em;
               background:#11141a; border:1px solid var(--border); border-radius:6px; padding:4px 10px; }
'''

_INBOX_BUTTON = ('<button type="button" class="dl inbox" id="inboxBtn" '
                 'title="push this pack\'s ids and verdicts to the public vote inbox">'
                 'Save to GitHub</button>'
                 '<span class="inboxnote" id="inboxNote" role="status"></span>')


def _inbox_js(inbox, pack_no, card_questions):
    """B2 + B3 — the inbox write and the hydrate read.

    Deliberately calls ``exportPayload()`` rather than re-deriving the item
    shape: repeating the ``note: rec.note || ''`` literal is the trap H2858 and
    H2887 already paid for, and every payload layer (V11 timing, V12 hand-in,
    V14 context) has already folded its fields into that one function by the
    time this layer runs. The inbox projection then throws most of it away —
    ids and verdicts are what a public repo is allowed to hold.
    """
    return '''
  var INBOX = %(inbox_json)s;
  var CARD_Q = %(questions_json)s;
  var INBOX_PULLING = 'pulling votes from GitHub…';
  var INBOX_HYDRATED = 'pulled {n} vote(s) from GitHub';
  var INBOX_SAVED = 'saved pack {pack} to GitHub';
  var INBOX_DISABLED = 'no OAuth client_id / device relay configured — use Download decisions.json';
  var INBOX_CODE = 'open {url} and enter code {code}';
  var INBOX_FAILED = 'GitHub save failed: {why}';
  var __inboxBtn = document.getElementById('inboxBtn');
  var __inboxNote = document.getElementById('inboxNote');
  function __inboxSay(msg) { if (__inboxNote) __inboxNote.textContent = msg; }
  function __inboxDir() {
    return 'https://api.github.com/repos/' + INBOX.repo + '/contents/decisions/'
      + encodeURIComponent(SHEET_ID);
  }
  // A public repo must not become a back door onto the card text. A note ships
  // only when it is short, carries no markup, and is not the card's own question
  // pasted back — otherwise the decision travels alone.
  function __inboxNoteOk(id, note) {
    if (!note) return false;
    if (note.length > 280) return false;
    if (note.indexOf('<') >= 0) return false;
    var q = CARD_Q[id];
    if (q && q.length > 12 && note.indexOf(q) >= 0) return false;
    return true;
  }
  function __inboxPayload() {
    var base = JSON.parse(exportPayload());
    return { sheet_id: base.sheet_id, pack: INBOX.pack, generated: base.generated,
             reviewedAt: base.reviewedAt, decided: base.decided,
             items: base.items.map(function (it) {
               var out = { id: it.id, decision: it.decision };
               if (__inboxNoteOk(it.id, it.note)) out.note = it.note;
               return out;
             }) };
  }
  // The pull is two network hops, and the second one -- raw.githubusercontent.com,
  // once per decisions file -- is routinely slow to settle, sometimes past 10 s,
  // while the api.github.com listing answers in about one. Measured 18-08-2026: the
  // first hydrate smoke FAILED on a 20 s ceiling against completely correct code.
  // Without a hint the reviewer sees an unvoted sheet that silently fills in later,
  // which reads as a bug and invites them to start voting over the top of votes that
  // are about to arrive. So say so while it is happening, and clear the line if the
  // pull turns out to bring nothing.
  function __inboxHydrate() {
    var said = false;
    function announce() { if (!said) { said = true; __inboxSay(INBOX_PULLING); } }
    function done(merged) {
      if (merged) { __inboxSay(INBOX_HYDRATED.replace('{n}', merged)); return; }
      if (said) __inboxSay('');
    }
    announce();
    fetch(__inboxDir()).then(function (r) { return r.ok ? r.json() : []; }).then(function (list) {
      if (!Array.isArray(list) || !list.length) { done(0); return; }
      var files = list.filter(function (f) { return /\\.json$/.test(f.name || ''); });
      var pending = files.length, merged = 0;
      if (!pending) { done(0); return; }
      files.forEach(function (f) {
        fetch(f.download_url).then(function (r) { return r.ok ? r.json() : null; })
          .then(function (doc) {
            if (!doc || !doc.items) return;
            doc.items.forEach(function (it) {
              if (!it.decision || ids.indexOf(it.id) < 0) return;
              // Two machines, one sheet: the inbox is the shared record, so it wins.
              state[it.id] = state[it.id] || {};
              if (state[it.id].decision !== it.decision) merged++;
              state[it.id].decision = it.decision;
            });
          })
          .catch(function () {})
          .then(function () {
            if (--pending > 0) return;
            if (merged) {
              save();
              document.querySelectorAll('.card').forEach(function (c) { applyCardUI(c); });
            }
            done(merged);
          });
      });
    }).catch(function () { done(0); });
  }
  function __inboxPut(token) {
    var path = 'decisions/' + encodeURIComponent(SHEET_ID) + '/pack-' + INBOX.pack_name + '.json';
    var url = 'https://api.github.com/repos/' + INBOX.repo + '/contents/' + path;
    var body = JSON.stringify(__inboxPayload(), null, 2);
    var enc = btoa(unescape(encodeURIComponent(body)));
    function send(sha) {
      var msg = { message: 'vote: ' + SHEET_ID + ' pack-' + INBOX.pack_name,
                  content: enc };
      // No branch unless the caller named one: the contents API then writes to the
      // repo's OWN default branch. Defaulting to 'main' here shipped a bug in
      // 0.17.0 — gasyoun/vote-inbox defaults to `master`, so the first real save
      // would have 404'd on a branch that does not exist.
      if (INBOX.branch) msg.branch = INBOX.branch;
      if (sha) msg.sha = sha;
      return fetch(url, { method:'PUT',
        headers: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json',
                   'Accept': 'application/vnd.github+json' },
        body: JSON.stringify(msg) });
    }
    return fetch(url + (INBOX.branch ? '?ref=' + encodeURIComponent(INBOX.branch) : ''),
                 { headers: { 'Authorization': 'Bearer ' + token } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (cur) { return send(cur && cur.sha); })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        __inboxSay(INBOX_SAVED.replace('{pack}', INBOX.pack_name));
      });
  }
  // GitHub does not send Access-Control-Allow-Origin on login/device/* (measured
  // 18-08-2026), so this exchange cannot go straight to github.com from a page.
  // INBOX.device_url must name a relay that forwards and echoes CORS headers.
  function __inboxDeviceToken() {
    var base = INBOX.device_url.replace(/\\/$/, '');
    return fetch(base + '/code', { method:'POST',
        headers: { 'Content-Type':'application/json', 'Accept':'application/json' },
        body: JSON.stringify({ client_id: INBOX.client_id, scope: 'public_repo' }) })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) {
        __inboxSay(INBOX_CODE.replace('{url}', d.verification_uri).replace('{code}', d.user_code));
        var iv = Math.max(5, d.interval || 5) * 1000, deadline = Date.now() + (d.expires_in || 900) * 1000;
        return new Promise(function (resolve, reject) {
          (function poll() {
            if (Date.now() > deadline) { reject(new Error('expired')); return; }
            setTimeout(function () {
              fetch(base + '/token', { method:'POST',
                  headers: { 'Content-Type':'application/json', 'Accept':'application/json' },
                  body: JSON.stringify({ client_id: INBOX.client_id, device_code: d.device_code,
                    grant_type: 'urn:ietf:params:oauth:grant-type:device_code' }) })
                .then(function (r) { return r.json(); })
                .then(function (t) {
                  if (t.access_token) { resolve(t.access_token); return; }
                  if (t.error === 'authorization_pending' || t.error === 'slow_down') { poll(); return; }
                  reject(new Error(t.error || 'device flow refused'));
                })
                .catch(reject);
            }, iv);
          })();
        });
      });
  }
  if (__inboxBtn) {
    if (!INBOX.enabled) {
      __inboxBtn.disabled = true;
      __inboxSay(INBOX_DISABLED);
    } else {
      __inboxBtn.addEventListener('click', function () {
        __inboxBtn.disabled = true;
        __inboxDeviceToken()
          .then(__inboxPut)
          .catch(function (e) { __inboxSay(INBOX_FAILED.replace('{why}', e && e.message ? e.message : e)); })
          .then(function () { __inboxBtn.disabled = false; });
      });
    }
  }
  __inboxHydrate();
''' % {"inbox_json": json.dumps(inbox, ensure_ascii=False),
       "questions_json": json.dumps(card_questions, ensure_ascii=False)}


def _normalize_inbox(raw, pack_no, pack_total):
    """Validate ``config["github_inbox"]`` and resolve the enabled state."""
    if not isinstance(raw, dict):
        raise TypeError("github_inbox must be a mapping")
    repo = str(raw.get("repo", _INBOX_REPO_DEFAULT))
    if repo.count("/") != 1 or not all(repo.split("/")):
        raise ValueError("github_inbox['repo'] must be 'owner/name'; got %r" % repo)
    for secret_key in ("client_secret", "token", "secret"):
        if raw.get(secret_key):
            raise ValueError(
                "github_inbox[%r] is refused: the device flow needs no secret, and a "
                "review sheet is a public artifact. Pass only a public client_id."
                % secret_key
            )
    client_id = str(raw.get("client_id", "") or "")
    device_url = str(raw.get("device_url", "") or "")
    return {
        "repo": repo,
        # Empty means "the repo's own default branch", which the contents API
        # resolves for us. Never guess 'main': gasyoun/vote-inbox is on `master`.
        "branch": str(raw.get("branch", "") or ""),
        "client_id": client_id,
        "device_url": device_url,
        "pack": pack_no,
        "pack_name": "%02d" % pack_no,
        "packs": pack_total,
        "enabled": bool(client_id and device_url),
    }


def _add_github_inbox(doc, inbox, items):
    """Install the V16 inbox layer on a finished pack/sheet document."""
    anchor = '<button class="dl" id="downloadBtn">Download decisions.json</button>'
    if anchor not in doc:
        raise ValueError("review-sheet download button anchor is missing")
    doc = doc.replace(anchor, anchor + _INBOX_BUTTON, 1)
    if "</style>" in doc:
        doc = doc.replace("</style>", _INBOX_CSS + "</style>", 1)
    questions = {}
    for it in items:
        q = _TAG_STRIP.sub(" ", it.get("question", "") or "")
        q = " ".join(q.split())
        if q:
            questions[it["id"]] = q
    doc = doc.replace("})();\n</script>", _inbox_js(inbox, inbox["pack"], questions) + "})();\n</script>", 1)
    return doc


_PARENT_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="dark">
<meta name="generator" content="csl-pyutil/%(version)s">
<title>%(title)s — %(packs)d packs</title>
<style>
  :root { color-scheme: dark; --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --text:#e6e6e6; --muted:#9aa0aa;
          --accent:#5b8cff; --ok:#3fb950; --border:#2a2f3a; }
  * { box-sizing: border-box; }
  body { background:var(--bg); color:var(--text); font-family:-apple-system,Segoe UI,Roboto,sans-serif;
         margin:0; padding:0 0 80px 0; font-size:15px; }
  header.top { background:var(--panel); border-bottom:1px solid var(--border); padding:14px 20px; }
  header.top h1 { font-size:17px; margin:0 0 4px; }
  header.top .sub { color:var(--muted); font-size:12px; }
  main { max-width:760px; margin:0 auto; padding:18px 20px; }
  .overall { background:var(--panel); border:1px solid var(--border); border-radius:10px;
             padding:14px 16px; margin-bottom:18px; }
  .bar { height:8px; background:var(--panel2); border-radius:5px; overflow:hidden; margin-top:8px; }
  .bar > i { display:block; height:100%%; background:var(--ok); width:0; transition:width .2s; }
  ol.packs { list-style:none; margin:0; padding:0; }
  ol.packs li { margin-bottom:10px; }
  a.pack { display:flex; align-items:center; justify-content:space-between; gap:12px;
           background:var(--panel); border:1px solid var(--border); border-radius:10px;
           padding:13px 16px; color:var(--text); text-decoration:none; }
  a.pack:hover { border-color:var(--accent); }
  a.pack .n { font-weight:700; }
  a.pack .prog { color:var(--muted); font-size:13px; }
  a.pack.done { border-left:4px solid var(--ok); }
  a.pack.done .prog { color:var(--ok); }
  footer.hint { max-width:760px; margin:20px auto; padding:0 20px; color:var(--muted); font-size:12px; }
</style>
</head>
<body>
<header class="top">
  <div>
    <h1>%(title)s</h1>
    <div class="sub">Generated %(generated)s &middot; sheet_id <code>%(sheet_id)s</code>
      &middot; %(n)d items in %(packs)d packs &middot; %(subtitle)s</div>
  </div>
</header>
<main>
  <div class="overall">
    <div><b id="ovText">0 of %(n)d decided</b></div>
    <div class="bar"><i id="ovBar"></i></div>
  </div>
  <ol class="packs" id="packs">%(rows)s
  </ol>
</main>
<footer class="hint">%(footer)s Each pack is its own page; all packs share this
  sheet_id, so one browser keeps one record of the whole sheet and a pack you
  finished stays finished when you come back.</footer>
<script>
(function () {
  var SHEET_ID = %(sheet_id_json)s;
  var STORE_KEY = 'review-sheet:' + SHEET_ID;
  var PACKS = %(packs_json)s;
  var state = {};
  try { state = JSON.parse(localStorage.getItem(STORE_KEY) || '{}') || {}; } catch (e) { state = {}; }
  var total = 0, done = 0;
  PACKS.forEach(function (p) {
    var d = p.ids.filter(function (id) { return state[id] && state[id].decision; }).length;
    total += p.ids.length; done += d;
    var el = document.getElementById('pack-' + p.name);
    if (!el) return;
    el.querySelector('.prog').textContent = d + ' / ' + p.ids.length;
    if (d === p.ids.length) el.classList.add('done');
  });
  document.getElementById('ovText').textContent = done + ' of ' + total + ' decided';
  document.getElementById('ovBar').style.width = (total ? (100 * done / total) : 0) + '%%';
})();
</script>
</body>
</html>
'''


def _render_pack_parent(config, pack_slices, hub_name):
    """The index page over a packset: one row per pack, progress off the shared record."""
    packs_meta = [{"name": "%02d" % n, "ids": [it["id"] for it in sl]}
                  for n, sl in enumerate(pack_slices, 1)]
    rows = "".join(
        '\n    <li><a class="pack" id="pack-%(name)s" href="%(href)s">'
        '<span class="n">Pack %(num)d of %(total)d</span>'
        '<span class="prog">0 / %(n)d</span></a></li>'
        % {"name": p["name"], "num": i, "total": len(packs_meta), "n": len(p["ids"]),
           "href": esc("%s/pack-%s.html" % (hub_name, p["name"]))}
        for i, p in enumerate(packs_meta, 1)
    )
    return _PARENT_TEMPLATE % {
        "version": __version__,
        "title": esc(config["title"]), "subtitle": esc(config["subtitle"]),
        "footer": config["footer"], "generated": esc(config["generated"]),
        "sheet_id": esc(config["sheet_id"]),
        "n": sum(len(p["ids"]) for p in packs_meta), "packs": len(packs_meta),
        "rows": rows,
        "sheet_id_json": json.dumps(config["sheet_id"]),
        "packs_json": json.dumps(packs_meta),
    }


def render_review_sheet(items, config, *, extras=True, screening=None, manifest=None):
    """Build a self-contained HTML review/voting sheet.

    items: list of dicts, each ``{"id", "filt", "title", "badges": [...]
        (optional), "question" (HTML), "panels": [(heading, html_body), ...],
        "note_placeholder" (optional)}`` — the exact shape
        ``build_h180_review_sheets.py`` used. ``filt`` is the value the filter
        bar's buttons match against (``data-filt``).
    config: dict with ``sheet_id``, ``title``, ``subtitle``, ``footer``,
        ``approve_label``, ``reject_label``, ``filters`` (list of
        ``(key, label)`` tuples for the filter bar), and ``generated`` (a
        date string — pass it explicitly, never computed here, so output is
        reproducible).
    extras: fold in the H779 auto-save + legend additions (default True for
        real callers). Pass False only to reproduce a pre-H779 shell's
        literal historical output (see tests/test_fixture_byte_identical.py).
    screening: **required when extras=True** (H1649). Mapping with counts for
        deterministic / lookup / agent / human, plus ``evidence_path`` and
        ``rules``. Rendered as a banner so the reviewer sees what was taken
        off their plate. Building without it raises ``ValueError``. Ignored
        when ``extras=False`` (donor byte-identical path).
    manifest: **V9 (H1889)** — a ``csl_pyutil.evidence.EvidenceManifest`` naming
        every repo artifact keyed on these row ids that was joined into the
        cards, and every one deliberately left out with a reason. When passed,
        :func:`csl_pyutil.evidence.preflight` runs against the FINISHED document
        and raises ``PreflightError`` before any HTML is returned. When absent,
        a ``PreflightWarning`` states the reason — a migration ramp for the
        pre-H1889 generators, which becomes an error in 1.0.0. Tune the checks
        with ``config["preflight"]`` (``allow_slp1_tokens``,
        ``overlap_threshold``, ``skip_prior_art``).

    config["non_decision_share"]: **V10 (H1889)** — the maximum fraction of
        cards a sheet may carry that the CALLER's own pre-filter already
        resolved, marked per card with ``item["machine_resolvable"] = True``.
        Default **0.0**: a card the machine has answered does not belong on a
        human's plate at all. Over the threshold raises ``PreflightError``. A
        sheet whose items carry no such flag is unaffected.

    config["identity_gate"]: **V13 (H2854)** — ``{"patterns": [regex, ...],
        "labels": {match: label, ...}}``. Deterministic, no heuristics: every
        distinct regex match against a card's tag-stripped ``question`` must
        have a ``labels`` entry, and that label's text must itself appear in
        the same question — the acc001 lesson (H2841/H2842), a reviewer must
        not be able to vote on a bare internal id. A defective card raises
        ``PreflightError`` naming it. Absent ``identity_gate``: a
        ``PreflightWarning`` (same migration-ramp shape as V9's manifest
        warning, becomes an error in 1.0.0). Named V13, not V12 — H2858 (same
        day) already shipped V12 for the partial hand-in + pause layer.
    item["typology"]: **U7 (H2846)** — ``[{"label", "n", "share"}, ...]``, one
        entry per classification label this card is being asked to confirm.
        Rendered as chips distinct from plain ``badges``, each showing the
        label plus its count on this card and its share of the sheet's whole
        population (``"share": 0.86`` renders ``86%``). Omitting ``n`` or
        ``share`` raises ``PreflightError`` — pass ``"share_unknown": True``
        on an entry only when the population share is genuinely unknown; a
        bare label is a build error, not a style lapse (see
        ``_check_typology_stats``). Cards with no ``typology`` key are
        unaffected.

    config["strict_review"]: optional mapping enabling an additive strict
        decisions export. ``reviewer`` supplies the initial reviewer ID;
        ``require_all_votes`` and ``require_reject_note`` default to True.
        Strict exports add top-level ``reviewer``, ``reviewedAt``, and
        ``complete`` fields. Partial auto-saves remain possible with
        ``complete:false``; final download is blocked until the policy passes.

        Since 0.23.0 (H3697) EVERY export also carries a top-level
        ``reviewedAt`` export stamp: the base payload already wrote the export
        moment into ``generated``, so the explicit key makes the vote moment
        machine-readable everywhere (the S6 census greps ``reviewedAt``), while
        ``generated`` is kept byte-compatible for existing consumers. In strict
        exports ``reviewedAt`` remains the policy-gated vote time and
        ``generated`` stays the sheet build date.

    19-07-2026 standard options (all optional and additive — with none of
    them set, and no item carrying ``title_href``, output is unchanged):

    - ``config["show_ids"]`` (V3): render each card's ``id`` as a visible,
      copyable chip in the card header so the reviewer can cite it back.
    - item ``title_href`` (V4): card header title becomes a clickable link
      to the full source entry (generator supplies the URL).
    - ``config["rating"]`` (V1+V5): ``{"label": "DA", "scale": 5,
      "threshold": 3, "approve_min": 4}`` — a row of 1..scale click-buttons
      BELOW the card content (never above); values below ``threshold`` show
      a warning color; voting approve auto-raises the rating to at least
      ``approve_min`` (manual clicks can then lower/raise it). The export's
      items gain a fourth field ``rating`` (number or null).
    - ``config["note_min_height_px"]`` (V6): taller note textarea.
    - ``config["save_as"]`` (V8): exact destination path for the exported
      decisions file, rendered as an always-visible banner together with the
      ``sheet_id`` so both the human and a later agent can bind the export
      to this sheet.
    - ``mark_cyrillic()`` (V7): helper for generators — wraps Cyrillic runs
      in ``<mark class="hl">``; the matching style ships with the standard
      CSS (always included once any standard option is active).

    config["reject_labels"]: optional ordered list of ``(value, human_label)``
        pairs (H1802). When present, choosing *reject* on a card reveals a
        required single-select control (the note textarea stays, for the
        rationale). Each exported item gains a ``reject_label`` field
        (``"<value>"`` or ``null``); ``note`` is left untouched. With
        ``strict_review`` on and ``require_reject_note`` true, a reject with
        no ``reject_label`` blocks the export the same way a missing note
        does. Replaces the unenforceable "correct label as the first word of
        the note" convention (measured 83% non-compliant on the first real
        G6 vote, H1796) with an actual control.
    Presentation (H1808, ``extras=True`` only — ``extras=False`` stays a
    byte-faithful donor shell):

    - ``config["font_scale"]``: multiplier over the whole type scale, default
      **1.5** (MG 28-07-2026, "+150%"), plus an A−/A+ toolbar control that
      re-points it per browser. ``1`` restores the donor sizes exactly.
    - ``config["extra_css"]``: caller CSS appended last in the cascade. Its
      absence is why csl-atlas's anatomy helper had to inline every colour
      (H1646); ``csl_pyutil.anatomy`` now ships its stylesheet through here.

    Faceted browse (H1847, ``extras=True`` only):

    - ``config["facets"]``: ordered list of dimensions, each either a mapping
      ``{"key", "label", "values": [(value, label), ...]}`` or a
      ``(key, label, values)`` triple. Renders a facet bar above the cards:
      multi-select WITHIN a dimension (OR), intersected ACROSS dimensions
      (AND), composed with the core single-dimension filter bar. Values carry
      whatever label the caller passes — put the corpus count in it, since the
      point of faceting a tag vocabulary is knowing how much a tag buys.
    - item ``facets``: ``{dimension_key: [values]}`` for that card. A card is
      matched by a dimension when it carries at least one selected value; a
      dimension a card has no value for simply never matches, so filtering on
      it hides that card rather than silently keeping it.
    - ``config["facet_count_label"]`` / ``config["facet_reset_label"]``:
      the visible-count template (``{shown}``/``{total}`` placeholders) and the
      reset button's text — pass translations here, as with ``ui_strings``.

    Timing (V11, H2840, ``extras=True`` only — default ON):

    - ``config["timing"]`` (bool, default True): the sheet meters the
      reviewer's ACTIVE time — a 1 s tick accumulates while the tab is
      visible (a gap over 4 s is discarded as sleep/hidden), attributed to
      the card nearest the viewport centre. A live ``⏱`` counter joins the
      tally; totals persist in localStorage beside the votes and export as
      integer seconds: top-level ``time_total_seconds``, per item
      ``time_seconds``. Pass ``False`` to opt a sheet out. Translate the
      chip tooltip via ``ui_strings["timing_title"]``.

    Hand-in and pause (V12, H2858, ``extras=True`` only — default ON):

    - ``config["hand_in"]`` (bool, default True): a second toolbar button,
      **Hand in what I got**, and a ⏸ toggle beside the ⏱ chip. The toggle
      freezes the V11 clock (a break is not review time; the paused flag
      persists with the totals). The button flushes the notes, stops the clock,
      and exports the decisions payload marked ``partial: true`` /
      ``complete: false`` with ``undecided: N``, under a
      ``<sheet_id>_decisions_partial.json`` filename. It deliberately bypasses
      the ``strict_review`` all-votes gate — that gate exists to stop a sheet
      being *closed* half-done, not to trap a reviewer's work in a browser — and
      still carries the reviewer id when strict is on. Votes stay in
      localStorage, so the sitting resumes; appliers are already partial-safe,
      since a ``null`` decision is never applied. Translate via
      ``ui_strings["handin_button"|"handin_title"|"pause_title"|"handin_said"]``
      (``handin_said`` keeps its ``{n}``/``{total}`` placeholders).

    Session flow (V15, H2887, ``extras=True`` only — default ON):

    - ``config["session_flow"]`` (bool, default True): the voting-session layer.
      It fixes two defects the curator's «сохраняю решения, таймер не
      останавливается» surfaced (16-08-2026), the second of which nobody had
      reported:

      * **The clock now stops on every export**, not just on hand-in. V12 wrote
        the stop into ``handinBtn`` alone, so the PARTIAL exit stopped the clock
        and the FULL one («Download decisions.json», the strict variant, the
        file-picker) did not. The pause is now a STATE — ``running`` /
        ``manual`` / ``export`` / ``idle`` — persisted as ``pause_reason``
        beside ``paused`` in ``TIME_KEY``; a record written before this layer
        reads back as ``manual``. Any sign of continued voting (a vote, a note
        edit, a keypress, a pointer press, a scroll) rearms the clock — unless
        the pause was **manual**, which always wins. 90 s with no input pauses
        it as ``idle``. The chip says which of the three states it is in. The
        background autosave writes are deliberately NOT treated as exports (see
        the layer comment): they fire after every vote, so pausing there would
        freeze the clock for the whole sitting.
      * **The silent misvote is gone.** ``a``/``r``/``d`` targeted
        ``vis[activeIdx]``, and ``activeIdx`` moved on arrow keys only — scroll
        to card 40 with the mouse, press ``a``, and the vote landed off-screen
        while the clock billed the card at the viewport centre. Both now read
        ONE current card (V11's ``__timeActiveId()`` when the clock is on, the
        same nearest-to-centre rule written out when it is not), a throttled
        scroll handler keeps it in step, a ``.card.kbd-active`` ring makes it
        visible, and it is re-derived after any filter/facet click.

      Plus the rhythm the same interview asked for: auto-advance to the next
      undecided card after a vote, undo (``z`` or the ↶ button — it restores
      the previous decision, including "there was none", and never touches the
      clock), a progress bar with a median-based ETA that is marked rough until
      five cards are decided, and resume-at-the-first-undecided with a toast on
      load. Translate via ``ui_strings["flow_*"]`` (12 keys, all in
      ``RU_UI_STRINGS``). Named V15, not the plan's V14 — the export-context
      layer shipped as V14 the same day.

    Localization preset (H2854 step 2, decision 8): ``csl_pyutil.review_sheet.
    RU_UI_STRINGS`` (also importable as ``csl_pyutil.RU_UI_STRINGS``) is a
    ready-made Russian translation of every ``UI_STRINGS`` chrome key except
    ``save_banner`` (see its own docstring for why). Enable with one line:
    ``config["ui_strings"] = RU_UI_STRINGS``.

    Split layout (0.22.0, ``extras=True`` only — default OFF):

    - ``config["split_layout"]``: two full-width columns (``item["left"]`` /
      ``item["right"]``), store anatomy in a closed ``<details>`` from
      ``item["store_markup"]``, and the current card's vote/rating/note
      mirrored into the V17 ``#voteBar``. ``main`` has no 980px cap. Sheets
      without ``left``/``right`` raise ``ValueError``. ``extras=False``
      ignores the flag so the donor fixture stays byte-identical.

    Mobile layer (H2854 step 2, decision 12, ``extras=True`` only — always on,
    no config flag): one ``@media (max-width: 640px)`` block — buttons ≥44px,
    panels single-column, a compressed sticky header, wrapping filter chips.
    No JS.

    Meta generator (H2854 step 1, ``extras=True`` only): every render stamps
    ``<meta name="generator" content="csl-pyutil/{__version__}">`` right after
    the color-scheme meta, so the vote hub's weekly CI staleness check
    (gasyoun.github.io) can compare a published sheet against the latest
    csl-pyutil release tag with a plain string read.

    Export context (V14, ``extras=True`` only — default off):

    - ``config["context"]`` (mapping of str → scalar, e.g. ``{"handoff":
      "H2707", "repo": "gasyoun/BookIndex", "apply_with": "python
      scripts/…/apply_gate_decisions.py"}``): rides verbatim as a top-level
      ``context`` field in EVERY exported decisions payload — download,
      autosave, strict, hand-in — and is shown in the header beside
      ``sheet_id``. Born from the H2707 gate hand-in (16-08-2026): a
      decisions.json naming only its sheet_id does not say which handoff,
      repo, or apply command it belongs to. Appliers should treat it as
      opaque provenance (read, verify, never require).

    Returns the full HTML document as a string.
    """
    screening_norm = None
    if extras:
        if screening is None:
            raise ValueError(
                "screening= is required when extras=True (H1649). Pass a mapping with "
                "deterministic/lookup/agent/human counts, evidence_path, and rules. "
                "Use extras=False only for the donor byte-identical fixture path."
            )
        screening_norm = _normalize_screening(screening)
    elif screening is not None:
        # Donor path must stay byte-identical; refuse silent mixing.
        raise ValueError("screening= is incompatible with extras=False")

    # V10 first: a sheet that should not exist is not worth rendering.
    _check_non_decisions(items, config.get("non_decision_share", 0.0))
    # V13 (H2854): every internal id named in a card's question must also name
    # its human identity — same call site as V10, before any HTML is built.
    _check_identity(items, config.get("identity_gate"), config.get("sheet_id"), extras)
    # U7 (H2846): a typology label with no count/share is a build error.
    _check_typology_stats(items)

    show_ids = bool(config.get("show_ids", False))
    rating = config.get("rating")
    if rating is not None:
        if not isinstance(rating, dict):
            raise TypeError("rating must be a mapping")
        rating = {
            "label": str(rating.get("label", "Rating")),
            "scale": int(rating.get("scale", 5)),
            "threshold": int(rating.get("threshold", 3)),
            "approveMin": int(rating.get("approve_min", 4)),
        }
        if not (1 <= rating["threshold"] <= rating["scale"]) or not (1 <= rating["approveMin"] <= rating["scale"]):
            raise ValueError("rating threshold/approve_min must lie within 1..scale")
    save_as = config.get("save_as")
    note_min_height_px = config.get("note_min_height_px")
    reject_labels = config.get("reject_labels")
    if reject_labels is not None:
        reject_labels = [(str(v), str(l)) for v, l in reject_labels]
        if not reject_labels:
            raise ValueError("reject_labels must be a non-empty list of (value, label) pairs")
        values = [v for v, _ in reject_labels]
        if len(set(values)) != len(values):
            raise ValueError("reject_labels values must be unique")
    font_scale = config.get("font_scale", 1.5)
    if not isinstance(font_scale, (int, float)) or isinstance(font_scale, bool):
        raise TypeError("font_scale must be a number")
    if not (0.7 <= float(font_scale) <= 3):
        raise ValueError("font_scale must lie within 0.7..3")
    extra_css = config.get("extra_css")
    if extra_css is not None and not isinstance(extra_css, str):
        raise TypeError("extra_css must be a string")
    timing = config.get("timing", True)
    if not isinstance(timing, bool):
        raise TypeError("timing must be a bool")
    context = config.get("context")
    if context is not None:
        if not isinstance(context, dict) or not context:
            raise TypeError("context must be a non-empty mapping (e.g. "
                            "{'handoff': 'H2707', 'repo': 'gasyoun/BookIndex'})")
        for k, v in context.items():
            if not isinstance(k, str) or not isinstance(v, (str, int, float)):
                raise TypeError("context keys must be str and values scalar "
                                "(str/int/float); got %r: %r" % (k, v))
    hand_in = config.get("hand_in", True)
    if not isinstance(hand_in, bool):
        raise TypeError("hand_in must be a bool")
    session_flow = config.get("session_flow", True)
    if not isinstance(session_flow, bool):
        raise TypeError("session_flow must be a bool")
    # V16 (H2991). personal_data wins over every inbox setting: a sheet carrying
    # personal data may not gain a control that writes to a public repo, and must
    # not read one either, so the layer is simply absent from the document.
    personal_data = config.get("personal_data", False)
    if not isinstance(personal_data, bool):
        raise TypeError("personal_data must be a bool")
    # V17 (MG 18-08-2026): progress and submit controls where the reviewer's eye is.
    vote_ux = config.get("vote_ux", True)
    if not isinstance(vote_ux, bool):
        raise TypeError("vote_ux must be a bool")
    split_layout = bool(config.get("split_layout", False))
    if split_layout and extras:
        for it in items:
            if not it.get("left") or not it.get("right"):
                raise ValueError(
                    "split_layout=True requires item['left'] and item['right'] "
                    "(id=%r)" % (it.get("id"),)
                )
    elif split_layout and not extras:
        # Donor path must stay byte-identical; the flag is invisible here.
        split_layout = False
    packset_total = config.get("packset_total")
    if packset_total is not None:
        if not isinstance(packset_total, int) or isinstance(packset_total, bool):
            raise TypeError("packset_total must be an int")
        if packset_total < len(items):
            raise ValueError("packset_total (%d) is smaller than this page's own "
                             "item count (%d)" % (packset_total, len(items)))
    inbox_raw = config.get("github_inbox")
    inbox = None
    if inbox_raw is not None and not personal_data:
        pack_info = config.get("pack") or {}
        inbox = _normalize_inbox(inbox_raw, int(pack_info.get("index", 1)),
                                 int(pack_info.get("total", 1)))
    facets = _normalize_facets(config.get("facets"))
    facet_count_label = str(config.get("facet_count_label", "showing {shown} of {total}"))
    facet_reset_label = str(config.get("facet_reset_label", "clear facets"))
    standard_on = bool(show_ids or rating is not None or save_as or note_min_height_px is not None
                       or any(it.get("title_href") for it in items))
    cards = "\n".join(render_card(it, config["approve_label"], config["reject_label"],
                                  show_id=show_ids, rating=rating, reject_labels=reject_labels,
                                  split_layout=split_layout)
                      for it in items)
    filters = ('<button data-filter="all" class="active">all</button>'
               + "".join('<button data-filter="%s">%s</button>' % (esc(k), esc(l))
                         for k, l in config["filters"])
               + '<button data-filter="unvoted">unvoted only</button>')
    ids = [it["id"] for it in items]
    doc = _CORE_TEMPLATE % {
        "title": config["title"], "subtitle": config["subtitle"], "footer": config["footer"],
        "approve_label": config["approve_label"], "reject_label": config["reject_label"],
        "n": len(items), "generated": config["generated"], "sheet_id": config["sheet_id"],
        "cards": cards, "filters": filters,
        "sheet_id_json": json.dumps(config["sheet_id"]), "ids_json": json.dumps(ids),
        "generated_json": json.dumps(config["generated"]),
    }
    if not extras and config.get("strict_review") is not None:
        raise ValueError("strict_review requires extras=True")
    if not extras and facets is not None:
        raise ValueError("facets requires extras=True")
    if not extras:
        # Donor-parity mode: no scale layer, no caller CSS — see the fixture test.
        if standard_on:
            doc = _add_standard(doc, save_as=save_as, sheet_id=config["sheet_id"],
                                note_min_height_px=note_min_height_px, rating=rating)
        if reject_labels:
            doc = _add_reject_labels(doc, reject_labels, strict=False)
        # The gate never edits the document, so the donor fixture stays byte-identical;
        # the absent-manifest WARN is suppressed here because this path exists only to
        # reproduce a pre-H779 shell's historical output.
        return _evidence_gate(doc, manifest, config, extras=False)

    # H2854 step 1: stamp the render version so the vote-hub CI staleness check
    # (gasyoun.github.io) can compare a published sheet against the latest
    # csl-pyutil release tag with a plain string read, no repo-side bookkeeping.
    doc = _add_generator_meta(doc)

    # H1649: inject screening banner + CSS before extras polish.
    banner = _screening_banner_html(screening_norm)
    if "</style>" in doc:
        doc = doc.replace("</style>", _SCREENING_CSS + "\n</style>", 1)
    if '<div class="toolbar">' in doc:
        doc = doc.replace('<div class="toolbar">', banner + '\n<div class="toolbar">', 1)
    else:
        doc = doc.replace("<main", banner + "\n<main", 1)

    doc = _add_extras(doc)
    strict = config.get("strict_review")
    if strict is not None:
        if not isinstance(strict, dict):
            raise TypeError("strict_review must be a mapping")
        reviewer = strict.get("reviewer", "")
        if not isinstance(reviewer, str):
            raise TypeError("strict_review.reviewer must be a string")
        policy = {
            "reviewer": reviewer,
            "requireAllVotes": bool(strict.get("require_all_votes", True)),
            "requireRejectNote": bool(strict.get("require_reject_note", True)),
            "generated": config["generated"],
        }
        doc = _add_strict_review(doc, policy)
    if standard_on:
        doc = _add_standard(doc, save_as=save_as, sheet_id=config["sheet_id"],
                            note_min_height_px=note_min_height_px, rating=rating)
    if reject_labels:
        doc = _add_reject_labels(doc, reject_labels, strict=strict is not None)
    doc = _add_font_scale(doc, float(font_scale))
    doc = _add_mobile_css(doc)
    if facets is not None:
        doc = _add_facets(doc, facets, facet_count_label, facet_reset_label)
    if extra_css:
        doc = _add_extra_css(doc, extra_css)
    if timing:
        doc = _add_timing(doc)
    if hand_in:
        # After timing: the pause control drives the clock that layer installed,
        # and this layer instruments its own item, so it must not be in the
        # document when V11's item surgery runs.
        doc = _add_handin(doc, json.dumps(config["generated"]), timing=timing,
                          rating_on=rating is not None,
                          reject_labels_on=bool(reject_labels),
                          strict_on=config.get("strict_review") is not None)
    if session_flow:
        # After V11 and V12 — this layer drives the clock the first installed and
        # the pause control the second installed — and before V14 export context,
        # whose replace-all target this layer deliberately never contains.
        doc = _add_session_flow(doc, timing=timing, pause_ui=timing and hand_in,
                                facets_on=facets is not None)
    if context is not None:
        # After every payload-producing layer (V8 autosave, strict, V12 hand-in):
        # one replace_all then covers all export sites.
        doc = _add_export_context(doc, context)
    if inbox is not None:
        # V16 last among the payload layers: it projects exportPayload()'s finished
        # output down to ids+verdicts, so every field the earlier layers fold in is
        # already there to be dropped. Before _localize, so its strings translate.
        doc = _add_github_inbox(doc, inbox, items)
    if vote_ux:
        # Last of the DOM layers: it relocates controls the earlier layers
        # installed, so all of them must already be in the document.
        doc = _add_vote_ux(doc, packset_total)
    if split_layout:
        # After V17 so #voteBar exists for the current-card mirror.
        doc = _add_split_layout(doc)
    doc = _localize(doc, config.get("ui_strings"))
    # Last, on the finished document: the script-purity and citation checks must see
    # exactly what the reviewer will see, translations and all.
    return _evidence_gate(doc, manifest, config, extras=True)


def render_review_sheet_packset(items, config, *, extras=True, screening=None,
                                manifest=None, hub_name=None):
    """V16 (H2991) — split a long sheet into packs of ``config["pack_size"]`` (10).

    A 320-card sheet is one file and one sitting nobody finishes. This returns
    ``{"parent": html_or_None, "packs": [html, ...]}``: one page per pack of at
    most ``pack_size`` cards (the last may be shorter — 22 becomes 10+10+2), plus
    an index page listing them with live progress.

    **The packs share one record.** Every pack renders with the SAME
    ``config["sheet_id"]``, so ``STORE_KEY`` is one string per origin and pack 2
    already knows what pack 1 decided; the parent reads that same record to show
    per-pack progress. Each pack's exported JSON still carries only ITS OWN slice
    of ids, so a decisions file names exactly the cards that page could vote on.

    ``len(items) <= pack_size`` is not a packset: you get
    ``{"parent": None, "packs": [one_sheet]}``, byte-identical to calling
    :func:`render_review_sheet` directly. Splitting a sheet that fits would cost a
    click and buy nothing.

    ``hub_name`` is the published directory stem — the parent links to
    ``<hub_name>/pack-01.html``. Defaults to ``config["sheet_id"]``, which is the
    hub's own convention (``vote/sheets/<name>.html`` beside
    ``vote/sheets/<name>/pack-01.html``).

    ``config["github_inbox"]`` (V16, optional) adds the **Save to GitHub** control
    and the hydrate read — see :func:`_normalize_inbox`. Each pack writes
    ``decisions/<sheet_id>/pack-NN.json`` in the inbox repo, so packs never
    overwrite one another. ``config["personal_data"] = True`` removes the control
    and the read entirely, whatever ``github_inbox`` says.

    ``screening`` / ``manifest`` are forwarded to every pack unchanged: both
    describe the WHOLE sheet's provenance, and the manifest's own checks are
    manifest-level (evidence floor, prior art) or text-level against the document
    in hand, so a slice neither weakens nor falsely trips them.
    """
    pack_size = config.get("pack_size", _PACK_SIZE_DEFAULT)
    if not isinstance(pack_size, int) or isinstance(pack_size, bool):
        raise TypeError("pack_size must be an int")
    if pack_size < 1:
        raise ValueError("pack_size must be >= 1")
    items = list(items)
    if len(items) <= pack_size:
        return {"parent": None,
                "packs": [render_review_sheet(items, config, extras=extras,
                                              screening=screening, manifest=manifest)]}
    slices = [items[i:i + pack_size] for i in range(0, len(items), pack_size)]
    packs = []
    for n, sl in enumerate(slices, 1):
        cfg = dict(config)
        cfg["pack"] = {"index": n, "total": len(slices)}
        # V17: every pack shows progress and an ETA for the WHOLE instrument, not
        # just its own ten cards -- the reviewer's question on a 32-pack sheet is
        # how long the whole thing takes at the pace they are going.
        cfg.setdefault("packset_total", len(items))
        packs.append(render_review_sheet(sl, cfg, extras=extras,
                                         screening=screening, manifest=manifest))
    parent = _render_pack_parent(config, slices, hub_name or config["sheet_id"])
    return {"parent": parent, "packs": packs}
