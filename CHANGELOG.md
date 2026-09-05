_Created: 14-07-2026 · Last updated: 05-09-2026_

# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.24.0] - 2026-09-05

### Added

- **GitHub-backed packsets now state explicitly when the human is finished** (Codex `gpt-5.6-sol`, 05-09-2026; prompted by H4093 (Codex) — Portfolio roadmap renewal for revenue, Sanskrit research, and pedagogy). After hydration or a successful GitHub save, the sheet verifies that every expected `pack-NN.json` belongs to the current sheet and contains a decision for every item. Only then does it display “All {packs} packs received. Nothing more is expected from the human.” The terminal state is also localized in Russian; missing, partial, malformed, or foreign-sheet packs do not trigger it.

## [0.23.1] - 2026-09-05

### Fixed

- **“Save to folder…” can no longer leave a zero-byte decision export when the reviewer moves to the next pack quickly** (Codex `gpt-5.6-sol`, 05-09-2026; found during H4093 (Codex) — Portfolio roadmap renewal for revenue, Sanskrit research, and pedagogy). The file-picker path now writes immediately, serializes every later autosave, awaits both `write()` and `close()`, exposes `Saving…` / `Saved` / retry status, and raises the browser's navigation guard while a write is pending. Previously the picker created or truncated the target and only scheduled the first write one second later; leaving the page in that window cancelled the timer, while a blanket empty `catch` concealed the failure. Two regression tests cover immediate flush and pending-write navigation protection; the new status strings are part of `UI_STRINGS` and `RU_UI_STRINGS`.

## [0.23.0] - 2026-08-29

### Added

- **Every base-mode export now embeds a top-level `reviewedAt` vote stamp (H3697).** The base `exportPayload()` already wrote the browser-stamped export moment into `generated` — the S6 census (H3378) misread that key as the sheet build date, reported the vote leg of the round trip as unmeasured (0/23), and its «issued → applied» figures were actually vote → applied. From 0.23.0 the base payload captures one `nowIso` and writes it to both `generated` (byte-compatible for existing consumers) and `reviewedAt` (the key the census and strict mode already speak); the V16 inbox pack projection forwards `reviewedAt` so `merge_vote_packs.py`-assembled exports stay measurable. Strict exports are unchanged (`reviewedAt` stays the policy-gated vote time, `generated` the sheet build date). Forward-only: awaiting-vote sheets are never silently regenerated (LockCollision). Tests: `tests/test_review_sheet.py::test_base_export_embeds_reviewedat_export_stamp`, `tests/test_v16_packset.py::test_inbox_payload_carries_reviewedat`.

## [0.22.0] - 2026-08-21

### Added

- **`split_layout` (opt-in).** `config["split_layout"] = True` with `item["left"]` / `item["right"]` renders a two-column grid at full viewport width (`main` has no 980px cap), wraps `item["store_markup"]` in a closed `<details>`, and mirrors the **current** card's vote / rating / note into the existing V17 `#voteBar` (the clone forwards clicks and input to the hidden original, so localStorage and export stay bound to the card id). Independent column scroll, 900px stack (DE then RU), insertion-chip tooltip pin on tap. `extras=False` ignores the flag (donor fixture stays byte-identical). Missing `left`/`right` raises `ValueError`. Tests: `tests/test_split_layout.py`.

## [0.21.0] - 2026-08-18

### Added

- **V17 — voting ergonomics, from a real sitting (MG, 18-08-2026, after voting pack 1 of the 320-card gold set).** Four reports, every one about where the reviewer's eye already is.
  - **The submit controls were in the HEADER, above the work.** A reviewer finishes at the BOTTOM and had to scroll back up to hand in. They now ride in a `.votebar` **stuck to the bottom of the viewport** — "at the foot" without meaning "scroll 3 000 px to submit". Navigation (filters, facets, the type-scale control) deliberately stays on top, where it is used *before* deciding, and the ⏸ pause toggle stays beside the ⏱ chip it operates.
  - **No real progress bar at the top** — V15's was a 120 px chip in that same toolbar. A full-width bar now rides *inside* the sticky header. Injected before the toolbar it sat ~180 px down at rest, and two `sticky; top:0` elements cover each other on scroll; inside the header there is one pinned thing and no conflict.
  - **The ETA covered the current PAGE.** On a 32-pack sheet the reviewer's question is how long the WHOLE instrument takes at the pace they are going. Because every pack shares one `localStorage` record **and one timing record** (both keyed on `sheet_id`), any pack can count and time the whole sheet without loading another: `packset_total` is set automatically by `render_review_sheet_packset`, and the bar reads `{n} of {total} across the whole sheet` with `about {minutes} min left for all {total}`, marked rough under five timed cards.
  - **Auto-advance scrolled the next card to the viewport CENTRE**, so the card under judgement began half off the top. Now `block: 'start'` with `scroll-margin-top` clearing the sticky strips. Applied to the FINISHED document, never the core template — `extras=False` reproduces a pre-H779 shell byte-for-byte, and that fixture is what caught the first draft.
  - Four new `UI_STRINGS` keys (`vote_*`), all translated in `RU_UI_STRINGS`. Opt out with `config["vote_ux"] = False`, which leaves no identifier behind.

### Fixed (in the same layer, before release)

- **The relocation must not name a layer that is switched off.** The first draft listed control ids in JS, so a sheet without facets still carried `facetbar` and one without the inbox still carried `inboxBtn` — breaking the absence contracts V12/V15/V16 each rely on. Controls are now tagged `data-submit` **at build time, only when present**, and moved by attribute.
- **`VOTE_PROGRESS` reused V15's exact English default** (`decided {n} of {total}`), so translating one would silently rewrite the other. They are different readouts — V15's chip counts this pack, V17's bar the whole sheet — and now say so.

### Tests

- `tests/test_v17_vote_ux.py` — 24 cases incl. both absence directions, the donor-path exemption, and the V15 collision.
- `tests/fixtures/smoke_v17_vote_ux_browser.py` — 12 checks in headless Chromium against real geometry (bar at y≈110, submit pinned at the viewport foot, advanced card at y≈96, ETA reading «≈1 мин на все 22»). Needs `playwright`.

## [0.20.0] - 2026-08-18

### Added

- **Two more filter-bar chrome words `UI_STRINGS` never reached ([H2847](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2847-Sonnet_Uprava_review-sheet-explanations-russian-only-and-jargon-expansion_15.08.26.md)).** `_CORE_TEMPLATE` bakes `"all"` / `"unvoted only"` straight into the filter buttons, same class of gap as the `count_suffix`/`generated_label`/`doc_lang` fix in 0.18.0. New keys `filter_all`, `filter_unvoted`; `RU_UI_STRINGS` carries both (`"все"` / `"только непроголосованные"`).

## [0.19.1] - 2026-08-18

### Fixed

- **A stale agent worktree inside a repo made its sheets unbuildable ([H2991](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2991-Opus_csl-pyutil_vote-w3-packs-oauth_17.08.26.md)).** `EvidenceManifest.scan_prior_art()` walked the whole repo pruning only `.git` / `node_modules` / `__pycache__` / `review` — nothing that covers an agent's own scratch checkout. Two leftover worktrees under `SanskritLexicography/.claude/worktrees/` therefore turned the 500-card BLI gold sheet into a hard `PreflightError` with **13 blocking findings, every one a COPY of a file the manifest had already declared**. The sheet could not be regenerated at all, and the error blamed the sheet rather than the environment.
  - **A scratch checkout is not prior art — it is the same art seen twice.** The pruning list is now the named `_SCAN_SKIP_DIRS`, covering VCS internals, dependency trees (`node_modules`, `.venv`, `site-packages`, `.tox`), build outputs (`dist`, `build`, `.eggs`), caches, and agent/tool scratch areas (`.claude`, `.codex`, `.grok`, `.worktrees`, `.idea`, `.vscode`) alongside the existing `review`.
  - A repo that genuinely keeps evidence in one of those is misfiled, not mis-scanned — so this cannot hide a real artifact.
  - Regression test builds a real artifact plus four copies under scratch/dependency trees and asserts the real one is still found while none of the copies are.

## [0.19.0] - 2026-08-18

### Added

- **The vote pull says it is happening ([H2991](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2991-Opus_csl-pyutil_vote-w3-packs-oauth_17.08.26.md) follow-up).** V16 hydration is two network hops, and the second — `raw.githubusercontent.com`, once per decisions file — is routinely slow to settle, sometimes past 10 s, while the `api.github.com` listing answers in about one. Measured 18-08-2026 during the live smoke: the first hydrate test **failed on a 20 s ceiling against completely correct code**. For a reviewer the effect is worse than a slow page — an unvoted sheet silently fills in a few seconds later, which reads as a bug and invites them to start voting on top of votes that are about to land.
  - The inbox status line now shows `INBOX_PULLING` (**«подтягиваю голоса…»** under `RU_UI_STRINGS`, *pulling votes from GitHub…* in English) from **before** the first request, and replaces it with the existing pulled-N message on success.
  - A pull that brings nothing **clears the line** rather than leaving the hint up: every terminal path reports, including an empty directory, a directory with no `.json`, and an outright network failure.
  - The repaint (`save()` + `applyCardUI`) now runs only when something actually merged, instead of on every completion.
  - New `UI_STRINGS` key `inbox_pulling`, translated in `RU_UI_STRINGS`. Four tests, including that the announcement is emitted *before* the fetch rather than after it resolves.

## [0.18.0] - 2026-08-18

### Added

- **Five head/header chrome strings `UI_STRINGS` never reached ([H2847](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2847-Sonnet_Uprava_review-sheet-explanations-russian-only-and-jargon-expansion_15.08.26.md)).** `_CORE_TEMPLATE` bakes `"%(n)d items"` into both `<title>` and `<h1>`, `"Generated %(generated)s"` into the subtitle line, `lang="en"` onto `<html>`, and the `"all"` / `"unvoted only"` filter-bar buttons — none reachable via `title`/`subtitle`/`footer`/`approve_label`/`reject_label`/`filters`, so a fully card-translated Russian sheet still leaked English into the browser tab, the document's declared language, and the filter bar. New keys `count_suffix`, `generated_label`, `doc_lang`, `filter_all`, `filter_unvoted`; `RU_UI_STRINGS` carries all five (`"карточек"` / `"Собрано"` / `"ru"` / `"все"` / `"только непроголосованные"`). Regression tests, including one exercising the preset directly.

## [0.17.1] - 2026-08-18

### Fixed

- **The inbox `PUT` named a branch that does not exist ([H2991](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2991-Opus_csl-pyutil_vote-w3-packs-oauth_17.08.26.md)).** `github_inbox["branch"]` defaulted to `"main"`, and [`gasyoun/vote-inbox`](https://github.com/gasyoun/vote-inbox) is on **`master`** — so the first real Save to GitHub would have `404`ed against a branch that is not there. Nothing caught it in 0.17.0 because the whole write path is unreachable until an OAuth client_id exists, so the unit tests exercised the payload and never the branch. The default is now **empty, meaning "the repo's own default branch"**, which the contents API resolves itself; `?ref=` is likewise omitted from the pre-read unless a branch is named explicitly. Passing `branch` still works and still wins. Three regression tests.

### Changed

- **The device-flow relay exists, so the button is reachable.** The 0.17.0 note said token acquisition needed a CORS-capable relay; one now runs at `https://kosha.193.232.229.92.sslip.io/gh-device` (nginx `proxy_pass` + CORS headers, no new service and no `client_secret`). Set `github_inbox["device_url"]` to it. Verified in a real browser: a direct `fetch` to `github.com/login/device/code` fails with `TypeError: Failed to fetch` while the same page reads GitHub's genuine response through the relay. Registering an OAuth App is still a human step — GitHub exposes no API for it — and without a `client_id` the button stays disabled by design.

## [0.17.0] - 2026-08-18

### Added

- **V16 — packs of 10 sharing one record, plus the public vote inbox ([H2991](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2991-Opus_csl-pyutil_vote-w3-packs-oauth_17.08.26.md), W3 track B; plan [PLAN_UPRAVA_VOTE_PLATFORM_2026Q3.md](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_UPRAVA_VOTE_PLATFORM_2026Q3.md)).** A 320-card sheet is one HTML file and one sitting nobody finishes.
  - New entry point `render_review_sheet_packset(items, config, *, hub_name=None) -> {"parent", "packs"}`. `config["pack_size"]` (default **10**) splits a long sheet into `pack-NN.html` slices — 22 becomes 10+10+2 — under a parent index page carrying per-pack progress. `len(items) <= pack_size` returns `{"parent": None, "packs": [one sheet]}` **byte-identical to a plain `render_review_sheet`** call, so splitting a sheet that fits costs nothing and buys nothing.
  - **One `sheet_id` across parent and packs**, therefore one `STORE_KEY` per origin: pack 2 already knows what pack 1 decided, and the parent reads that same record. Each pack's own export still names only its slice, so a `decisions.json` describes exactly the cards that page could vote on.
  - **`config["github_inbox"]`** adds «Сохранить в GitHub» / **Save to GitHub**: each pack writes `decisions/<sheet_id>/pack-NN.json` to a public inbox repo (default `gasyoun/vote-inbox`) and hydrates from it on load, so a second machine resumes the same sitting. Scope is `public_repo` only; the inbox payload is **ids and verdicts**, never card text. A note ships only when it is ≤280 chars, carries no `<`, and is not the card's own question pasted back. Passing `client_secret`/`token`/`secret` in that mapping is a build error — the device flow needs no secret.
  - **`config["personal_data"] = True` removes the layer entirely** — no button, and no hydrate read either — whatever `github_inbox` says. The pack split still happens.
  - Six new `UI_STRINGS` keys (`inbox_*`), all translated in `RU_UI_STRINGS`.

### Known limitation

- **The device-flow login needs a CORS relay; GitHub will not serve it directly.** Measured 18-08-2026: `OPTIONS https://github.com/login/device/code` with `Origin: https://gasyoun.github.io` answers **404 with no `Access-Control-Allow-Origin`**, and the POST likewise carries none — a static page may send the device-code request but can never read the reply. This is GitHub hardening its OAuth endpoints against browser-based token theft, not an outage to wait out. The `api.github.com` half is unaffected and works today: the hydrate GET answers `Access-Control-Allow-Origin: *` and the contents `PUT` preflight answers `204` allowing `Authorization`. So B3 and the write itself are live; only **token acquisition** needs a relay that forwards to github.com and echoes CORS headers, named in `github_inbox["device_url"]`. Until BOTH `client_id` and `device_url` are set the button ships **disabled with an honest tooltip** rather than as a control that cannot succeed — and the pack layer ships regardless, per the handoff's "missing OAuth App is not a stop" fence.

### Tests

- `tests/test_v16_packset.py` — 50 cases: the 10/11/22 split contract, the byte-identical single-pack path, shared `sheet_id`, per-pack id scoping, parent progress metadata, the inbox enable rule, secret refusal, the `personal_data` blackout, note hygiene, `exportPayload()` reuse (never re-emitting the `note: rec.note || ''` literal), no `typeof` neighbour probes, RU coverage, and `node --check` over six layer combinations.
- `tests/fixtures/build_v16_packset_demo.py` builds the 22-card acceptance fixture; `tests/fixtures/smoke_v16_packset_browser.py` drives it in headless Chromium over HTTP (one origin, as on the hub) and asserts the acceptance sentence — voting pack 1 leaves pack 2 unvoted while the parent reads 10/22 and 1 of 3 packs done. **21/21 green 18-08-2026.** Requires `playwright`, which is not a package dependency.

## [0.16.0] - 2026-08-18

### Added

- **U7 — typology / classification labels must carry their count and population share ([H2846](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2846-Sonnet_Uprava_review-sheet-typology-requires-statistics-standard_15.08.26.md), new universal row in [`docs/REVIEW_SHEET_CONTENT_STANDARD_2026.md`](https://github.com/gasyoun/Uprava/blob/main/docs/REVIEW_SHEET_CONTENT_STANDARD_2026.md)).** MG, reviewing the v2 re-glue card: «typology always needs to be supported by statistics, make it a general rule» — the card asked a reviewer to approve a typology whose distribution (1,534 restatements · 250 additions · 1 correction, ≈86% of everything glued onto PWG is PW abridging what PWG already said) was invisible on the card; a label with no denominator invites the reader to over-weight the rare class.
  - New opt-in item field ``item["typology"] = [{"label", "n", "share"}, ...]`` (or ``"share_unknown": True``), rendered as ``.badge-typology`` chips distinct from plain ``badges`` — e.g. `restatement (n=1534, 86%)`. Omitting ``n`` or ``share`` raises ``PreflightError`` at build time (``_check_typology_stats``, same call site as V10/V13); items with no ``typology`` key are unaffected.
  - Tests: `tests/test_typology_stats.py` (7 cases: renders label+count+share, `share_unknown` text, and a raise per missing field).
  - Released as a **minor**: a new opt-in structural gate + rendering path, not a bugfix.

## [0.15.0] - 2026-08-17

### Added

- **`csl_pyutil.integrity_tripwire` — a committed checksum + key-set on human-reviewed overlay data, red in CI when a writer wipes it ([H2891](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2891-Opus_csl-pyutil_q7-integrity-tripwire-checker_16.08.26.md), wave 1 of the Q7 data-integrity programme; census [H2890](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2890-Opus_Uprava_q7-integrity-census-contract_16.08.26.md)).** Three stores have each lost human review work to an automated writer that left a file which still parsed, still had roughly the right row count, and still passed CI: csl-atlas's `build-r2-checkpoint-review.mjs --reseed` skips `loadPreserved` and resets every human ruling; eleven WhitneyRoots `scripts/dcs/apply_*.py` writers open `src/app_data.json` with `'w'` and no lock, no reviewed gate and no backup; and pwg_ru's `run_batch.py` — the very code that *creates* the reviewer stamps — rewrites the 26 MB gitignored store with no lock and no `--override-reviewed`. In every case the loss was silent for months. This module is the thing that was missing: something watching.
  - **The gate is a projection, not the file.** Only the census key fields plus the census reviewed fields of the rows a store's predicate calls reviewed. A reformat, a row reorder, an added field elsewhere, or an edit to unreviewed content is invisible; a dropped `reviewer` stamp is not. A whole-file SHA-256 was tried first and cried wolf — H2153 saw pwg_ru shrink **1.29 MB at an identical row count** from a serializer change — and a gate that is red for benign churn is a gate that gets ignored.
  - **Two digests, because one catches half the failures.** `overlay_sha256` answers *did the reviewed content change* (an overwrite in place leaves the key set untouched); `keyset_sha256` answers *did the reviewed row set change* (a deletion leaves surviving content untouched).
  - **Row order is deliberately NOT part of the digest.** Every writer in all three stores rewrites wholesale and several reorder as a side effect. Reviewed rows are proven key-unique at extract time, so sorting them cannot fold two rulings into one.
  - **The predicate is data, not code** — it rides in the `spec` block of each consumer's pin, copied from the org census, because the three stores share no review stamp and the census repo is private to CI. pwg_ru: `reviewer` / non-`ai_` `review_status` / any `editorial_decision*`. csl-atlas: `reviewStatus` in `{reviewed-ok, reviewed-corrected}` **and** a human `reviewer` — H1684, since 137 of its 147 status-reviewed rows are agent-attributed and the status half alone over-claims human review **14.7×**. WhitneyRoots: no per-row stamp exists, so reviewed-ness is file-level.
  - **Key collisions refuse loudly.** The live pwg_ru key `(key1, subcard, sense_tag)` collides on 573 of 11,603 rows and is collision-free only over the 5 rows reviewed today; a future reviewed row landing in a collision group would make a row substitution invisible to the key-set digest, so `extract` raises rather than pinning a digest it cannot defend.
  - **Gitignored stores commit a derived extract.** `--extract` writes the reviewed projection as canonical JSONL so CI can check a store it is not allowed to see. The live bytes never enter git — and `redact_fields` is what makes that true rather than merely intended. pwg_ru's `human_review` is a reviewed field whose wipe is exactly what this module watches for, but it holds the curator's verbatim free-text notes, and the extract lands in a **public** repo while the store is gitignored precisely because its bytes are unpublished. Redaction replaces the value with `sha256:<hex>` of itself in the projection — identically on both the live-store and committed-extract paths, so the digests still agree — keeping every wipe detectable while publishing nothing. Caught during execution: the first real extract carried five reviewer notes verbatim, several hundred words of unpublished Russian editorial prose. Redaction is not applied twice when checking from an extract, and a key field may not be redacted (the key set must stay legible).
  - **Exit codes are three, not two:** `0` match, `1` tripwire, `2` broken spec — a spec/data mismatch must not be able to look like a clean store, and must not be able to look like a wipe either.
  - The acknowledgement ritual is one commit: regenerate the pin beside the change and write a one-line `reason`. No sign-off file, no second human. Auto-refreshing the pin would make the tripwire a changelog.
  - Public API `project` · `overlay_digest` · `keyset_digest` · `is_reviewed` · `extract` · `check`, exported from `csl_pyutil`; CLI `--check` / `--extract`.
  - Tests: `tests/test_integrity_tripwire.py` (47 cases) against synthetic scale models of the real incidents in `tests/fixtures/integrity/` — preserve-rebuild green, reviewed-field overwrite red, key-set shrink red, pin-bump green, atlas `--reseed` red, plus two **mutation** tests that fail if the contract is ever narrowed: one proves a hasher without `review_status` returns the *same* digest for a clean store and an overwritten one, the other proves an atlas predicate without the H1684 human-identity half over-claims. No existing test was modified — the suite goes 173 → 220 green.
  - Released as a **minor**, not the patch the implementation doc named: that instruction was written against a stale 0.10.0 clone, and a new exported public module is a feature under the SemVer this changelog claims to follow.

## [0.14.0] - 2026-08-16

### Fixed

- **The clock did not stop on export — the semantics were inside out ([H2887](https://github.com/gasyoun/Uprava/blob/main/handoffs/H2887-Opus_csl-pyutil_review-sheet-v14-clock-stop-misvote-fix-voting-ux_16.08.26.md)).** MG, curating the private sheet 16-08-2026: «Когда я сохраняю решения, таймер должен останавливаться. Сейчас этого не происходит.» V12 ([H2858](https://github.com/gasyoun/Uprava/blob/main/handoffs/archive/H2858-Opus_csl-pyutil_review-sheet-partial-submit-pause-timer_15.08.26.md)) wrote `__timePauseSet(true)` into the `handinBtn` handler **only**, so the PARTIAL exit («Hand in what I got») stopped the clock and the FULL one («Download decisions.json», the `strict_review` variant, the file-picker) did not — one `setInterval`, zero `clearInterval` in every published sheet.
- **Silent misvote — vote-data corruption nobody had reported.** `a`/`r`/`d` targeted `vis[activeIdx]`, and `activeIdx` moved on **arrow keys only**: no scroll handler, no focus ring. Scroll to card 40 with the mouse, press `a`, and the vote landed on whatever card the arrows last pointed at, off-screen, with no warning — while V11's clock billed the time to the card at the viewport centre (`__timeActiveId()`). Two layers disagreeing about "the current card" is how a vote silently lands on the wrong row. Both defects lived in the canonical emitter on `main`, so **every** sheet ever built carried them.

### Added

- **V15 session flow — the voting-session layer (`config["session_flow"]`, `extras=True` only, default ON).** The opt-out layer that fixes both defects above and adds the rhythm the same `/ask` interview asked for (12 forks closed 16-08-2026; wave W1.5 of [PLAN_UPRAVA_VOTE_PLATFORM_2026Q3.md](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_UPRAVA_VOTE_PLATFORM_2026Q3.md), step layer [IMPLEMENTATION_UPRAVA_VOTE_PLATFORM_W15.md](https://github.com/gasyoun/Uprava/blob/main/docs/IMPLEMENTATION_UPRAVA_VOTE_PLATFORM_W15.md)):
  - **Pause is a STATE, not a boolean.** `running` / `manual` / `export` / `idle`, persisted as `pause_reason` beside `paused` in the same `TIME_KEY` record, so it survives a closed tab. A record written before this layer has no reason and is read back as **manual** — a curator who paused yesterday must not find the clock restarted itself overnight.
  - **Every export gesture stops the clock** (Download, Save to folder…, Hand in what I got), caught in the capture phase on `document` so it also covers the strict handler, which `stopImmediatePropagation()`s on its own element. The debounced background autosave writes are deliberately **not** treated as exports: they fire after every vote, so pausing there would freeze the clock for the whole sitting.
  - **Auto-rearm on continued voting** — a vote, a note edit, a keypress, a pointer press or a scroll lifts an `export`/`idle` pause. A **manual** pause always wins and is never lifted automatically.
  - **90 s idle auto-pause** (`FLOW_IDLE_SECONDS`, a named constant beside the layer), the largest source of inflated review time.
  - **One current card** shared by the clock and the keys — V11's own `__timeActiveId()` when the clock is on, the same nearest-to-viewport-centre rule written out when it is not — kept in step by a throttled (120 ms) scroll handler, marked with a visible `.card.kbd-active` ring, and re-derived after any filter/facet click (both bars reset `activeIdx` to 0 as they re-filter, which is how the defect would otherwise return wearing a filter).
  - **Rhythm:** auto-advance to the next undecided card after a vote · undo (`z` or the ↶ button) restoring the previous decision including "there was none", never touching the clock · a progress bar with a median-seconds-per-card ETA, marked rough until five cards are decided · resume at the first undecided card on load, with a toast · the clock chip naming which of the three states it is in.
  - 12 new `UI_STRINGS` keys (`flow_*`), all present in `RU_UI_STRINGS`, placeholders (`{n}`/`{total}`/`{minutes}`/`{id}`/`{decision}`) preserved.
  - Named **V15**, not the plan's "V14": the export-context layer shipped as V14 the same day, so this build takes the next free slot per the plan's ambiguity contract — the same move H2854 made when H2858 had already taken V12.
  - Written under the two constraints H2858 paid for: no `typeof` probe of a neighbouring layer (every clock-touching line is emitted only when `config["timing"]` is on, every `__pauseShow()` call only when `config["hand_in"]` is on too, and `facetbar` is named only when that layer exists — three tests assert those identifiers are ABSENT from the document), and no repeat of the shared `note: rec.note || ''` literal that `_add_timing` rewrites. This layer produces no export payload at all, so it carries neither that literal nor V14's `sheet_id: SHEET_ID,` replace-all target.
  - Tests: `tests/test_v15_session_flow.py` (43 cases, including `node --check` of the emitted script in six layer combinations: plain · timing_off · strict · rating+labels · everything · session_flow_off). No existing test was modified — the suite goes 130 → 173 green.

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

_Dr. Mārcis Gasūns_
