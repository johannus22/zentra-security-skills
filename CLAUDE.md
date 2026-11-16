# Zentra contributor guidance

Read [AGENTS.md](AGENTS.md) for the skill catalog, evidence/safety contract, platform delivery and validation commands. This is a 14-skill instruction framework with a Python evidence validator and isolated fixture tests, not an application server.

Edit canonical `skills/zentra-*/SKILL.md` and bundled scripts/references. Run `python scripts/sync_skills.py` to regenerate platform adapters; do not hand-edit copies. Validate with `python scripts/check_framework.py`, `python -m unittest discover -s tests -v` and `git diff --check`.

Preserve existing user changes. Static scanning does not authorize source edits or project execution. Remediation needs per-patch approval; DAST needs explicit scope authorization. A completed scan is not independent verification or certification.
