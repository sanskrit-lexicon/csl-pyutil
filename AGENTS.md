# AGENTS.md — csl-pyutil

_Created: 13-09-2026 · Last updated: 13-09-2026_

## Tool manifest

- Purpose: shared Python utility library for the Cologne/CDSL repos
  (`csl_pyutil` package, `pyproject.toml`, offline tests in `tests/`).
- Harnesses: Claude Code ([CLAUDE.md](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/CLAUDE.md)),
  Codex/OpenCode/Grok (this AGENTS.md) — org default all four.
- CI: [ci.yml](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/.github/workflows/ci.yml) +
  [dependabot-auto-merge.yml](https://github.com/sanskrit-lexicon/csl-pyutil/blob/main/.github/workflows/dependabot-auto-merge.yml).
- Repo-level MCP: none carried (no `.mcp.json`); estate MCP wiring is
  machine-level (opencode: uprava-recall; claude: uprava-recall + repowise).
- Landing route: foreign owner `sanskrit-lexicon` → PR only, human merges
  (no auto-merge).
- Census: tracked by [module-spread census v2](https://github.com/gasyoun/Uprava/blob/main/data/module_spread_census_v2.json)
  (`mcp_config` marker, H4525).

_Dr. Mārcis Gasūns_
