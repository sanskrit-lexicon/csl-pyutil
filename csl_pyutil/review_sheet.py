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

__version__ = "0.7.0"

__all__ = ["render_review_sheet", "esc", "mark_cyrillic"]


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


def render_card(item, approve_label, reject_label, *, show_id=False, rating=None,
                reject_labels=None):
    """Ported verbatim from build_h180_review_sheets.py — item shape:
    {"id", "filt", "title", "badges": [...], "question" (HTML), "panels":
    [(heading, html_body), ...], "note_placeholder" (optional), "title_href"
    (optional — V4 of the 19-07-2026 standard: the card header becomes a
    clickable link to the full source entry)}.

    With ``show_id=False``, ``rating=None``, ``reject_labels=None`` and no
    ``title_href`` the output is byte-identical to the v0.2.0 renderer
    (fixture contract)."""
    panels = "".join(
        '<div class="panel"><h4>%s</h4>%s</div>' % (esc(h4), body)
        for h4, body in item["panels"])
    badges = "".join('<span class="badge">%s</span>' % esc(b) for b in item.get("badges", []))
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
    return JSON.stringify({ sheet_id: SHEET_ID, generated: new Date().toISOString(), decided: decided,
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
    return JSON.stringify({ sheet_id: SHEET_ID, generated: new Date().toISOString(), decided: decided,
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


def render_review_sheet(items, config, *, extras=True):
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
    config["strict_review"]: optional mapping enabling an additive strict
        decisions export. ``reviewer`` supplies the initial reviewer ID;
        ``require_all_votes`` and ``require_reject_note`` default to True.
        Strict exports add top-level ``reviewer``, ``reviewedAt``, and
        ``complete`` fields. Partial auto-saves remain possible with
        ``complete:false``; final download is blocked until the policy passes.

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

    Returns the full HTML document as a string.
    """
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
    facets = _normalize_facets(config.get("facets"))
    facet_count_label = str(config.get("facet_count_label", "showing {shown} of {total}"))
    facet_reset_label = str(config.get("facet_reset_label", "clear facets"))
    standard_on = bool(show_ids or rating is not None or save_as or note_min_height_px is not None
                       or any(it.get("title_href") for it in items))
    cards = "\n".join(render_card(it, config["approve_label"], config["reject_label"],
                                  show_id=show_ids, rating=rating, reject_labels=reject_labels)
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
        return doc

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
    if facets is not None:
        doc = _add_facets(doc, facets, facet_count_label, facet_reset_label)
    if extra_css:
        doc = _add_extra_css(doc, extra_css)
    return _localize(doc, config.get("ui_strings"))
