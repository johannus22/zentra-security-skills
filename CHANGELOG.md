# Changelog

## [3.2.0] - 2026-11-16

### Added
- A self-contained offline release installer ZIP with a Windows double-click launcher, macOS/Linux launcher and all 14 skills bundled in a portable Python application.
- Native-skill installation for Claude Code, Codex, Cursor and OpenCode alongside Pi, DeepSeek Harness, Kimi Code, Gemini CLI, Qwen Code and shared Agent Skills.
- Interactive harness selection, unattended installation flags and checksums for the ZIP, Python application and existing package.
- Offline installation, launcher, resource-lifetime and archive-validation regression tests.

### Changed
- Getting started now begins at GitHub Releases and requires no repository clone, Git, npm or network connection during installation; Python 3.11+ remains required.
- Release packaging builds and uploads the offline installers with every versioned release.

## [3.1.0] - 2026-11-16

### Added
- Native Pi, official DeepSeek Harness, Kimi Code, Gemini CLI and Qwen Code installation targets, plus a shared Agent Skills target.
- A standard-library Python installer with user/project/custom roots, environment overrides, dry runs, full resource copying and ownership-hash checks that preserve local edits.
- Explicit Bash/PowerShell targets and native harness discovery in interactive menus.
- Pi package metadata exposing the canonical skills without executable extensions.
- Harness compatibility documentation and isolated installation/update regression coverage.


## [3.0.0] - 2026-11-16

### Added
- Canonical VERSION file, synchronized semantic version tooling and changelog-derived release notes.
- GitHub validation and draft release workflows with tag/version checks, packaged assets and SHA-256 checksums.
- `zentra-secure-code`: secure implementation patterns, explicit security invariants and positive/abuse-case verification.
- `zentra-verify`: fresh adversarial/final reviews, candidate dispositions, versioned evidence records and a standard-library Python acceptance gate.
- `zentra-web-audit`: browser security, WCAG 2.2, supported-browser fallbacks and measured performance checks.
- Strict source/receipt/review-digest checks, selected audit control inventory, coverage tracking and fail-closed exit codes; isolated regression tests.
- Generated platform adapters/resources and framework consistency checks, including installer delivery of validator resources to flat legacy adapters.

### Changed
- Release metadata and installation links now target johannus22/zentra-security-skills; the remote Apache-2.0 license is retained alongside the original MIT notice.
- Updated source risk taxonomy to OWASP Top 10:2025 and secure coding guidance to ASVS 5.0.0; retained explicitly versioned API Top 10:2023.
- Scanners produce candidates for independent verification; only one coordinator publishes shared pipeline artifacts.
- Tool/provider failures and missing required coverage remain incomplete; zero findings cannot bypass overall evidence review.
- Remediation requires behavioral regression evidence and fresh review; grep disappearance never verifies a fix.
- Audits require affirmative evidence and distinguish satisfied, unsatisfied, not_assessed and not_applicable; reports no longer infer compliance from absent findings or discount unverified fixes.
- Dev review includes staged/unstaged/untracked files, HTML/CSS, lockfiles and configuration; removed unverified hook API examples.

### Migration
- Legacy Markdown findings must be reverified before strict acceptance. Verification v1 is a skill-pack protocol, not the separate zentra-cli wire format or runtime enforcement.


## [2.1.0] — 2026-04-22

### Added
- **OpenCode support** — Zentra now works as a first-class plugin on both Claude Code and OpenCode
- `opencode.json` — OpenCode plugin configuration with Playwright MCP reference
- `AGENTS.md` — OpenCode instructions file with pipeline overview and skill reference
- `.opencode/commands/` — 11 slash commands (`/zentra`, `/zentra-code-recon`, etc.) for OpenCode TUI
- `.opencode/agents/zentra.md` — Dedicated Zentra agent definition for OpenCode's subagent system
- `package.json` — npm package manifest for `zentra-security` distribution
- `install.sh` / `install.ps1` — Cross-platform installer that auto-detects Claude Code and OpenCode
- Dual pre-commit hook examples in `zentra-dev` (Claude Code + OpenCode)

### Changed
- Platform-agnostic descriptions — removed "Claude Code" references from skill descriptions
- Updated README with dual-platform installation instructions
- Updated prerequisites to include OpenCode as an alternative to Claude Code

## [2.0.0] — 2026-04-22

### Added
- **zentra-threat-model**: STRIDE threat modeling with attack surface mapping and data flow analysis
- **zentra-iac-scan**: Infrastructure-as-code scanner for Docker, Terraform, Kubernetes, Helm, and CI/CD pipelines
- **zentra-supply-chain**: Deep software composition analysis — CVEs, transitive dependencies, typosquatting, license risk
- **zentra-api-scan**: API security analysis for OWASP API Top 10, OpenAPI/Swagger, GraphQL
- **zentra-remediate**: Automated patch generation with per-patch user approval and fix verification
- **zentra-compliance**: Compliance mapping for SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001
- **zentra-report**: Executive summary with risk scoring, trend analysis, and board-ready output
- **zentra-dev**: Standalone development-phase security guard with inline feedback and pre-commit hook support
- Shared `config.json` for pipeline state across all skills
- Unified `.zentra/` folder structure for all skill outputs
- Pipeline handoff protocol — each skill offers next steps after completion
- `**Source**:` tag on all findings for cross-scanner traceability

### Changed
- **zentra-code-recon**: Refactored to v3.0 — unified folder structure, config.json, Source tags, full pipeline handoff
- **zentra-pentester**: Refactored to v2.0 — accepts findings from all scanners, API exploit strategies, pipeline handoff

## [1.0.0] — 2026-04-22

### Added
- **zentra-code-recon** (v2.0): Static analysis skill for OWASP Top 10 vulnerability detection. Scans for hardcoded secrets, injection flaws, broken access control, cryptographic failures, security misconfigurations, SSRF, and authentication weaknesses. Spawns parallel subagents for large codebases. Produces structured reports in `.zentra/` directory.
- **zentra-pentester** (v1.0): Dynamic penetration testing skill that validates static findings against live targets using Playwright MCP. Captures screenshot evidence and PoC logs. Supports Burp Suite and Caido MCP for passive scanning. Requires explicit authorization before testing.
- Plugin packaging for Claude Code marketplace with self-hosted marketplace support.
