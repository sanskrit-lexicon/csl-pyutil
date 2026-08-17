# csl-pyutil

_Created: 14-07-2026 · Last updated: 17-08-2026_

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
        # Optional: make final exports publication-review admissible.
        "strict_review": {
            "reviewer": "gasyoun",
            "require_all_votes": True,
            "require_reject_note": True,
        },
    },
    # Required when extras=True (default) since v0.8.0 / H1649:
    screening={
        "deterministic": 0,
        "lookup": 0,
        "agent": 0,
        "human": 43,
        "evidence_path": "review/screening_evidence.md",
        "rules": ["none"],  # or the real rule names applied
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

With `strict_review`, the same payload gains additive top-level fields:

```json
{"sheet_id": "...", "generated": "2026-07-14", "decided": 12,
 "reviewer": "gasyoun", "reviewedAt": "2026-07-17T20:45:00.000Z",
 "complete": true,
 "items": [{"id": "L142", "decision": "approve", "note": ""}, ...]}
```

Partial File System Access API auto-saves use `complete: false` and
`reviewedAt: null`. Final download is blocked until the reviewer is non-empty,
every item is voted, and every rejected item has a note. Callers that omit
`strict_review` retain the 0.1.x behavior and byte-identical core rendering.

See [`csl_pyutil/review_sheet.py`](csl_pyutil/review_sheet.py) for the full
item/config schema docstring.

### Presentation (0.5.0)

`config["font_scale"]` multiplies the whole type scale and **defaults to 1.5** —
MG's "+150%", ruled 28-07-2026 while voting the G5 sheet, together with a fix to
the inherited hierarchy: the panel `<pre>` holding the text under judgement used
to be the smallest type on the page. An A−/A+ toolbar control re-points the scale
per browser. `font_scale=1` restores the donor sizes; `extras=False` never gets
the layer, so the byte-identical fixture stands.

`config["extra_css"]` appends caller CSS last in the cascade.

### The evidence gate — V9 / V10 (0.9.0)

V1–V8 are entirely about *presentation*. A sheet can be green on every one of them
and still ask a human to re-derive, by eye, a conclusion the repo already holds on
disk — measured 29-07-2026 on the sheet that prompted this: **191 of 200 cards**
already carried a machine verdict, a named rule and cited evidence computed from
the same inputs, none of it rendered, and **69 of 200** were not disagreements at
all. So the emitter now refuses to write those sheets.

```python
from csl_pyutil import EvidenceManifest, render_review_sheet

man = EvidenceManifest(sheet_id=SHEET_ID, row_ids=[i["id"] for i in items],
                       repo_root=REPO)
man.declare_joined("research/adjudication.tsv", ["verdict", "rule", "reason"])
man.declare_omitted_path("research/superseded_run.tsv",
                         because="superseded by the H1681 rerun, kept for audit")
man.declare_omitted("DCS attested sentence",
                    because="no per-compound sentence map exists; only sense-level")
for it in items:
    man.add_card(it["id"], evidence_fields=["verdict", "rule"])

html = render_review_sheet(items, config, screening=..., manifest=man)  # raises, or returns
```

**V9 — evidence reuse.** With `manifest=`, [`preflight()`](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/csl_pyutil/evidence.py)
runs against the *finished* document (after `ui_strings`, so it sees exactly what the
reviewer sees) and raises `PreflightError` before a byte is returned: undeclared
prior art keyed on the same row ids, cards under the evidence floor with no stated
reason, Cyrillic/IAST mixed inside one word, SLP1 leaking into human-facing text,
and structurally impossible sūtra citations. Tune it with `config["preflight"]`
(`allow_slp1_tokens`, `overlap_threshold`, `skip_prior_art`). Without `manifest=`
you get a `PreflightWarning` naming the reason — a migration ramp for the pre-0.9.0
generators that **becomes an error in 1.0.0**; escalate it today with
`-W error::csl_pyutil.evidence.PreflightWarning`.

**V10 — no non-decisions.** `config["non_decision_share"]` is the largest fraction
of cards the sheet may carry that your own pre-filter already resolved, marked per
card as `item["machine_resolvable"] = True`. The caller classifies (only it knows its
domain); the emitter enforces. It **defaults to 0.0** — a card the machine has
answered does not belong on a human's plate — and a sheet with no flagged item is
unaffected.

Two asymmetries in the gate are deliberate and load-bearing: a conceptual
`declare_omitted()` can never silence a real file the scan found (only
`declare_omitted_path()` can), and the SLP1 detector stays **silent** on the
undecidable all-lowercase case (`agni + deva` is byte-identical in SLP1 and IAST)
rather than guessing.

## `anatomy` — colour-coded CDSL raw markup

```python
from csl_pyutil import anatomy

panel_body = anatomy.highlight(raw_record, target="As")     # tinted, markup still visible
legend     = anatomy.legend_html(parts=["sanskrit", "gloss", "citation"])
```

A raw CDSL record dumped verbatim into a review card is a wall of punctuation.
`highlight()` keeps every tag **visible** — the tags are the anatomy — but dims the
delimiters and colours each payload by part class (Sanskrit form · gloss · citation ·
grammar · abbreviation · cross-reference · etymology · homonym), outlining any form
equal to `target`. Written for csl-atlas's xref sheet (H1646), moved here under H1808
when a second generator needed it; csl-atlas's `scripts/lib/cdsl_anatomy.py` is now a
re-export shim so there is one canonical copy.

Hooks for what a shared module cannot know:

| Argument | Use |
|---|---|
| `tag_parts={"ab": "crossref"}` | override the tag → part map (PWG wraps *every* abbreviation in `<ab>`; an xref sheet wants the brighter class) |
| `plain_hook(text)` | reach text the markup does not delimit — NWS-layer cards carry citations as bare text with no `<ls>` around them |
| `payload_hook(part, inner, attrs)` | render a tagged payload yourself, e.g. `<ls>` as a Cologne source link |

The sheet's naming, placement (gitignored `review/`), GTD `@DO` line, and
`Uprava/REVIEW_SHEETS_INDEX.md` registration are still the caller's job — this
function only produces the HTML string. See
[`~/.claude/commands/review-sheet.md`](https://github.com/gasyoun/claude-config/blob/main/commands/review-sheet.md)
for the full process.

## `integrity_tripwire` — a committed checksum on human-reviewed data

```sh
python -m csl_pyutil.integrity_tripwire --check   --pin data/integrity/<store>.pin.json
python -m csl_pyutil.integrity_tripwire --extract --pin data/integrity/<store>.pin.json \
       --write-pin --reason "what changed and why"
```

Three repos have each lost human review work to an automated writer that left a
file that still parsed: csl-atlas's `--reseed` drops every preserved ruling,
eleven WhitneyRoots `apply_*` scripts open `src/app_data.json` with `'w'` and no
lock, and pwg_ru's own review-applying script is unlocked and un-gated. Nobody
noticed for months, because nothing was watching. This module is what watches.

It hashes a **projection** — only the key fields and the reviewed fields of the
rows a store's predicate calls reviewed — so a reformat, a reorder, or an edit
to unreviewed content is invisible, and a dropped `reviewer` stamp is not. A
whole-file SHA-256 was tried first and cried wolf (a 1.29 MB serializer shrink
at an identical row count), which is how it came to be ignored. Two digests:
`overlay_sha256` for *did the reviewed content change*, `keyset_sha256` for
*did the reviewed row set change* — an in-place overwrite moves only the first,
a deleted row only the second.

The rule for "a row is reviewed" is **data, not code**: it lives in the `spec`
block of each pin, copied from the org census, because the three stores share no
review stamp. pwg_ru has `reviewer`/`review_status`/`editorial_decision*`;
csl-atlas needs `reviewStatus` **and** a human `reviewer` (137 of its 147
status-reviewed rows are agent-attributed, so status alone over-claims human
review 14.7×); WhitneyRoots has no per-row stamp at all and is reviewed
file-level.

CI runs `--check` and **fails** on a mismatch. A legitimate change regenerates
the pin in the same commit with a one-line `reason` — that is the whole
acknowledgement ritual. Exit codes: `0` match, `1` tripwire, `2` broken spec
(a defect must not be able to look like a clean store).

Gitignored stores (pwg_ru's live 26 MB JSONL) commit a derived `--extract`
projection instead, so CI can check what it cannot see. The live bytes never
enter git: `redact_fields` names reviewed fields whose value is replaced by
`sha256:<hex>` of itself, so a field like pwg_ru's `human_review` — the
curator's verbatim free-text notes, watched precisely because a wipe of it is
the failure mode — stays fully covered by the digest while publishing nothing
into a public repo. The hash moves the instant a single character does.

## Tests

```sh
pip install -e . pytest
pytest tests -q
```

`tests/fixtures/` holds 100%-synthetic placeholder content generated only
through the donor's own render functions — never real translation data (the
donor's own gitignored/unpublished pwg_ru store must never land in this
public repo).
