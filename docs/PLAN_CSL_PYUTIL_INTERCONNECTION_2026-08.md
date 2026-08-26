# Plan — csl-pyutil interconnection, 2026-08

_Created: 26-08-2026 · Last updated: 26-08-2026_

csl-pyutil's slice of the spine-interconnection programme. Programme index:
[PLAN_SPINE_INTERCONNECTION_2026H2.md](https://github.com/gasyoun/Uprava/blob/main/docs/PLAN_SPINE_INTERCONNECTION_2026H2.md).

Architecture and verification are **not** restated here (ruling F13) — they are identical for
all fourteen repos and live once in Uprava:

- [ARCHITECTURE_SPINE_INTERCONNECTION.md](https://github.com/gasyoun/Uprava/blob/main/docs/ARCHITECTURE_SPINE_INTERCONNECTION.md) — the five attachment points and the rules governing them
- [IMPLEMENTATION_SPINE_INTERCONNECTION_W1.md](https://github.com/gasyoun/Uprava/blob/main/docs/IMPLEMENTATION_SPINE_INTERCONNECTION_W1.md) — execution order, per-handoff steps, isolation, risks
- [VERIFICATION_SPINE_INTERCONNECTION.md](https://github.com/gasyoun/Uprava/blob/main/docs/VERIFICATION_SPINE_INTERCONNECTION.md) — the five gates and what "done" means

**Nothing here has executed.** The handoff below is 🟡 queued and runs only when a human
launches it.

## Why csl-pyutil is in scope

Zero PROJECT_INTERLINKS rows while shipping `review_sheet` at v0.22.0 with an active merged-PR stream — it is the emitter the `/review-sheet` skill depends on. The ledger already carried the open action to verify this before wiring an edge; the verification was done 26-08-2026 and passed.

## Measured baseline and target

| | Value |
|---|---|
| Wiring score, 26-08-2026 | **28** / 100 |
| Target after this plan | **36** / 100 |
| How the target is reached | +6 for the `CLAUDE.md`, ~+2 once the sibling handoff registers the edge. |

Measured by [`tools/interconnection_audit.py`](https://github.com/gasyoun/Uprava/blob/main/tools/interconnection_audit.py); full row in
[data/interconnection_audit_2026-08-26.json](https://github.com/gasyoun/Uprava/blob/main/data/interconnection_audit_2026-08-26.json);
report [AUDIT_REPO_INTERCONNECTION_2026-08-26.md](https://github.com/gasyoun/Uprava/blob/main/docs/AUDIT_REPO_INTERCONNECTION_2026-08-26.md).

The score counts artefacts, not whether they are true. It is **report-only** by ruling F2 and no
handoff closes on it — verification Gates 2 to 4 are what actually decide, and Gate 4 is read by
a human.

## Rulings that apply here

| Fork | Ruling |
|---|---|
| F10 | The csl-pyutil `review_sheet` edge is real and unregistered; it is registered without a vote. |
| F1 | Local `FINDINGS.md` in exactly four repos; the other eight get a `CLAUDE.md` pointer line. No repo gains the other seven registries. |

Full rulings table with every fork:
[ASK_BATCH_STAGING_REPO_INTERCONNECTION_2026-08.md](https://github.com/gasyoun/Uprava/blob/main/ASK_BATCH_STAGING_REPO_INTERCONNECTION_2026-08.md) Phase 2.

## What this plan does

1. Create a short `CLAUDE.md` carrying the FINDINGS routing pointer plus one line stating this package is generic non-Sanskrit Python helpers, distinct from `sanskrit-util` which owns Sanskrit string and transcoding work (F1).
2. No registry files, no `.ai_state.md`.
3. The edge itself is registered by the sibling Uprava handoff H3575 (F10); the two can run in either order.

## Handoff

- [H3573 (Sonnet 5) — interconnect cslpyutil claudemd findings pointer](https://github.com/gasyoun/Uprava/blob/main/handoffs/H3573-Sonnet_csl-pyutil_interconnect-cslpyutil-claudemd-findings-pointer_26.08.26.md) · trivial · 🟡 queued

## Autonomy contract

The launching agent may create the files named above, add hub rows, open and merge its PR,
remove its worktree and close its handoff row — without asking.

It must stop and ask if a local `FINDINGS.md` cannot be given two genuine findings (the
documented fallback is to drop the file and take the pointer line, recorded not silent), if a
corpus row would carry an unmasked snapshot or quote a sample, or if a second speculative edge
becomes necessary. It must never turn the wiring score into a failing gate, commit to
`csl-orig`, or add the seven non-FINDINGS registries.

## Open @DECIDE

None. Every fork touching csl-pyutil was ruled in sitting 1 on 26-08-2026, so the autonomy gate
passes and nothing in the wave-1 path stalls on a human.

_Dr. Mārcis Gasūns_
