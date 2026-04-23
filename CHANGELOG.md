# Changelog

## [2.1.0] — 2026-04-22

### Added
- **OpenCode support** — Edward now works as a first-class plugin on both Claude Code and OpenCode
- `opencode.json` — OpenCode plugin configuration with Playwright MCP reference
- `AGENTS.md` — OpenCode instructions file with pipeline overview and skill reference
- `.opencode/commands/` — 11 slash commands (`/edward`, `/edward-code-recon`, etc.) for OpenCode TUI
- `.opencode/agents/edward.md` — Dedicated Edward agent definition for OpenCode's subagent system
- `package.json` — npm package manifest for `edward-security` distribution
- `install.sh` / `install.ps1` — Cross-platform installer that auto-detects Claude Code and OpenCode
- Dual pre-commit hook examples in `edward-dev` (Claude Code + OpenCode)

### Changed
- Platform-agnostic descriptions — removed "Claude Code" references from skill descriptions
- Updated README with dual-platform installation instructions
- Updated prerequisites to include OpenCode as an alternative to Claude Code

## [2.0.0] — 2026-04-22

### Added
- **edward-threat-model**: STRIDE threat modeling with attack surface mapping and data flow analysis
- **edward-iac-scan**: Infrastructure-as-code scanner for Docker, Terraform, Kubernetes, Helm, and CI/CD pipelines
- **edward-supply-chain**: Deep software composition analysis — CVEs, transitive dependencies, typosquatting, license risk
- **edward-api-scan**: API security analysis for OWASP API Top 10, OpenAPI/Swagger, GraphQL
- **edward-remediate**: Automated patch generation with per-patch user approval and fix verification
- **edward-compliance**: Compliance mapping for SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001
- **edward-report**: Executive summary with risk scoring, trend analysis, and board-ready output
- **edward-dev**: Standalone development-phase security guard with inline feedback and pre-commit hook support
- Shared `config.json` for pipeline state across all skills
- Unified `.edward/` folder structure for all skill outputs
- Pipeline handoff protocol — each skill offers next steps after completion
- `**Source**:` tag on all findings for cross-scanner traceability

### Changed
- **edward-code-recon**: Refactored to v3.0 — unified folder structure, config.json, Source tags, full pipeline handoff
- **edward-pentester**: Refactored to v2.0 — accepts findings from all scanners, API exploit strategies, pipeline handoff

## [1.0.0] — 2026-04-22

### Added
- **edward-code-recon** (v2.0): Static analysis skill for OWASP Top 10 vulnerability detection. Scans for hardcoded secrets, injection flaws, broken access control, cryptographic failures, security misconfigurations, SSRF, and authentication weaknesses. Spawns parallel subagents for large codebases. Produces structured reports in `.edward/` directory.
- **edward-pentester** (v1.0): Dynamic penetration testing skill that validates static findings against live targets using Playwright MCP. Captures screenshot evidence and PoC logs. Supports Burp Suite and Caido MCP for passive scanning. Requires explicit authorization before testing.
- Plugin packaging for Claude Code marketplace with self-hosted marketplace support.
