# Zentra — Security Skills

Zentra is a cybersecurity framework with 10 specialized skills. Use the `/zentra` command to see pipeline status and available skills.

## Pipeline

```
threat-model -> code-recon -+
               iac-scan ----+
               supply-chain +-> pentester -> remediate -> compliance -> report
               api-scan ----+
```

`zentra-dev` runs independently during development.

## Available Skills

| Command | Phase | Description |
|---------|-------|-------------|
| `/zentra-pipeline` | Orchestrate | Full pipeline — spawns isolated subagents per phase |
| `/zentra-threat-model` | Pre-scan | STRIDE analysis, attack surface mapping |
| `/zentra-code-recon` | Scan | OWASP Top 10 static analysis (SAST) |
| `/zentra-iac-scan` | Scan | Docker, Terraform, K8s, CI/CD security |
| `/zentra-supply-chain` | Scan | CVEs, transitive deps, typosquatting (SCA) |
| `/zentra-api-scan` | Scan | OWASP API Top 10, OpenAPI, GraphQL |
| `/zentra-pentester` | Validate | Dynamic testing against live targets (DAST) |
| `/zentra-remediate` | Fix | Auto-patch generation with approval |
| `/zentra-compliance` | Audit | SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001 |
| `/zentra-report` | Report | Executive summary, risk scoring, trends |
| `/zentra-dev` | Dev | Lightweight guard for changed files |

## Safety

- Static analysis is read-only
- Remediation requires explicit per-patch user approval
- Dynamic testing requires authorization before execution
- Credentials in memory only — never written to files
- Destructive operations (DELETE, DROP) prohibited during pentesting
- `.zentra/` automatically excluded from version control

## Platform Support

| Platform | Skill delivery |
|----------|---------------|
| Claude Code | Plugin symlink at `~/.claude/plugins/zentra` — use `/zentra-<name>` slash commands |
| OpenCode | Per-skill symlinks at `~/.config/opencode/skills/` + commands copied — use `/zentra-<name>` |
| Cursor IDE | MDC rules copied to `~/.cursor/rules/` — ask AI to run zentra skills by name |
| Codex CLI | Skill files in `~/.codex/zentra/` + index appended to `~/.codex/AGENTS.md` — ask AI to run zentra skills by name |
