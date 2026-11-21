# AGENTS.md — csl-pyutil

_Created: 13-09-2026 · Last updated: 21-11-2026_

## Tool manifest

- Purpose: shared Python utility library for the Cologne/CDSL repos
  (`csl_pyutil` package, `pyproject.toml`, offline tests in `tests/`).
- Harnesses: Claude Code ([CLAUDE.md](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/CLAUDE.md)),
  Codex/OpenCode/Grok (this AGENTS.md) — org default all four.
- CI: [ci.yml](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/.github/workflows/ci.yml) +
  [dependabot-auto-merge.yml](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/.github/workflows/dependabot-auto-merge.yml).
- Repo-level MCP: none carried (no `.mcp.json`); estate MCP wiring is
  machine-level (opencode: uprava-recall; claude: uprava-recall + repowise).
- Landing route: PR-first; green PRs auto-merge (MG 21-11-2026: «human merges
  only in csl-orig and some other cologne properties, all other always
  automerge»). Human-merge exceptions live in Uprava
  `data/drain_repo_allowlist.json` → `foreign_human_merge`; this repo is not on
  it. csl-orig is the org-wide fence.
- Census: tracked by [module-spread census v2](https://github.com/gasyoun/Uprava/blob/main/data/module_spread_census_v2.json)
  (`mcp_config` marker, H4525).

_Dr. Mārcis Gasūns_
