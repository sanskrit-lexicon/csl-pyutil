# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-07-29

### Added

- **`config["font_scale"]` — the type scale, defaulting to 1.5 (H1808).** MG, voting
  the SanskritLexicography G5 print-readiness sheet: «increase fonts by default
  +150%». The donor template's sizes also inverted the hierarchy — `.panel pre`, the
  text actually under judgement, was the *smallest* type on the page (12px) while
  uppercase panel labels and toolbar chrome took the visual weight; it now sits above
  the panel chrome (13.5px base). Every size routes through one `--fs` multiplier, and
  an A−/A+ toolbar control re-points it per browser (persisted under
  `review-sheet:<sheet_id>:fs`). The default is deliberately the big one: an opt-in
  knob would have left every existing generator emitting the old sizes. `font_scale=1`
  restores the donor sizes exactly, and `extras=False` (donor-parity mode) never gets
  the layer at all, so the byte-identical fixture test is untouched.
- **`config["extra_css"]` — a caller-CSS hook, appended last in the cascade.** Its
  absence is why csl-atlas's anatomy helper had to inline every colour (H1646, whose
  module docstring says so outright).
- **`csl_pyutil.anatomy` — the CDSL raw-markup anatomy colouring, now shared (H1808).**
  Lifted unchanged in behaviour from
  [`csl-atlas/scripts/lib/cdsl_anatomy.py`](https://github.com/sanskrit-lexicon/csl-atlas/blob/main/scripts/lib/cdsl_anatomy.py)
  (H1646, SHARED_CODE §23), which is now a re-export shim, when a SECOND sheet
  generator needed the same thing and had no way to reach it — MG on the G5 sheet:
  «why entry anatomy is missing again? It must be a hook». `highlight()` keeps the
  markup visible, dims delimiters and colours the payload by part class;
  `legend_html()` renders the swatch legend. New for the second caller: `<ab>` defaults
  to its own `abbreviation` class (PWG wraps *every* abbreviation in it, not just
  cf./Vgl. — csl-atlas passes `tag_parts={"ab": "crossref"}` for its xref semantics);
  `plain_hook` reaches text the markup does not delimit (NWS-layer cards carry
  citations as bare text with no `<ls>` around them); `payload_hook` lets a caller
  render a tagged payload itself, e.g. an `<ls>` citation as a Cologne source link;
  `legend_html(parts=…, extra_chips=…)` restricts and extends the legend.

## [0.5.0] - 2026-07-28

### Added

- **`config["reject_labels"]` — a required typology-label control on reject (H1802).**
  The G6 MQM contract asked reviewers to write the correct typology label as the
  first word of the free-text note; `strict_review` could require a note on reject
  but not its *shape*. Measured on the first real G6 vote (H1796): 5 of 6 rejects
  were prose, and the consumer's all-or-nothing apply meant all 20 votes — including
  14 clean approves — failed to apply. `reject_labels` is an ordered list of
  `(value, human_label)` pairs; when present, choosing *reject* on a card reveals a
  required single-select control (the note textarea stays, for the rationale).
  Absent, behaviour is unchanged. Each exported item gains a `reject_label` field
  (`"<value>"`/`null`); `note` is left untouched so `apply_decisions.py` can still
  read the legacy first-token convention on already-exported sheets. With
  `strict_review.require_reject_note` on, a reject with no `reject_label` blocks
  the export the same way a missing note does. Additive string surgery on the same
  stable anchors as `rating`/`standard` — a caller that passes nothing gets a
  byte-identical document.

## [0.4.0] - 2026-07-26

### Added

- **`config["ui_strings"]` — translate the emitter's own chrome (H1648).** A caller
  could already set `title` / `subtitle` / `footer` / `approve_label` / `reject_label`,
  but the toolbar button, keyboard hint, localStorage/export note, V8 save banner and
  the H779 approve/reject/defer legend were hard-coded English. csl-atlas's xref sheet
  is reviewed in Russian: its card content was fully translated while those five pieces
  of chrome — all of them instructions the reviewer has to read — stayed English.
  Localising by post-processing the emitted HTML in each caller would have copied the
  same brittle literals into every repo, so the mapping lives here beside the strings.
  Keys: `download_button`, `save_button`, `footer_hint`, `save_banner`, `legend`
  (`UI_STRINGS` is the public roster). Unknown keys and non-string values raise; a key
  whose chrome is absent from a given sheet (no `save_as`, `extras=False`) is skipped,
  so one table can serve every sheet a repo emits. Applied as a final surgery pass in
  the established `_add_extras` / `_add_standard` style — callers that pass nothing get
  a byte-identical document, and the fixture contract is untouched.

## [0.3.2] - 2026-07-23

### Fixed

- **Review-sheet note race on second vote (csl-pyutil#1 Part 1 / H1523 residual).**
  `vote()` previously wrote only `decision` into `state[id]`. That preserved an
  already-saved note, but a note still sitting only in the live `textarea` (missed
  `input` event, paste edge, or a second vote before the last keystroke committed)
  could export empty. `vote()` and the download path now re-read every card's
  textarea via `syncNoteFromDom()` before mutating decision / building the payload.
  `__version__` in `review_sheet.py` also re-synced to the package version (was
  stuck at `0.3.0` after the 0.3.1 release).

## [0.3.1] - 2026-07-19

### Fixed

- **Review sheets were unreadable in light-mode browsers/OS.** The template is
  dark-themed but declared no `color-scheme`, so a light-mode browser rendered the
  note `textarea` with a white native background while its text stayed light
  (`#e6e6e6`) — invisible letters (reported live while voting on the H1323
  ghost-word sheet). Added `<meta name="color-scheme" content="dark">` +
  `:root { color-scheme: dark }`, and forced the textarea's dark background + light
  text (`!important`, `-webkit-text-fill-color`, `::placeholder`) so it is readable
  regardless of OS theme. Golden byte-identical fixture regenerated to match; the
  `note_min_height_px` string-surgery contract is preserved.
- **`csl_pyutil.__version__` still reported `0.2.0` on the 0.3.0 release** (folded in
  from PR #5). The 0.3.0 release bumped `pyproject.toml` and `review_sheet.py`'s
  `__version__` but missed the shadow copy in `csl_pyutil/__init__.py`, which is the one
  consumers actually import (`from csl_pyutil import __version__`). Any downstream that
  pins the emitter by an equality guard — csl-atlas's `REQUIRED_EMITTER_VERSION` check in
  [`scripts/build-review-sheets.py`](https://github.com/sanskrit-lexicon/csl-atlas/blob/main/scripts/build-review-sheets.py)
  is the live case — could not express "require the V1–V8 standard". `__init__.py`
  `__version__` now tracks `pyproject.toml` and rides this 0.3.1 release.

## [0.3.0] - 2026-07-19

### Added — the 19-07-2026 review-sheet standard (V1–V8)

The org-wide sheet standard ratified from the `h178_da` vote's meta-note
([H178 DA-vote issue register §2](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/pwg_ru/H178_DA_VOTE_ISSUE_REGISTER_2026-07-19.md)),
implemented as additive string-surgery layers on the frozen core template
(the byte-identical fixture contract is untouched — with no standard option
set, output is unchanged):

- **V1/V5 `config["rating"]`** — a 1..scale click-button row **below** the
  card content (never above; replaces slider-style widgets), with a visible
  approval threshold and approve-vote coupling (voting approve auto-raises
  the rating to `approve_min`, default 4; manual clicks can then lower or
  raise it). Export items gain a fourth field `rating` (number|null) in the
  core, auto-save, and strict payload constructors alike.
- **V3 `config["show_ids"]`** — every card shows its `id` as a copyable
  monospace chip the reviewer can cite back.
- **V4 item `title_href`** — the card header becomes a clickable link to
  the full source entry.
- **V6 `config["note_min_height_px"]`** — taller free-text note box.
- **V7 `mark_cyrillic()`** — new exported helper wrapping Cyrillic runs in
  `<mark class="hl">` (matching style ships with the standard CSS), so the
  Russian words under judgment are visually distinct from markup and German.
- **V8 `config["save_as"]`** — an always-visible banner naming the
  `sheet_id`, the download filename, and the exact destination path, binding
  a downloaded decisions file to its sheet for both human and agent.

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
