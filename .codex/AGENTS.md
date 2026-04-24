# Zentra Security Skills

Zentra is a cybersecurity framework with 11 specialized security skills. Full skill files are installed at `~/.codex/zentra/`.

## Running Skills

When asked to run a zentra skill (e.g., "run zentra-code-recon"):
1. Read `~/.codex/zentra/zentra-<name>.md`
2. Follow the instructions in that file exactly

## Available Skills

| Skill | Phase | Description |
|-------|-------|-------------|
| `zentra-pipeline` | Orchestrate | Full pipeline — runs all phases as isolated subagents |
| `zentra-threat-model` | Pre-scan | STRIDE analysis, attack surface mapping |
| `zentra-code-recon` | Scan | OWASP Top 10 static analysis (SAST) |
| `zentra-iac-scan` | Scan | Docker, Terraform, K8s, CI/CD security |
| `zentra-supply-chain` | Scan | CVEs, transitive deps, typosquatting (SCA) |
| `zentra-api-scan` | Scan | OWASP API Top 10, OpenAPI, GraphQL |
| `zentra-pentester` | Validate | Dynamic testing against live targets (DAST) |
| `zentra-remediate` | Fix | Auto-patch generation with approval |
| `zentra-compliance` | Audit | SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001 |
| `zentra-report` | Report | Executive summary, risk scoring, trends |
| `zentra-dev` | Dev | Lightweight guard for changed files |

## Pipeline

```
zentra-threat-model → zentra-code-recon ─┐
                       zentra-iac-scan   ├→ zentra-pentester → zentra-remediate → zentra-compliance → zentra-report
                       zentra-supply-chain┤
                       zentra-api-scan   ┘
```

`zentra-dev` runs independently. All pipeline skills write to `.zentra/` in the project root.
