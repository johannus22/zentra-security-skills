# Edward — Security Framework

Edward is a cybersecurity framework with 10 specialized skills. Use the `/edward` command to see pipeline status and available skills.

## Pipeline

```
threat-model -> code-recon -+
               iac-scan ----+
               supply-chain +-> pentester -> remediate -> compliance -> report
               api-scan ----+
```

`edward-dev` runs independently during development.

## Available Skills

| Command | Phase | Description |
|---------|-------|-------------|
| `/edward-threat-model` | Pre-scan | STRIDE analysis, attack surface mapping |
| `/edward-code-recon` | Scan | OWASP Top 10 static analysis (SAST) |
| `/edward-iac-scan` | Scan | Docker, Terraform, K8s, CI/CD security |
| `/edward-supply-chain` | Scan | CVEs, transitive deps, typosquatting (SCA) |
| `/edward-api-scan` | Scan | OWASP API Top 10, OpenAPI, GraphQL |
| `/edward-pentester` | Validate | Dynamic testing against live targets (DAST) |
| `/edward-remediate` | Fix | Auto-patch generation with approval |
| `/edward-compliance` | Audit | SOC 2, PCI-DSS, HIPAA, GDPR, ISO 27001 |
| `/edward-report` | Report | Executive summary, risk scoring, trends |
| `/edward-dev` | Dev | Lightweight guard for changed files |

## Safety

- Static analysis is read-only
- Remediation requires explicit per-patch user approval
- Dynamic testing requires authorization before execution
- Credentials in memory only — never written to files
- Destructive operations (DELETE, DROP) prohibited during pentesting
- `.edward/` automatically excluded from version control
