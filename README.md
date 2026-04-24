# Zentra

Complete cybersecurity framework for AI coding agents. Zentra provides 10 specialized security skills covering the full lifecycle — from threat modeling and static analysis through dynamic validation, auto-remediation, compliance mapping, and executive reporting.

**Supported platforms:** [Claude Code](https://claude.ai/code) · [OpenCode](https://opencode.ai) · [Cursor](https://cursor.com) · [Codex CLI](https://openai.com/codex)

## Pipeline

```
/zentra-pipeline (orchestrates all phases below)

threat-model -> code-recon -+
               iac-scan ----+
               supply-chain +-> pentester -> remediate -> compliance -> report
               api-scan ----+
```

`zentra-dev` runs independently during development.

## Skills

### Pipeline Skills

| Skill | Phase | Description |
|-------|-------|-------------|
| `/zentra-pipeline` | Orchestrate | Runs full pipeline — spawns each skill as an isolated subagent |
| `/zentra-threat-model` | Pre-scan | STRIDE analysis, attack surface mapping, trust boundaries |
| `/zentra-code-recon` | Scan | OWASP Top 10 static analysis (SAST) |
| `/zentra-iac-scan` | Scan | Docker, Terraform, K8s, CI/CD security |
| `/zentra-supply-chain` | Scan | CVEs, transitive deps, typosquatting, license risk (SCA) |
| `/zentra-api-scan` | Scan | OWASP API Top 10, OpenAPI, GraphQL analysis |
| `/zentra-pentester` | Validate | Dynamic testing against live targets (DAST) |
| `/zentra-remediate` | Fix | Auto-patch generation with user approval |
| `/zentra-compliance` | Audit | SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001 mapping |
| `/zentra-report` | Report | Executive summary, risk scoring, trends |

### Standalone

| Skill | Description |
|-------|-------------|
| `/zentra-dev` | Lightweight dev-phase guard — scans changed files, inline feedback |

## Quick Start

### Full Pipeline

```
# Run everything at once (recommended)
/zentra-pipeline               # Orchestrates all phases, spawns isolated subagents

# Or run phases individually
1. /zentra-threat-model        # Understand the attack surface
2. /zentra-code-recon           # Static analysis
   /zentra-iac-scan             # (run alongside code-recon)
   /zentra-supply-chain         # (run alongside code-recon)
   /zentra-api-scan             # (run alongside code-recon)
3. /zentra-pentester            # Validate against running app
4. /zentra-remediate            # Auto-fix vulnerabilities
5. /zentra-compliance           # Map to regulatory frameworks
6. /zentra-report               # Executive summary
```

### During Development

```
/zentra-dev                     # Scan changed files before committing
```

### Skip Ahead

Every skill can run independently. Start wherever makes sense:
- Just want SAST? Run `/zentra-code-recon`
- Just need compliance? Run scanners first, then `/zentra-compliance`
- Just want to fix things? Run `/zentra-remediate` after any scanner

## Output Structure

All pipeline skills write to `.zentra/` (automatically added to `.gitignore`):

```
.zentra/
├── config.json                  # Shared state across skills
├── scan-summary.md              # Unified findings summary
├── detailed-findings.md         # All findings with evidence
├── recommendations.md           # Prioritized fix list
├── threat-model/                # Threat modeling outputs
│   ├── threat-model.md
│   ├── attack-surface.md
│   └── data-flows.md
├── evidence/                    # Evidence from scans + pentesting
│   ├── critical/
│   ├── high/
│   ├── medium/
│   └── low/
├── pentest-summary.md           # Dynamic testing results
├── remediation/                 # Patch records
│   ├── remediation-plan.md
│   └── patches/
├── compliance/                  # Compliance reports
│   ├── compliance-summary.md
│   ├── soc2.md
│   ├── pci-dss.md
│   ├── hipaa.md
│   ├── gdpr.md
│   └── iso27001.md
└── reports/
    └── executive-summary.md     # Board-ready report
```

`zentra-dev` outputs inline — no files created.

## Prerequisites

- **Claude Code** with plugin support — OR — **OpenCode** v0.1+ — OR — **Cursor** with AI chat enabled — OR — **Codex CLI** (OpenAI)
- **Playwright MCP** (for `/zentra-pentester`): `npx @playwright/mcp@latest`
- **Burp Suite MCP** or **Caido MCP** (optional): Passive proxy during pentesting

## Installation

### Quick Install (auto-detects your agent)

```bash
# Unix/macOS
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra && bash install.sh

# Windows (PowerShell)
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra; .\install.ps1
```

### Claude Code — From Marketplace

```
/plugin marketplace add Kodecraft-Dev/zentra
/plugin install zentra@zentra
```

### OpenCode — From npm

```bash
# Add to your project's opencode.json
{
  "plugin": ["zentra-security"]
}
```

Or install skills globally:

```bash
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra && bash install.sh
```

### Cursor IDE

```bash
# Unix/macOS
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra && bash install.sh   # select "Cursor IDE" or "All"

# Windows (PowerShell)
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra; .\install.ps1       # select "Cursor IDE" or "All"
```

Rules are installed to `~/.cursor/rules/`. Once installed, use Cursor's AI chat:

```
Ask AI: run zentra-code-recon
Ask AI: run the full zentra pipeline
Ask AI: scan this project for OWASP vulnerabilities
```

> **Note:** Cursor reads rules from `.cursor/rules/` within the current project. If zentra rules don't auto-apply, copy `~/.cursor/rules/zentra-*.mdc` into your project's `.cursor/rules/` folder.

### Codex CLI

```bash
# Unix/macOS
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra && bash install.sh   # select "Codex CLI" or "All"

# Windows (PowerShell)
git clone https://github.com/Kodecraft-Dev/zentra.git
cd zentra; .\install.ps1       # select "Codex CLI" or "All"
```

The installer:
1. Copies full skill files to `~/.codex/zentra/`
2. Appends a zentra skill index to `~/.codex/AGENTS.md` (creates it if missing; uses `<!-- zentra:start/end -->` markers for safe idempotent updates)

Once installed, use Codex's chat:

```
Ask AI: run zentra-code-recon
Ask AI: run the full zentra pipeline
Ask AI: scan this project for OWASP vulnerabilities
```

> **How it works:** Codex reads your global `~/.codex/AGENTS.md` at session start — this includes the zentra skill index. When you ask to run a skill, Codex reads the full instructions from `~/.codex/zentra/zentra-<name>.md`.

## Safety

- Static analysis is read-only — never modifies your codebase
- Remediation requires explicit per-patch user approval
- Dynamic testing requires authorization before execution
- Credentials are held in memory only, never written to files
- Destructive operations (DELETE, DROP) are prohibited during pentesting
- curl/nmap usage requires per-command user approval
- `.zentra/` is automatically excluded from version control

## License

MIT
