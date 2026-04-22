# Edward

Security penetration testing agent for Claude Code. Edward scans your codebase for OWASP Top 10 vulnerabilities through static analysis, then validates findings against a live application using Playwright MCP.

## Skills

### /edward-code-recon (Static Analysis)

Scans codebases for security vulnerabilities using pattern-based static analysis. Detects:

- Hardcoded secrets and credentials
- SQL injection, XSS, command injection
- Broken access control patterns
- Cryptographic failures
- Security misconfigurations
- SSRF vulnerabilities
- Authentication weaknesses

Produces structured reports in `.edward/` with severity classification (Critical/High/Medium/Low), OWASP categorization, CWE mapping, and remediation guidance. Spawns parallel subagents for large codebases.

### /edward-pentester (Dynamic Validation)

Reads findings from `/edward-code-recon` and attempts to reproduce each vulnerability against a running application using Playwright MCP. Produces:

- Screenshot evidence for each exploit attempt
- Proof-of-concept logs with step-by-step reproduction
- Verdicts: Confirmed, Partially Confirmed, Not Reproducible, or Requires Manual Testing
- Updated findings with dynamic testing results

**Requires authorization** — prompts for explicit consent before testing.

## Workflow

```
1. Run /edward-code-recon against your codebase
2. Review findings in .edward/detailed-findings.md
3. Start your application locally
4. Run /edward-pentester to validate findings against the live target
```

## Prerequisites

- **Claude Code** with plugin support
- **Playwright MCP** (required for `/edward-pentester`): `npx @playwright/mcp@latest`
- **Burp Suite MCP** or **Caido MCP** (optional): Enables passive proxy scanning during pentesting

## Installation

### From Self-Hosted Marketplace

Register the marketplace:

```
/plugin marketplace add Kodecraft-Dev/edward
```

Install the plugin:

```
/plugin install edward@edward
```

## Output Structure

```
.edward/
├── scan-summary.md          # Overview with severity counts
├── detailed-findings.md     # All findings with evidence
├── recommendations.md       # Prioritized fix list
├── pentest-summary.md       # Dynamic testing results (after pentester)
└── evidence/
    ├── critical/
    ├── high/
    ├── medium/
    └── low/
```

## Safety

- Static analysis is read-only — never modifies your codebase
- Dynamic testing requires explicit authorization before execution
- Credentials are held in memory only, never written to files
- Destructive operations (DELETE, DROP) are prohibited during pentesting
- curl/nmap usage requires per-command user approval

## License

MIT
