# Changelog

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
