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

__version__ = "0.2.0"

__all__ = ["render_review_sheet", "esc"]


def esc(s):
    return html.escape("" if s is None else str(s))


# ----------------------------------------------------------------------------- core template
# Ported verbatim from build_h180_review_sheets.py's TEMPLATE — do not reformat
# or "clean up" whitespace/quoting here; a byte-identical fixture test depends
# on this string matching the donor exactly.
_CORE_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%(title)s — %(n)d items</title>
<style>
  :root { --bg:#0f1115; --panel:#171a21; --panel2:#1e222b; --text:#e6e6e6; --muted:#9aa0aa;
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
  textarea.note { width:100%%; margin-top:10px; min-height:44px; background:#11141a; color:var(--text);
                  border:1px solid var(--border); border-radius:6px; padding:8px; font-size:13px;
                  font-family:inherit; resize:vertical; }
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
  function vote(id, d) { state[id] = state[id] || {}; state[id].decision = d; save(); }
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


def render_card(item, approve_label, reject_label):
    """Ported verbatim from build_h180_review_sheets.py — item shape:
    {"id", "filt", "title", "badges": [...], "question" (HTML), "panels":
    [(heading, html_body), ...], "note_placeholder" (optional)}."""
    panels = "".join(
        '<div class="panel"><h4>%s</h4>%s</div>' % (esc(h4), body)
        for h4, body in item["panels"])
    badges = "".join('<span class="badge">%s</span>' % esc(b) for b in item.get("badges", []))
    return '''
  <section class="card" data-id="%s" data-filt="%s">
    <header><div class="hw">%s %s</div></header>
    <div class="question">%s</div>
    %s
    <div class="controls">
      <button class="vote approve" data-vote="approve">&#9989; %s</button>
      <button class="vote reject" data-vote="reject">&#10060; %s</button>
      <button class="vote defer" data-vote="defer">&#9208; Defer</button>
      <span class="vote-state">unvoted</span>
    </div>
    <textarea class="note" placeholder="%s"></textarea>
  </section>''' % (esc(item["id"]), esc(item["filt"]), esc(item["title"]), badges,
                   item["question"], panels, esc(approve_label), esc(reject_label),
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


def _add_extras(doc):
    doc = doc.replace(
        '<button class="dl" id="downloadBtn">Download decisions.json</button>',
        '<button class="dl" id="downloadBtn">Download decisions.json</button>' + _SAVE_BUTTON,
    )
    doc = doc.replace("</footer>\n<script>", "</footer>\n" + _LEGEND_HTML + "<script>")
    doc = doc.replace("})();\n</script>", _AUTOSAVE_JS + "})();\n</script>")
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

    Returns the full HTML document as a string.
    """
    cards = "\n".join(render_card(it, config["approve_label"], config["reject_label"]) for it in items)
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
    if not extras:
        return doc

    doc = _add_extras(doc)
    strict = config.get("strict_review")
    if strict is None:
        return doc
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
    return _add_strict_review(doc, policy)
