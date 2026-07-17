# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-17

### Added — optional strict review exports

`render_review_sheet()` now accepts an optional `strict_review` policy. Strict
sheets preserve the existing decisions shape and add `reviewer`, `reviewedAt`,
and `complete`; final download requires reviewer attribution, a vote on every
item, and a non-empty note for every rejection. File-system auto-save continues
to write resumable partial drafts with `complete:false`, while the existing
sheet ID, item IDs, localStorage key, and named download remain unchanged.

## [0.1.1] - 2026-07-14

### Fixed — generic download filename collision

`_CORE_TEMPLATE`'s download button hardcoded the exported vote file's name as
the literal `decisions.json`, colliding with every other review sheet's
export in a flat Downloads/ folder — the exact collision problem the org's
no-generic-filename convention exists to prevent (found 14-07-2026 auditing
the H931 port). `a.download` is now `SHEET_ID + '_decisions.json'`, matching
the convention every hand-rolled sheet already followed. `tests/fixtures/h180_typology_golden.html`
regenerated to match (one deliberate deviation from byte-for-byte donor
fidelity, documented in `review_sheet.py`'s module docstring).

## [0.1.0] - 2026-07-14

### Added — `render_review_sheet()` (H925)

First release. `render_review_sheet(items, config, extras=True)` — the shared
HTML review/voting sheet emitter, ported byte-for-byte (fixture-tested) from
[`build_h180_review_sheets.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/build_h180_review_sheets.py),
the richest of six independently hand-rolled review-sheet shells found across
four repos. `extras=True` folds in H779's mandated File System Access API
auto-save + button-legend footer, which no existing shell had implemented.
