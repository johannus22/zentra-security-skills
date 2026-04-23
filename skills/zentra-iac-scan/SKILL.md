---
name: zentra-iac-scan
description: "Infrastructure-as-code security scanner. Analyzes Dockerfiles, docker-compose, Terraform, Kubernetes manifests, Helm charts, and CI/CD pipelines (GitHub Actions, GitLab CI) for misconfigurations, privilege escalation, and secret exposure. Writes findings to .zentra/detailed-findings.md."
---

# Zentra — IaC Security Scan

You are Zentra's infrastructure-as-code scanner. Analyze Dockerfiles, docker-compose, Terraform, Kubernetes manifests, Helm charts, and CI/CD pipelines for security misconfigurations. Write findings in the shared format to `.zentra/detailed-findings.md`.

---

## Phase 1: Intake

1. Read `.zentra/config.json` if it exists — use the target, stack, and exclusions. If it doesn't exist, create it (follow zentra-code-recon Phase 1 intake process, including auto-ignore of `.zentra/` in `.gitignore`).

2. Detect IaC files:

```
Glob("**/Dockerfile*", "**/docker-compose*.{yml,yaml}", "**/.dockerignore")
Glob("**/*.tf", "**/*.tfvars", "**/terraform.tfstate*")
Glob("**/k8s/**/*.{yml,yaml}", "**/kubernetes/**/*.{yml,yaml}", "**/manifests/**/*.{yml,yaml}")
Glob("**/Chart.yaml", "**/values.yaml", "**/templates/**/*.{yml,yaml}")
Glob("**/.github/workflows/*.{yml,yaml}", "**/.gitlab-ci.yml", "**/Jenkinsfile", "**/.circleci/config.yml")
Glob("**/cloudbuild.yaml", "**/appspec.yml", "**/buildspec.yml")
```

3. If NO IaC files are found, tell the user and stop:

> "No infrastructure-as-code files detected. This skill scans Dockerfiles, Terraform, Kubernetes manifests, Helm charts, and CI/CD pipelines. Skipping."

---

## Phase 2: Docker Scan

### Dockerfile Analysis

For each Dockerfile, Grep for:

```
FROM.*:latest|FROM.*:master
USER\s+root|^(?!.*USER)
RUN.*apt-get.*-y|RUN.*apk add.*--no-cache
(ENV|ARG).*(PASSWORD|SECRET|KEY|TOKEN|CREDENTIAL).*=
RUN.*curl.*\|.*sh|RUN.*wget.*\|.*sh
COPY\s+\.\s+\.|ADD\s+\.
EXPOSE\s+(22|23|3389|5432|3306|27017|6379)
RUN.*chmod\s+777|RUN.*chmod\s+a\+rwx
--privileged|--cap-add|--security-opt\s+seccomp=unconfined
```

Read the full Dockerfile for each match. Check:
- Running as root (no USER directive after FROM)
- Secrets passed via ENV/ARG (should use secrets mount)
- Piping curl to shell (unsigned code execution)
- COPY . . without .dockerignore (may include .env, .git)
- Exposed database/admin ports
- Multi-stage builds not used (large attack surface)

### docker-compose Analysis

```
Grep: privileged:\s*true
Grep: network_mode:\s*["']?host
Grep: volumes:.*(/etc|/var/run/docker.sock|/proc|/sys|/dev)
Grep: (environment|env_file).*\n.*(?:PASSWORD|SECRET|KEY|TOKEN)
Grep: cap_add:.*(SYS_ADMIN|NET_ADMIN|ALL)
Grep: restart:\s*no|^(?!.*restart:)
```

---

## Phase 3: Terraform Scan

For each `.tf` file, Grep for:

```
acl\s*=\s*["']?public|public_access.*=.*true|block_public_acls\s*=\s*false
ingress\s*\{[^}]*cidr_blocks\s*=\s*\["0\.0\.0\.0/0"\]
encrypted\s*=\s*false|kms_key_id\s*=\s*""
(access_key|secret_key|password|token)\s*=\s*"[^"]{8,}"
versioning\s*\{[^}]*enabled\s*=\s*false
logging\s*\{[^}]*enabled\s*=\s*false|^(?!.*logging)
(deletion_protection|prevent_destroy)\s*=\s*false
```

Also check:
- `terraform.tfstate` committed to repo (contains secrets)
- `.tfvars` files with hardcoded credentials
- No backend configuration (state stored locally)
- Missing `required_providers` version constraints

---

## Phase 4: Kubernetes Scan

For each K8s manifest YAML, Grep for:

```
privileged:\s*true
hostNetwork:\s*true
hostPID:\s*true|hostIPC:\s*true
runAsUser:\s*0|runAsNonRoot:\s*false
(capabilities:.*add:.*SYS_ADMIN|capabilities:.*add:.*NET_ADMIN|capabilities:.*add:.*ALL)
hostPath:|emptyDir:
^(?!.*resources:)|^(?!.*limits:)
automountServiceAccountToken:\s*true
(imagePullPolicy:\s*Always|image:.*:latest)
```

Also check:
- Missing `securityContext` on pods/containers
- Missing `NetworkPolicy` for namespace isolation
- `ClusterRole`/`ClusterRoleBinding` with wildcard verbs or resources
- Secrets stored as plain YAML (not sealed/encrypted)
- Missing `readOnlyRootFilesystem: true`

---

## Phase 5: CI/CD Pipeline Scan

### GitHub Actions

```
Grep: pull_request_target
Grep: \$\{\{.*github\.event\.(issue|pull_request|comment)\.body
Grep: actions/checkout@[^v]|uses:.*@(master|main|latest)
Grep: (GITHUB_TOKEN|secrets\.\w+).*\$\{\{
Grep: permissions:\s*write-all|permissions:\s*\n\s+contents:\s*write
Grep: run:.*\$\{\{.*inputs\.|run:.*\$\{\{.*github\.event
```

Check:
- Third-party actions not pinned to SHA (supply chain risk)
- `pull_request_target` with checkout of PR code (code injection)
- Secrets exposed in logs via `echo` or `run`
- Overly permissive `permissions` block
- Self-hosted runners without security hardening

### GitLab CI / Other

```
Grep: (PRIVATE_TOKEN|CI_JOB_TOKEN|DEPLOY_TOKEN)
Grep: allow_failure:\s*true.*security|allow_failure:\s*true.*sast
Grep: when:\s*manual.*security
```

---

## Phase 6: Classify & Report

Write all findings to `.zentra/detailed-findings.md` using the shared finding format. Every finding MUST have:
- `**Source**: zentra-iac-scan`
- A specific file path and line number
- The actual problematic configuration snippet
- A remediation example with the fixed configuration

### Severity Rules

| Severity | Criteria |
|----------|----------|
| **Critical** | Exploitable with no auth: RCE, SQLi with data access, leaked production secrets, unauthenticated admin access, privileged container escape |
| **High** | Exploitable with low-privilege auth: stored XSS, IDOR, privilege escalation, SSRF to internal services, public cloud storage, known CVE with exploit |
| **Medium** | Requires specific conditions: reflected XSS, CSRF on state-changing actions, weak crypto in non-critical paths, missing rate limiting, permissive RBAC |
| **Low** | Defense-in-depth issues: missing security headers, verbose errors, outdated non-vulnerable deps, informational disclosure, missing resource limits |

### Update scan-summary.md

Add a row to the "Findings by Source" table:

```
| zentra-iac-scan | N | N | N | N | N |
```

### Update config.json

Append to scans array:

```json
{
  "skill": "zentra-iac-scan",
  "date": "[YYYY-MM-DD]",
  "findings": { "critical": N, "high": N, "medium": N, "low": N }
}
```

---

## Decision Gates

- **Skip sections** if no files of that type exist (e.g., skip Terraform if no .tf files).
- **Spawn subagents** if there are >20 IaC files — one agent per IaC category (Docker, Terraform, K8s, CI/CD) in parallel.
- **Escalate** if any finding allows container escape or cluster compromise — notify user immediately.

---

## Phase 7: Handoff

> **IaC Scan complete.** Found **N Critical**, **N High**, **N Medium**, **N Low** infrastructure findings.
>
> **Pipeline status:**
> [Read config.json scans array and mark completed skills]
>
> **Recommended next steps:**
> [Show uncompleted pipeline steps, recommend the next logical one]

---

*v1.0 — rafael@kodecraft.dev*
