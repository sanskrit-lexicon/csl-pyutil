# csl-pyutil

_Created: 14-07-2026 · Last updated: 14-07-2026_

Generic (non-Sanskrit-specific) Python helpers shared across the CDSL /
Sanskrit-Lexicon repos. Distinct from
[`sanskrit-util`](https://github.com/sanskrit-lexicon/sanskrit-util), which is
scoped narrowly to Sanskrit string/transcoding helpers (IAST/SLP1/Devanāgarī)
— this package is for everything else that shouldn't be re-typed per repo but
also isn't Sanskrit-linguistics-specific.

## Why this exists

A [cross-repo dev-status + reuse review](https://github.com/gasyoun/Uprava/blob/main/CROSS_REPO_DEV_STATUS_AND_REUSE_REVIEW_07.2026.md)
found **six independently hand-rolled ~150–250-line HTML review-sheet shells**
across four repos — all implementing the same approve/reject/defer pattern
(running tally, `localStorage` persistence, a/r/d keyboard shortcuts, free-text
notes, `Download decisions.json` with an identical
`{sheet_id, generated, decided, items}` schema) — with **no shared import
between any of them**. Root cause: the org's `/review-sheet` Claude Code skill
is prose-only, so every invocation re-derived the same markup/JS from
scratch. Proven drift: none of the six shells implemented the skill-mandated
`showSaveFilePicker` auto-save + legend footer (H779, 12-07-2026) — manual
propagation had already failed once.

## `render_review_sheet()`

```sh
pip install "csl-pyutil @ git+https://github.com/sanskrit-lexicon/csl-pyutil@main"
```

```python
from csl_pyutil import render_review_sheet

html = render_review_sheet(
    items=[
        {"id": "L142", "filt": "typeA", "title": "headword or item label",
         "badges": ["tag1", "tag2"],
         "question": "the judgment question shown on the card (HTML allowed)",
         "panels": [("Panel heading", "<pre>panel body, HTML allowed</pre>")],
         "note_placeholder": "optional custom placeholder text"},
        ...
    ],
    config={
        "sheet_id": "commentarystrategies-sundarakanda_35-37",  # org naming convention
        "title": "Sundarakāṇḍa commentary xref — sarga 35-37",
        "subtitle": "43 candidate cross-references needing a decision",
        "footer": "Approve = accept the xref. Reject = discard. Defer = unsure.",
        "approve_label": "Approve", "reject_label": "Reject",
        "filters": [("typeA", "Type A"), ("typeB", "Type B")],
        "generated": "2026-07-14",  # caller-supplied, never computed here — deterministic output
    },
)
open("review/commentarystrategies-sundarakanda_35-37_review.html", "w",
     encoding="utf-8").write(html)
```

Ported byte-for-byte (proven by a fixture test, `tests/test_fixture_byte_identical.py`)
from
[`SanskritLexicography/RussianTranslation/src/build_h180_review_sheets.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/build_h180_review_sheets.py)
— the richest of the six hand-rolled shells (H925). `extras=True` (the
default) additionally folds in what H779 mandated but no shell implemented: a
File System Access API "Save to folder" auto-save control and a button-legend
footer. Pass `extras=False` only to reproduce a pre-H779 shell's literal
historical output.

Exported decisions-JSON shape (unchanged from every shell's prior contract, so
[`Uprava/tools/review_decisions_watcher.py`](https://github.com/gasyoun/Uprava/blob/main/tools/review_decisions_watcher.py)
needs no changes):

```json
{"sheet_id": "...", "generated": "2026-07-14T12:00:00.000Z", "decided": 12,
 "items": [{"id": "L142", "decision": "approve", "note": ""}, ...]}
```

See [`csl_pyutil/review_sheet.py`](csl_pyutil/review_sheet.py) for the full
item/config schema docstring.

The sheet's naming, placement (gitignored `review/`), GTD `@DO` line, and
`Uprava/REVIEW_SHEETS_INDEX.md` registration are still the caller's job — this
function only produces the HTML string. See
[`~/.claude/commands/review-sheet.md`](https://github.com/gasyoun/claude-config/blob/main/commands/review-sheet.md)
for the full process.

## Tests

```sh
pip install -e . pytest
pytest tests -q
```

`tests/fixtures/` holds 100%-synthetic placeholder content generated only
through the donor's own render functions — never real translation data (the
donor's own gitignored/unpublished pwg_ru store must never land in this
public repo).
