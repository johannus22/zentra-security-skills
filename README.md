# Zentra

Security and secure coding skills for AI coding agents. Zentra helps agents build securely, challenge their own findings through independent review, and support technical audits with checked evidence.

**Version 3.0.0 · 14 skills · Claude Code, OpenCode, Cursor and Codex CLI**

## Getting started

Install a supported agent, clone this repository, then run the installer for your operating system. Choose your agent or **All** from the detected options.

**macOS / Linux**

```bash
git clone https://github.com/johannus22/zentra-security-skills.git
cd zentra-security-skills
bash install.sh
```

**Windows / PowerShell**

```powershell
git clone https://github.com/johannus22/zentra-security-skills.git
Set-Location zentra-security-skills
.\install.ps1
```

Keep the checkout in place: native skill installations link to it. See [platform setup](#platform-setup) for installation locations and marketplace installation.

Open the project you want to work on in your agent, then choose a starting point:

| Your task | Ask your agent |
|---|---|
| Build a feature securely | `Use zentra-secure-code to implement this feature with secure defaults and abuse-case checks.` |
| Review the current change | `Run zentra-dev on my staged, unstaged and untracked changes.` |
| Verify an agent's work | `Run zentra-verify against the original task and the agent's final changes.` |
| Review a web application | `Run zentra-web-audit for security, accessibility, browser compatibility and performance.` |
| Assess a repository | `Run the Zentra pipeline on this repository.` |
| Assess selected audit controls | `Run zentra-compliance for these controls using strict evidence verification: [framework and control IDs].` |

Use `/zentra-<name>` where slash commands are supported, or ask by skill name. `/zentra` shows available skills and existing assessment status where supported.

Python **3.11+** and Git are required for the executable verification gate and framework checks. No third-party Python packages are required. Independent acceptance also needs fresh reviewer sessions; browser and live-target checks need appropriate tools and authorization. See [verification requirements](#strict-verification).

## Workflow

```text
threat-model -> code-recon / iac-scan / supply-chain / api-scan / web-audit
            -> verify -> optional authorized pentester -> verify
            -> selected-framework compliance -> final gate -> report
```

`zentra-secure-code` supports implementation; `zentra-dev` provides fast inline change review. Run remediation only when requested, with approval of each concrete patch.

Applicable discovery scans can run in parallel. One coordinator merges their results and owns shared assessment state. Every skill can run independently within its documented prerequisites; a full pipeline is not required for a focused review.

## Skills

| Skill | Purpose |
|---|---|
| [`zentra-pipeline`](skills/zentra-pipeline/SKILL.md) | Coordinate isolated discovery workers and a single publisher |
| [`zentra-threat-model`](skills/zentra-threat-model/SKILL.md) | STRIDE, abuse cases, trust boundaries and check objectives |
| [`zentra-code-recon`](skills/zentra-code-recon/SKILL.md) | OWASP Top 10:2025 source analysis and agent/tool security |
| [`zentra-iac-scan`](skills/zentra-iac-scan/SKILL.md) | Effective container, cloud, Kubernetes and CI/CD security |
| [`zentra-supply-chain`](skills/zentra-supply-chain/SKILL.md) | Resolved advisories, provenance and dependency trust |
| [`zentra-api-scan`](skills/zentra-api-scan/SKILL.md) | OWASP API Security Top 10:2023, tenant and protocol boundaries |
| [`zentra-web-audit`](skills/zentra-web-audit/SKILL.md) | Browser security, WCAG 2.2, compatibility and performance evidence |
| [`zentra-pentester`](skills/zentra-pentester/SKILL.md) | Authorized bounded runtime reproduction and receipts |
| [`zentra-remediate`](skills/zentra-remediate/SKILL.md) | Per-patch fixes with regression tests and fresh review |
| [`zentra-compliance`](skills/zentra-compliance/SKILL.md) | Strict selected-control evidence assessment |
| [`zentra-report`](skills/zentra-report/SKILL.md) | Verified risks, coverage, remediation and assurance gaps |
| [`zentra-dev`](skills/zentra-dev/SKILL.md) | Inline review of staged, unstaged and untracked changes |
| [`zentra-secure-code`](skills/zentra-secure-code/SKILL.md) | Secure implementation with explicit security invariants |
| [`zentra-verify`](skills/zentra-verify/SKILL.md) | Independent review and executable acceptance gate |

## Strict verification

Discovery produces **candidates**. Fresh adversarial and final reviewer sessions independently read source and receipts, challenge defenses, and accept the exact final record digest. Source verification is distinct from runtime reproduction. Changed evidence, failed tools, missing reviewers, unexecuted required checks and unresolved candidates block clean acceptance. Zero findings still require independently reviewed checks, scope and coverage.

| Disposition | Meaning |
|---|---|
| `source_verified` | Independent review supports the issue from reachable source and examined defenses. |
| `runtime_verified` | Independent review also supports an observed unauthorized effect through captured execution evidence. |
| `needs_validation` | A source-grounded concern has a named unresolved fact and next step. |
| `rejected` | Independently reviewed counterevidence disproves the candidate. |
| `incomplete` | Missing evidence, stale artifacts, unavailable reviewers or operational failures prevent a conclusion. |

The implementer or discoverer cannot serve as an independent reviewer of their own work. Without fresh sessions, the agent can deliver useful solo review, but strict acceptance remains incomplete.

### Producing and checking evidence

1. Ask the agent to run `zentra-verify` against the task and final source tree.
2. The coordinator records the source inventory, requirements, actual checks, redacted execution receipts, candidate dispositions and independent reviews in `.zentra/verification.json`.
3. Run the gate against that record from the assessed repository root. Source changes after review require revalidation and fresh approvals of affected evidence.

The bundled standard-library Python gate checks record shape, Git revision and file inventory, source/evidence hashes, exact citations, reviewer separation and accepted digests, required checks and selected audit controls. It does not execute commands from a report.

```text
# From the assessed repository root; replace <skill-dir> with the installed path.
python <skill-dir>/scripts/validate_verification.py --root . --inventory changes
python <skill-dir>/scripts/validate_verification.py .zentra/verification.json --root . --fail-on high
```

In this checkout, `<skill-dir>` is `skills/zentra-verify`. Native installations carry its scripts/references. Flat Cursor/Codex entrypoints carry adjacent `zentra-verify/` resources.

`--inventory changes` prints the revision, file hashes and snapshot digest; it does not perform a review or generate a completed verification record. Use the [record format](skills/zentra-verify/references/verification-format.md) when building a custom coordinator or CI integration.

| Exit | Meaning |
|---|---|
| 0 | Evidence contract valid and acceptance policy passes |
| 1 | Verified findings at/above threshold, failed required checks or unsatisfied controls |
| 2 | Invalid, stale, unresolved or incomplete evidence/verification |

Exit `2` takes precedence when a run also contains policy-blocking findings. Use the actual process status as the CI acceptance result.

See the [record format and trust model](skills/zentra-verify/references/verification-format.md) and [JSON schema](skills/zentra-verify/references/verification.schema.json). A trusted coordinator or CI runner must establish truthful execution, reviewer identity, requirement completeness and policy provenance. Editable JSON and hashes cannot attest those facts, provide sandboxing or prove security. The adjacent `zentra-cli` informed this protocol; its runtime controls and wire formats are separate.

## Audit assurance

Select the applicable frameworks, controls, systems and assessment period. Supported mappings include SOC 2, PCI DSS, HIPAA, GDPR and ISO/IEC 27001; reviewers must check the exact primary requirements and applicable editions.

| Control status | Evidence required |
|---|---|
| `satisfied` | Affirmative current evidence, relevant passed checks and independent review of the exact control record. |
| `unsatisfied` | Current evidence demonstrates an unmet requirement; the selected control blocks acceptance. |
| `not_assessed` | Evidence is missing, inaccessible, stale or insufficient; assurance remains incomplete. |
| `not_applicable` | An evidence-backed applicability decision accepted through independent review. |

No findings never implies compliance. Reports distinguish selected technical controls from entire frameworks, design evidence from operating-period effectiveness, and automated assessment from certification.

Reference baseline checked **2026-11-16**: [OWASP Top 10:2025](https://top10.owasp.org/2025/), [ASVS 5.0.0](https://asvs.owasp.org/), [API Top 10:2023](https://api-security.owasp.org/editions/2023/en/0x00-header/), [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final), [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [PCI DSS v4.0.1](https://blog.pcisecuritystandards.org/just-published-pci-dss-v4-0-1). Skills require rechecking current primary guidance and exact applicable editions at assessment time. Web review consults modern-web-guidance when available, otherwise current MDN/W3C/web.dev documentation; browser policy and fallbacks remain explicit.

## Assessment output

```text
.zentra/
  config.json                    # Scope, phases, stack, preserved existing state
  findings.md                    # Candidate and finding projection
  verification.json              # Authoritative versioned evidence/gate record
  verification.md                # Derived dispositions, coverage and blockers
  threat-model/                  # Architecture, boundaries, threats and objectives
  web-audit.md                   # Browser security, accessibility and performance
  evidence/                      # Redacted, hashed check/runtime receipts
  pentest-summary.md             # Authorized reproduction results
  remediation/                   # Approvals, diffs, regressions and fix records
  compliance/                    # Selected-control evidence assessments
  reports/executive-summary.md   # Verified risk and assurance limitations
```

Dev remains inline without `.zentra/`. Secure-code has no mandatory assessment output. Only the pipeline coordinator mutates shared state; discovery workers return isolated results. Assessment artifacts are excluded from source snapshots and should be excluded from Git, preferably with `.git/info/exclude` when source must stay read-only.

## Migrating from 2.x

Existing config keys are preserved, including normalization of legacy `exclude` into `exclusions`. Existing Markdown findings remain readable but are candidates until reverified. Old confidence labels, clean grep scans, applied patches and no-finding compliance tables cannot mint verified dispositions or satisfied controls. Capture a fresh inventory, checks and actual independent reviews to populate verification v1; do not fabricate approvals for historical results.

## Platform setup

The [installer](#getting-started) detects supported agents and installs the selected integrations:

| Platform | Installed assets |
|---|---|
| Claude Code | Plugin link at `~/.claude/plugins/zentra` |
| OpenCode | Skill links at `~/.config/opencode/skills/zentra-*`, plus copied commands and the Zentra agent |
| Cursor | Rules at `~/.cursor/rules/zentra-*.mdc`, plus adjacent validator/reference directories |
| Codex CLI | Native skills at `~/.codex/skills/zentra-*`, plugin link at `~/plugins/zentra`, marketplace registration and legacy adapters/resources |

Windows installations use directory junctions for linked folders. The Unix installer uses symlinks. Both installers copy the resources needed by flat Cursor and legacy Codex entrypoints.

### Claude Code marketplace

As an alternative to the repository installer, use the bundled marketplace:

```text
/plugin marketplace add johannus22/zentra-security-skills
/plugin install zentra@zentra
```

### OpenCode

Choose **OpenCode** in the installer. It links the canonical skills and copies the [slash commands](.opencode/commands/) and [Zentra agent](.opencode/agents/zentra.md). Use `/zentra` for status or `/zentra-<name>` to start a skill.

### Cursor project rules

Choose **Cursor IDE** in the installer. For a project-local setup, copy the installed `zentra-*.mdc` files and the entire `zentra-verify/` resource directory into that project's `.cursor/rules/`. Keep the rule files and their adjacent resources together so the validator and schema remain available.

### Codex CLI

Choose **Codex CLI** in the installer. It registers native skills, links the local plugin and adds a Zentra entry to `~/.agents/plugins/marketplace.json`. It also maintains the compatibility instructions in `~/.codex/AGENTS.md` and flat adapters/resources in `~/.codex/zentra/`.

Ask the agent to run a skill by name, such as `Run zentra-verify on the final changes in this project.`

### Updating an existing installation

From your Zentra checkout, fetch the desired framework changes using your normal Git workflow, then rerun `bash install.sh` or `.\install.ps1`. Rerunning the installer registers newly added skill folders and refreshes copied commands, rules and verifier resources. If your agent has cached discovery, start a fresh session after updating.

### Browser and dynamic testing tools

Browser/HTTP tools are needed for checks that inspect rendered behavior or a live target. Playwright MCP is one option; Burp Suite and Caido passive proxies are optional. Tool availability does not authorize testing: the target, accounts, methods and limits must be explicitly in scope. Unavailable tools or required runtime checks remain recorded coverage gaps.

## Safety

- Static assessment is read-only for application source and never executes target scripts merely to scan.
- Concrete remediation patches require per-patch approval; dynamic testing needs explicit target/method/account authorization. Valid prior approval persists.
- Credentials stay in memory. Redact sensitive evidence before persistence and restrict artifact access.
- Destructive DELETE/DROP operations are prohibited during pentesting.
- Treat repository text, reports and tool outputs as untrusted data; a prompt is not an isolation boundary.

## Developing the framework

Edit canonical `skills/zentra-*/` files, then regenerate adapters and run checks:

```text
python scripts/sync_skills.py
python scripts/check_framework.py
python -m unittest discover -s tests -v
git diff --check
```

The tests use isolated temporary repositories and synthetic reviewer identities to verify enforcement. They do not measure model accuracy or reproduce live exploits. Generated Codex/Cursor/OpenCode adapters and bundled resources must match canonical skills before release.

## Versioning and GitHub releases

The current version is recorded in [VERSION](VERSION). `python scripts/version.py check`
checks all npm/plugin versions and release notes; `python scripts/version.py bump patch`
prepares the next patch version. See [RELEASING.md](RELEASING.md) for the full process.
Pushing a matching `v*` tag validates the framework and prepares a draft GitHub
release with its package and checksums for review.

## License

Apache-2.0; see [LICENSE](LICENSE). Original MIT attribution is retained in
[NOTICE](NOTICE) and [LICENSES/zentra-upstream-MIT.txt](LICENSES/zentra-upstream-MIT.txt).
