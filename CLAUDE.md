# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

Zentra is a collection of security skills for AI coding agents (Claude Code and OpenCode). There is no application to run or tests to execute — this is a **skill library**. Each skill is a markdown file (`SKILL.md`) that defines an AI agent persona, its workflow phases, grep patterns, and output format.

## Repo Structure

```
skills/
  zentra-<name>/SKILL.md   # One skill per folder — this is all the code
.opencode/
  commands/                 # OpenCode slash-command wrappers (one per skill)
  agents/                   # OpenCode agent definitions
install.sh                  # Unix installer — symlinks skills into ~/.claude/plugins/zentra
install.ps1                 # Windows installer — same logic via PowerShell
opencode.json               # OpenCode config (MCP: Playwright for pentester)
AGENTS.md                   # Agent-facing docs (shown to AI in OpenCode sessions)
```

## The Pipeline

Skills are designed to run in order, sharing state via `.zentra/` in the target project:

```
zentra-threat-model → zentra-code-recon ─┐
                       zentra-iac-scan   ├→ zentra-pentester → zentra-remediate → zentra-compliance → zentra-report
                       zentra-supply-chain┤
                       zentra-api-scan   ┘
```

`zentra-dev` is standalone — lightweight, no file output, scans only git-changed files.

## Shared State Contract

All pipeline skills (except `zentra-dev`) read and write to `.zentra/` in the scanned project:

- `config.json` — created by whichever skill runs first; stores target path, stack, exclusions. All downstream skills read this before doing anything.
- `detailed-findings.md` — append-only across all scanners. Each scanner adds its findings; pentester and remediate read from it.
- `scan-summary.md`, `recommendations.md` — updated by scanners.
- `threat-model/`, `evidence/`, `remediation/`, `compliance/`, `reports/` — owned by specific skills.

**Key invariant:** Every pipeline skill starts with "read `config.json`; if missing, create it (following zentra-code-recon's intake process)." This makes each skill independently runnable.

## Installing / Updating

```bash
# Unix
bash install.sh

# Windows
.\install.ps1
```

The installer symlinks `skills/zentra-*/` into `~/.claude/plugins/zentra` (Claude Code) and `~/.config/opencode/skills/` (OpenCode). Changes to SKILL.md files are live immediately — no reinstall needed unless the skill folder itself was added or removed.

## Adding a New Skill

1. Create `skills/zentra-<name>/SKILL.md` with YAML frontmatter (`name`, `description`) and the skill body.
2. Add a corresponding `.opencode/commands/zentra-<name>.md` for OpenCode slash-command support.
3. Update `README.md` skill table and pipeline diagram.
4. Update `AGENTS.md` skill table.

Skill frontmatter format:
```yaml
---
name: zentra-<name>
description: "One sentence — shown in skill picker UI."
---
```

## Skill Authoring Conventions

- **Phases** are numbered (Phase 1: Intake, Phase 2: Scan, etc.) — keep this consistent.
- **Subagents** are spawned via the `Agent` tool in parallel when the codebase is large (>200 files) or multi-stack. Always send independent agents in a single message.
- **Output** always goes to `.zentra/` in the target project, never in this repo.
- **Safety gates**: pentester requires explicit user authorization before any dynamic requests. Remediate requires per-patch approval.
- **False positive reduction**: after grep matches, read 30 lines of surrounding context before reporting a finding.
- Severity levels: Critical → High → Medium → Low (defined in zentra-code-recon and reused across all scanners).

## Platform Targets

| Platform | Skill delivery | Config |
|----------|---------------|--------|
| Claude Code | Plugin symlink at `~/.claude/plugins/zentra` | — |
| OpenCode | Per-skill symlinks at `~/.config/opencode/skills/` + commands/agents copied | `opencode.json` |
| Cursor IDE | MDC rules copied to `~/.cursor/rules/` | — |
| Codex CLI | Skill files in `~/.codex/zentra/` + section appended to `~/.codex/AGENTS.md` | — |

Playwright MCP is configured in `opencode.json` for `zentra-pentester`. Claude Code users install it separately (`npx @playwright/mcp@latest`).
