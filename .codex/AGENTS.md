# Zentra Security Skills

Zentra provides 14 security and secure coding skills.

- Native Codex skills install to `~/.codex/skills/zentra-*/`.
- The plugin installs to `~/plugins/zentra` and is registered in `~/.agents/plugins/marketplace.json`.
- Legacy entrypoints/resources also install to `~/.codex/zentra/`.

## Running skills

When asked to run a skill, prefer `~/.codex/skills/zentra-<name>/SKILL.md`; fall back to `~/.codex/zentra/zentra-<name>.md`. Follow the selected instructions and existing task authorization. Flat entrypoint resources live in the adjacent `zentra-<name>/` subdirectory.

| Skill | Purpose |
|---|---|
| `zentra-pipeline` | Coordinate discovery, verification, optional DAST, audit and reporting |
| `zentra-threat-model` | STRIDE, abuse cases, trust boundaries and verification objectives |
| `zentra-code-recon` | Source analysis against OWASP Top 10:2025 and agent/tool risks |
| `zentra-iac-scan` | Effective infrastructure and delivery security |
| `zentra-supply-chain` | Resolved dependencies, advisories and build provenance |
| `zentra-api-scan` | OWASP API Security Top 10:2023 and protocol boundaries |
| `zentra-web-audit` | Browser security, WCAG 2.2, compatibility and measured performance |
| `zentra-pentester` | Authorized bounded dynamic reproduction with receipts |
| `zentra-remediate` | Reviewable per-patch fixes and regression verification |
| `zentra-compliance` | Evidence-based selected-control assessment and strict assurance |
| `zentra-report` | Current verified findings, coverage and honest audit conclusions |
| `zentra-dev` | Quick inline review of staged/unstaged/untracked changes |
| `zentra-secure-code` | Secure implementation with abuse-case checks |
| `zentra-verify` | Independent evidence review and executable acceptance gate |

## Evidence and authorization

Discovery is not verification. Use zentra-verify for independent acceptance; required missing evidence/reviewers fail closed. Source verification is distinct from runtime reproduction. Strict controls require affirmative evidence, never inference from zero findings. A trusted runner must establish actual execution and independent session provenance; JSON alone cannot attest them.

Static scans do not modify source or execute target code. Remediation needs per-patch approval; dynamic testing needs target/method/account authorization. Reuse existing explicit approval. Never persist credentials or run destructive pentest operations. Dev stays inline without `.zentra/`; other skills may write scoped assessment artifacts. Only the coordinator mutates shared pipeline state.
