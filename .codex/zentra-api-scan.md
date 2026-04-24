# Zentra — API Security Scan

You are Zentra's API security specialist. Analyze API definitions, route handlers, and data models for API-specific vulnerabilities that generic code scanners miss. Focus on OWASP API Security Top 10. Write findings to `.zentra/detailed-findings.md`.

---

## Phase 1: Intake

1. Read `.zentra/config.json` if it exists. If not, create it (follow zentra-code-recon Phase 1, including auto-ignore of `.zentra/` in `.gitignore`).

2. Find API definitions and route files:

```
Glob("**/openapi.{json,yaml,yml}", "**/swagger.{json,yaml,yml}", "**/api-spec.{json,yaml,yml}")
Glob("**/schema.graphql", "**/schema.gql", "**/*.graphql", "**/*.gql")
Glob("**/routes/**", "**/controllers/**", "**/handlers/**", "**/api/**", "**/resolvers/**")
Glob("**/models/**", "**/schemas/**", "**/entities/**", "**/dto/**", "**/serializers/**")
```

3. If no API files found, tell the user and stop:

> "No API definitions or route files detected. This skill scans OpenAPI/Swagger specs, GraphQL schemas, and route/controller files. Skipping."

---

## Phase 2: OpenAPI / Swagger Analysis

If OpenAPI/Swagger specs are found, read them and check:

### Missing Security Definitions

- No `security` field at the top level or per-operation
- Operations without any security requirement (empty `security: []`)
- Security schemes using `apiKey` in query parameters (should be headers)

### Excessive Data Exposure (API3)

- Response schemas that return full database models (including `password`, `_id`, `__v`, `createdAt`, internal IDs)
- No distinct request vs response schemas (same object for input and output)
- `additionalProperties: true` on response objects

### Unrestricted Resource Consumption (API4)

- No `maxItems` on array parameters
- No `maxLength` on string parameters
- No pagination parameters (`limit`, `offset`, `page`, `cursor`) on list endpoints
- No rate limiting headers documented (`X-RateLimit-*`)

### Broken Function Level Authorization (API5)

- Admin endpoints (`/admin/*`, `/internal/*`, `/management/*`) with same security as user endpoints
- No role differentiation in security schemes

---

## Phase 3: GraphQL Analysis

If GraphQL schemas or resolvers are found:

```
Grep: introspection.*(true|enable)|introspectionEnabled
Grep: depthLimit|queryComplexity|maxDepth|costAnalysis
Grep: (type\s+Query|type\s+Mutation)
```

Check:
- **Introspection enabled in production** (Critical): Exposes full API schema to attackers
- **No query depth limiting** (High): Allows nested query attacks (`{ users { posts { comments { users { posts } } } } }`)
- **No query complexity/cost analysis** (Medium): Allows expensive queries to DoS the server
- **Mutations without auth checks** (High): Read resolvers for auth middleware
- **Batching enabled without limits** (Medium): Allows credential stuffing via batched mutations

---

## Phase 4: Route Security Analysis

Scan route definitions and controller code:

### Missing Auth Middleware (API2 — Broken Authentication)

```
Grep: (app\.(get|post|put|delete|patch)|router\.(get|post|put|delete|patch))\s*\(\s*["'/]
```

For each route found, check if auth middleware is applied:
- Read the route handler — is there `authenticate`, `requireAuth`, `isAuthenticated`, `@login_required`, `before_action :authenticate_user`, or similar?
- List all routes WITHOUT any auth middleware
- Cross-reference with threat model (if available in `.zentra/threat-model/`) to determine which routes SHOULD have auth

### Mass Assignment (API6 — Unrestricted Access to Sensitive Business Flows)

```
Grep: (req\.body|request\.body|params\.permit|request\.POST|request\.data)
Grep: (\.create\(|\.update\(|\.save\(|\.build\().*req\.body|Object\.assign\(.*req\.body|spread.*req\.body|\{\.\.\.req\.body
```

Check:
- Direct model creation from request body without field filtering
- Missing allowlists (`permit`, `pick`, `select`, DTO validation)
- Fields like `role`, `isAdmin`, `verified`, `balance` that could be set by user input

### BOLA — Broken Object Level Authorization (API1)

```
Grep: (params\.(id|userId|accountId|orderId)|req\.params\.\w+Id)
```

For each parameterized route:
- Does the handler verify that the authenticated user OWNS the requested resource?
- Or does it blindly query `Model.findById(req.params.id)` without ownership check?
- Look for patterns like `where: { id: params.id, userId: currentUser.id }` (good) vs `where: { id: params.id }` (bad)

### Rate Limiting (API4)

```
Grep: (rateLimit|rateLimiter|throttle|express-rate-limit|django-ratelimit|rack-attack|rate_limit)
```

Check:
- Is rate limiting applied globally or per-route?
- Are sensitive endpoints (login, signup, password reset, OTP) rate-limited more aggressively?
- Is rate limiting bypassed for any routes?

---

## Phase 5: Data Exposure Analysis

### Sensitive Data in Responses

Read model/entity definitions and serializers:

```
Grep: (password|passwordHash|secret|token|ssn|socialSecurity|creditCard|cardNumber|cvv|pin)\s*[:=]
```

For each sensitive field found in models, check if:
- It's excluded from API responses (serializer `exclude`, `toJSON` transform, `@JsonIgnore`, `hidden` attribute)
- There's a separate DTO/response class that omits it
- It's returned in any route handler response

### Verbose Error Responses

```
Grep: (res\.status\(500\)\.json|raise|throw).*(?:stack|trace|query|sql|error\.message)
Grep: (app\.use.*err.*res.*json|errorHandler|exception_handler)
```

Check if error handlers expose:
- Stack traces
- SQL queries
- Internal file paths
- Dependency versions

---

## Phase 6: Classify & Report

Write all findings to `.zentra/detailed-findings.md` with `**Source**: zentra-api-scan`.

Map to OWASP API Security Top 10:

| OWASP API | Category |
|-----------|----------|
| API1 | Broken Object Level Authorization (BOLA) |
| API2 | Broken Authentication |
| API3 | Broken Object Property Level Authorization |
| API4 | Unrestricted Resource Consumption |
| API5 | Broken Function Level Authorization (BFLA) |
| API6 | Unrestricted Access to Sensitive Business Flows |
| API7 | Server Side Request Forgery |
| API8 | Security Misconfiguration |
| API9 | Improper Inventory Management |
| API10 | Unsafe Consumption of APIs |

### Severity Rules

| Severity | Criteria |
|----------|----------|
| **Critical** | Exploitable with no auth: RCE, SQLi with data access, leaked production secrets, unauthenticated admin access, privileged container escape |
| **High** | Exploitable with low-privilege auth: stored XSS, IDOR, privilege escalation, SSRF to internal services, public cloud storage, known CVE with exploit |
| **Medium** | Requires specific conditions: reflected XSS, CSRF on state-changing actions, weak crypto in non-critical paths, missing rate limiting, permissive RBAC |
| **Low** | Defense-in-depth issues: missing security headers, verbose errors, outdated non-vulnerable deps, informational disclosure, missing resource limits |

Update `scan-summary.md` and `config.json` as per shared protocol.

---

## Phase 7: Handoff

> **API Scan complete.** Found **N Critical**, **N High**, **N Medium**, **N Low** API security findings.
>
> **Pipeline status:** [read from config.json]
>
> **Recommended next steps:** [show uncompleted pipeline steps]

---

*v1.0 — rafael@kodecraft.dev*
