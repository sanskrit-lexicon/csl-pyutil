# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.13.0] - 2026-08-16

### Added

- **V14 export context — decisions payloads carry their provenance (`config["context"]`, `extras=True` only).** Born from the H2707 crosswalk-gate hand-in (MG, 16-08-2026): «почему в скачанном .json нет главного, H2707 для опознания к кому он принадлежит?» A small str→scalar mapping (recommended keys: `handoff`, `repo`, `apply_with`) now rides verbatim as a top-level `context` field in EVERY exported decisions payload — download, autosave, strict, and V12 hand-in — and is shown in the header beside `sheet_id`, so both the file and the page answer whose sheet this is. Default off; validated shape; additive string surgery applied after all payload-producing layers; the donor byte-identical path never gets it. Tests: `tests/test_export_context.py`.

## [0.12.0] - 2026-08-16

### Added

- **`<meta name="generator">` tag, `extras=True` only ([H2854](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2854-Sonnet_Uprava_vote-platform-w1-build_15.08.26.md) step 1).**
  Every render stamps `<meta name="generator" content="csl-pyutil/{__version__}">`
  right after the color-scheme meta, before `<title>`. This is the whole
  mechanism the vote hub's weekly CI staleness check (gasyoun.github.io) needs
  to tell whether a published sheet is stale against the latest csl-pyutil
  release tag — a plain string read, no repo-side bookkeeping.
- **V13 identity gate — `config["identity_gate"]`, `PreflightError` (H2854
  step 2).** MG, gating the BookIndex crosswalk sheets (H2841/H2842): a card
  that names an internal id (`acc001`, `ch04`, …) without also naming the
  human identity behind it lets a reviewer vote on a bare token. Deterministic,
  no heuristics: every regex match in `config["identity_gate"]["patterns"]`
  found in a card's tag-stripped `question` must have a
  `config["identity_gate"]["labels"]` entry, and that label's text must itself
  occur in the same question. A defective card raises `PreflightError` naming
  it; an absent `identity_gate` emits a `PreflightWarning` (same migration-ramp
  shape as V9's manifest warning — an error in 1.0.0). **Named V13, not the
  plan's original "V12"**: [H2858](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2858-Opus_csl-pyutil_review-sheet-partial-submit-pause-timer_15.08.26.md)
  merged the same day and already claimed V12 for the partial hand-in + pause
  layer (v0.11.0) — this build takes the plan's own ambiguity-contract default
  (decision 14, default+log) rather than colliding with a shipped feature.
- **`RU_UI_STRINGS` — a ready-made Russian chrome preset (H2854 step 2,
  decision 8).** `csl_pyutil.review_sheet.RU_UI_STRINGS` (also
  `csl_pyutil.RU_UI_STRINGS`) translates every `UI_STRINGS` key that exists as
  of this release except `save_banner` — that key's default body bakes in the
  caller's actual `sheet_id`/`save_as` values before `_localize` runs, so a
  fixed replacement string would silently drop them rather than translate
  them; see the constant's docstring for the one-line override a generator
  using `save_as` needs. One line enables a whole sheet:
  `config["ui_strings"] = RU_UI_STRINGS`.
- **Mobile layer — one `@media (max-width: 640px)` block, `extras=True` only,
  always on (H2854 step 2, decision 12).** Buttons ≥44px, panels single-column,
  a compressed sticky header, wrapping filter chips. No JS, no config flag —
  a curator voting from a phone should not need one.

## [0.11.0] - 2026-08-15

### Added

- **V12 — «hand in what I got» + a pausable clock, on by default for every
  `extras=True` sheet
  ([H2858](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2858-Opus_csl-pyutil_review-sheet-partial-submit-pause-timer_15.08.26.md)).**
  MG, after one sitting on the BookIndex crosswalk gate (15-08-2026 — 30 approve
  / 14 reject of 255 cards in 14 minutes): «Хочу поставить на паузу, остановить
  таймер и остановить работу, сдать то что было. Но такой функции как сдать
  сколько успел нет — а она нужна.» Mechanically the plain download button had
  always exported partial work (unvoted items carry `decision: null`), but
  nothing in the sheet *said* so: a button labelled "Download decisions.json"
  reads as the finish line, and under `strict_review` it genuinely is one — that
  handler refuses to export until every card is voted. A reviewer who ran out of
  time therefore had no sanctioned way to stop.

  Two controls close that: a ⏸ toggle beside the V11 ⏱ chip freezes the clock
  (a break is not review time; the paused flag persists in localStorage with the
  totals, so a pause survives closing the tab), and a second toolbar button
  flushes the notes, stops the clock, and exports the decisions payload marked
  `partial: true` / `complete: false` with `undecided: N`, under a
  `<sheet_id>_decisions_partial.json` filename that cannot be mistaken for a
  finished sheet. The hand-in deliberately bypasses the strict all-votes gate —
  that gate exists to stop a sheet being *closed* half-done, not to trap a
  reviewer's work in a browser — while still carrying the reviewer id. Votes
  stay in localStorage, so the sitting resumes; appliers are already
  partial-safe, since a `null` decision is never applied.

  Emitted for exactly the layers a given sheet has (no `typeof` probes, so a
  `timing=False` or reject-label-less sheet keeps its identifier-absence
  contract), and the item is assembled by assignment rather than as the shared
  object literal, so V11's item surgery cannot instrument it twice.
  `config["hand_in"] = False` opts a sheet out; the donor `extras=False` fixture
  path never gets it; the label, both tooltips, and the confirmation sentence
  (which keeps its `{n}`/`{total}` placeholders) translate through
  `ui_strings["handin_button"|"handin_title"|"pause_title"|"handin_said"]`.

## [0.10.0] - 2026-08-15

### Added

- **V11 — active-time metering, on by default for every `extras=True` sheet
  ([H2840](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2840-Fable_csl-pyutil_review-sheet-timing-v11_15.08.26.md)).**
  MG, voting the BookIndex crosswalk gate 15-08-2026: the sheet itself must
  measure how long the reviewer spends on the page and on each card — here and
  in every other vote. A 1 s tick accumulates while the tab is visible (a gap
  over 4 s is discarded as sleep/hidden) and is attributed to the card nearest
  the viewport centre; a live `⏱` counter joins the tally; totals persist in
  localStorage beside the votes and ship in the decisions export as integer
  seconds — top-level `time_total_seconds`, per item `time_seconds` — so the
  apply pipeline and the vote hub's «Труд» traffic light can calibrate on real
  numbers instead of guesses. Additive string surgery applied LAST, so the
  item-literal instrumentation catches every constructor the earlier layers
  (rating, reject-label, strict) produce; the donor `extras=False` fixture path
  never gets it; `config["timing"] = False` opts a sheet out;
  `ui_strings["timing_title"]` translates the chip tooltip.

### Added

- **`csl_pyutil.evidence` — the review-sheet evidence gate, lifted from its one-repo
  home (H1889).** `EvidenceManifest`, `preflight()`, `valid_sutras()`,
  `sutra_href()`, the D1/D2 SLP1 detectors and the mixed-script detector move here
  from
  [`SanskritLexicography/RussianTranslation/src/review_evidence_preflight.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/review_evidence_preflight.py)
  (H1887), whose copy becomes a re-export shim — the same pattern H1808 used for
  `cdsl_anatomy`. Lifted, not rewritten: both deliberate asymmetries survive
  verbatim — a conceptual `declare_omitted()` can never silence a FOUND artifact
  (only `declare_omitted_path()` can), and the SLP1 detector stays silent on the
  undecidable all-lowercase case rather than guessing. `repo_root` now defaults to
  the current working directory instead of the module's own parent, which is the
  only behavioural change the move forced.
- **V9 — `render_review_sheet(..., manifest=)` runs the gate and RAISES before any
  HTML is returned (H1889).** V1–V8 + H1808 are entirely presentation, so a sheet
  could be green on every rule and still ask a human to re-derive what the repo
  already holds on disk: measured on the sheet that triggered this, **191 of 200
  cards** already had a machine verdict, a named rule and cited evidence from the
  same inputs, and none of it was rendered. The gate runs on the FINISHED document,
  after `ui_strings`, so the script-purity and citation checks see exactly what the
  reviewer will see. Tunable via `config["preflight"]` (`allow_slp1_tokens`,
  `overlap_threshold`, `skip_prior_art`); an unknown key raises rather than being
  ignored. With no `manifest=`, a `PreflightWarning` states the reason so the 22+
  existing generators keep working — a migration ramp with a deadline (it becomes an
  error in 1.0.0), not a permanent posture; escalate it today with
  `-W error::csl_pyutil.evidence.PreflightWarning`.
- **V10 — `config["non_decision_share"]`: a sheet that is mostly non-decisions is
  refused (H1889).** 69 of those same 200 cards were not disagreements at all. The
  CALLER classifies (`item["machine_resolvable"] = True`) because only it knows its
  domain; the emitter enforces the threshold, which **defaults to 0.0** — a card the
  machine has already answered has no business on a human's plate. Over the
  threshold raises `PreflightError`; a sheet with no flagged item is unaffected, so
  every existing caller is untouched.
- **`ui_strings` keys `defer_button` and `reject_reason_label` (H1889).** The
  per-card "Defer" button and the H1802 reject-picker's "Reason" label were the last
  two visible strings a fully translated sheet could not reach, so a Russian sheet
  still showed two English words. H1887 deliberately refused to patch this with
  per-caller post-processing of the emitted HTML — the exact anti-pattern
  `UI_STRINGS` exists to kill. Both are anchored on their surrounding markup, so the
  legend's own `<b>Defer</b>` explanation and any caller text saying "Reason" are
  left alone.

## [0.8.1] - 2026-08-04

### Fixed

- `review_sheet.__version__` was left at `0.7.0` while the package moved to `0.8.0` — the
  same two-disagreeing-version-strings defect the `0.7.0` release claimed to close,
  regressed one release later because nothing pinned it. Both now track the package
  version again, and `tests/test_version_strings.py` asserts
  `csl_pyutil.__version__ == review_sheet.__version__ == pyproject [project].version`
  so the next bump cannot silently drift (H2131).

## [0.8.0] - 2026-08-01

### Added

- **`screening=` required on `render_review_sheet(..., extras=True)` (H1649, V0.8.0).**
  Mapping `{deterministic, lookup, agent, human, evidence_path, rules}` is rendered as a
  sticky banner stating what was taken off the reviewer's plate. Building without it
  raises `ValueError`. `extras=False` (donor byte-identical fixture) refuses `screening=`
  so the historical shell stays untouched. Callers that have not screened must still pass
  an honest block (e.g. all zeros on a–c and `human=len(items)` with `rules=["none"]` and
  an evidence path that says so) — silence is no longer allowed.

## [0.7.0] - 2026-07-29

### Added

- **`config["facets"]` — faceted browse over N caller-defined dimensions (H1847).**
  The core filter bar is ONE dimension, single-select (`data-filt`) — enough for a
  stratum, useless for browsing a tag vocabulary. Cards now carry
  `item["facets"] = {dimension: [values]}` (one JSON `data-facets` attribute, because a
  card in both `ifc` and `Bhvr` has no honest single-attribute encoding), and the
  rendered bar multi-selects WITHIN a dimension (OR) while intersecting ACROSS
  dimensions (AND) — «all Vedic senses standing at the end of a compound» is one click
  each. Value labels are whatever the caller passes, so corpus counts ride in the chip:
  the census that motivated this
  ([`nws_tag_census.py`](https://github.com/gasyoun/SanskritLexicography/blob/master/RussianTranslation/src/nws_tag_census.py),
  48,214 senses) ends by noting a reviewer deciding whether a tag is worth a facet
  needs its numbers. `facet_count_label` / `facet_reset_label` are translatable like
  `ui_strings`. The layer is additive string surgery on the same stable anchors as
  every other one — no `facets` key means a byte-identical pre-H1847 document, and
  `extras=False` refuses it outright.
- The facet click handler is registered *after* the core filter bar's, so the two
  writers to `card.style.display` compose (base filter ∩ facets) instead of fighting —
  the failure mode that would otherwise show a hidden card again on the next facet click.

### Fixed

- `review_sheet.__version__` had been left at `0.5.0` while the package moved to
  `0.6.0` — two disagreeing version strings in one distribution. Both now track the
  package version.

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
