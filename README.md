# Edward

Complete cybersecurity framework for AI coding agents. Edward provides 10 specialized security skills covering the full lifecycle — from threat modeling and static analysis through dynamic validation, auto-remediation, compliance mapping, and executive reporting.

**Supported platforms:** [Claude Code](https://claude.ai/code) · [OpenCode](https://opencode.ai)

## Pipeline

```
threat-model -> code-recon -+
               iac-scan ----+
               supply-chain +-> pentester -> remediate -> compliance -> report
               api-scan ----+
```

`edward-dev` runs independently during development.

## Skills

### Pipeline Skills

| Skill | Phase | Description |
|-------|-------|-------------|
| `/edward-threat-model` | Pre-scan | STRIDE analysis, attack surface mapping, trust boundaries |
| `/edward-code-recon` | Scan | OWASP Top 10 static analysis (SAST) |
| `/edward-iac-scan` | Scan | Docker, Terraform, K8s, CI/CD security |
| `/edward-supply-chain` | Scan | CVEs, transitive deps, typosquatting, license risk (SCA) |
| `/edward-api-scan` | Scan | OWASP API Top 10, OpenAPI, GraphQL analysis |
| `/edward-pentester` | Validate | Dynamic testing against live targets (DAST) |
| `/edward-remediate` | Fix | Auto-patch generation with user approval |
| `/edward-compliance` | Audit | SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001 mapping |
| `/edward-report` | Report | Executive summary, risk scoring, trends |

### Standalone

| Skill | Description |
|-------|-------------|
| `/edward-dev` | Lightweight dev-phase guard — scans changed files, inline feedback |

## Quick Start

### Full Pipeline

```
1. /edward-threat-model        # Understand the attack surface
2. /edward-code-recon           # Static analysis (offers to run parallel scanners)
3. /edward-pentester            # Validate against running app
4. /edward-remediate            # Auto-fix vulnerabilities
5. /edward-compliance           # Map to regulatory frameworks
6. /edward-report               # Executive summary
```

### During Development

```
/edward-dev                     # Scan changed files before committing
```

### Skip Ahead

Every skill can run independently. Start wherever makes sense:
- Just want SAST? Run `/edward-code-recon`
- Just need compliance? Run scanners first, then `/edward-compliance`
- Just want to fix things? Run `/edward-remediate` after any scanner

## Output Structure

All pipeline skills write to `.edward/` (automatically added to `.gitignore`):

```
.edward/
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

`edward-dev` outputs inline — no files created.

## Prerequisites

- **Claude Code** with plugin support — OR — **OpenCode** v0.1+
- **Playwright MCP** (for `/edward-pentester`): `npx @playwright/mcp@latest`
- **Burp Suite MCP** or **Caido MCP** (optional): Passive proxy during pentesting

## Installation

### Quick Install (auto-detects your agent)

```bash
# Unix/macOS
git clone https://github.com/Kodecraft-Dev/edward.git
cd edward && bash install.sh

# Windows (PowerShell)
git clone https://github.com/Kodecraft-Dev/edward.git
cd edward; .\install.ps1
```

### Claude Code — From Marketplace

```
/plugin marketplace add Kodecraft-Dev/edward
/plugin install edward@edward
```

### OpenCode — From npm

```bash
# Add to your project's opencode.json
{
  "plugin": ["edward-security"]
}
```

Or install skills globally:

```bash
git clone https://github.com/Kodecraft-Dev/edward.git
cd edward && bash install.sh
```

## Safety

- Static analysis is read-only — never modifies your codebase
- Remediation requires explicit per-patch user approval
- Dynamic testing requires authorization before execution
- Credentials are held in memory only, never written to files
- Destructive operations (DELETE, DROP) are prohibited during pentesting
- curl/nmap usage requires per-command user approval
- `.edward/` is automatically excluded from version control

## License

MIT
