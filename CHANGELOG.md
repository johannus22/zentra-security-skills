# Changelog

## [1.0.0] - 2026-04-22

### Added

- **edward-code-recon** (v2.0): Static analysis skill for OWASP Top 10 vulnerability detection. Scans for hardcoded secrets, injection flaws, broken access control, cryptographic failures, security misconfigurations, SSRF, and authentication weaknesses. Spawns parallel subagents for large codebases. Produces structured reports in `.edward/` directory.
- **edward-pentester** (v1.0): Dynamic penetration testing skill that validates static findings against live targets using Playwright MCP. Captures screenshot evidence and PoC logs. Supports Burp Suite and Caido MCP for passive scanning. Requires explicit authorization before testing.
- Plugin packaging for Claude Code marketplace with self-hosted marketplace support.
