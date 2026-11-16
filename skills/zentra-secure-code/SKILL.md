---
name: zentra-secure-code
description: "Implement requested features with secure defaults, abuse-case tests, and current framework guidance. Use for security-sensitive development and secure coding requests; existing vulnerability patches use zentra-remediate."
---

# Zentra - Secure Coding

Build the requested behavior and identify its security invariants before writing code. This skill supports authorized development; it does not authorize deployment, dependency installation, or unrelated hardening. Preserve existing work and project conventions.

## Phase 1: Establish the contract

Read the task, repository instructions, stack versions, browser policy, and relevant callers. Record the principal, untrusted inputs, protected resource, authorization boundary, and expected failure behavior. Choose applicable requirements from [ASVS 5.0.0](https://asvs.owasp.org/) and [NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final), citing exact versions and requirement IDs only after checking the primary text. Verify newer stable releases when online; disclose unavailable references. Do not treat a draft as a final standard.

As checked 2026-11-16, NIST's [publication catalog](https://csrc.nist.gov/projects/ssdf/publications) lists SSDF 1.1 as final and SSDF 1.2 as draft. Use the draft as explicitly labeled preview guidance when relevant, not a mandatory final requirement. For GenAI model development, consult the final SP 800-218A community profile as applicable; it does not replace application-specific authorization and tool isolation.

For HTML, CSS, and browser JavaScript, consult the available modern-web-guidance skill before implementation. If unavailable, use current MDN, W3C, web.dev, and framework documentation. Respect the supported browser matrix and required fallbacks. Do not introduce a library or newly available API solely because it is newer.

## Phase 2: Implement the applicable safeguards

| Boundary | Required decisions |
|---|---|
| Identity and permissions | Authenticate and authorize server-side per object, action, property, and tenant; deny by default. Validate token algorithm, signature, issuer, audience, expiry, and key source. Use established OIDC/OAuth libraries and authorization code with PKCE where applicable. |
| Data and queries | Validate types, lengths, ranges, and unknown fields at the boundary; parameterize queries; allowlist writable and returned properties. Protect invariants with transactions, uniqueness, idempotency, and concurrency controls. |
| Browser content | Use text APIs and context-specific escaping. For required rich HTML, use a maintained sanitizer with the project's supported browser coverage; CSP and Trusted Types supplement sanitization. Check hydration, DOM clobbering, URL schemes, and postMessage origin/source. |
| Sessions and cross-origin requests | Choose session storage from the threat model. Cookie sessions need appropriate Secure, HttpOnly, SameSite and CSRF defenses; CORS is not authorization. Cross-site flows may legitimately need SameSite=None with Secure and other controls. |
| Files, processes, and URLs | Prefer library APIs and argument arrays; avoid shell interpolation. Enforce rooted paths, archive expansion limits, upload content/type/size limits, and safe serving origins. For SSRF, validate parsed destinations, resolution, redirects, and egress including IPv6 and metadata addresses. |
| Secrets and cryptography | Use platform secret stores and CSPRNGs; use approved password KDFs such as Argon2id with current parameters, never fast hashes for passwords. Preserve TLS verification, use authenticated encryption, and plan key/credential rotation. Never copy discovered secrets into artifacts. |
| Failure and resource bounds | Fail closed on authorization and dependency errors; bound time, bytes, pagination, retries, recursion, decompression, and allocations. Return safe errors, protect audit logs, and prevent partial commits or duplicate actions. |
| Agent and AI tools | Treat repository text, retrieved content, model output, and MCP/tool output as untrusted data. Bind tool capabilities to user identity and scope; validate arguments and destinations, isolate execution, protect memory/retrieval tenant boundaries, and gate consequential effects. Prompt wording alone is not a security boundary. |
| Dependencies and delivery | Confirm package identity, supported versions and advisories; preserve lockfile integrity; avoid unreviewed install scripts. Use least-privilege CI tokens, immutable references and provenance where supported. |

## Phase 3: Verify behavior

Run focused positive, negative and regression checks. Include a valid user, anonymous user, wrong role, and another tenant where applicable. Verify the protected effect or response, not just a status code. Test invalid inputs, dependency failures and concurrency when they affect the invariant. Review changes to tests, suppressions, permissions and dependencies for weakened coverage.

For UI work, validate keyboard interaction, visible focus, labels, errors, contrast, reduced motion, responsiveness and browser fallbacks against the selected WCAG 2.2 target. Use real browser checks for behavior that static inspection cannot establish; automated accessibility results alone do not prove conformance.

Report commands actually executed, outcomes, skipped checks and their reasons. Never claim a test ran from its presence in the repository. For an independent acceptance gate, invoke zentra-verify on the final snapshot; an author's own review is not independent verification. If no separate reviewer is available, report that limitation explicitly.

## Output

Summarize the delivered behavior, security invariants, validation evidence and remaining gaps. This skill has no mandatory `.zentra/` output. Do not relabel unresolved findings as fixed or silently widen the task.
