"""Check skill discovery, packaged resources, versions and generated adapters."""
import json
import sys

from sync_skills import ROOT, generated_files
from version import check as check_version


def main():
    errors = []
    try:
        check_version(ROOT)
    except (OSError, ValueError, KeyError) as error:
        errors.append(str(error))
    skills = sorted((ROOT / "skills").glob("zentra-*"))
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8-sig"))
    for folder in skills:
        source = (folder / "SKILL.md").read_text(encoding="utf-8-sig")
        try:
            _, front, body = source.split("---", 2)
            fields = dict(line.split(":", 1) for line in front.strip().splitlines())
            if fields["name"].strip() != folder.name or not json.loads(fields["description"].strip()) or not body.strip():
                raise ValueError("invalid frontmatter/body")
        except (ValueError, KeyError, json.JSONDecodeError):
            errors.append(f"Invalid skill entrypoint: {folder.name}")
        metadata = folder / "agents/openai.yaml"
        if not metadata.exists() or "$" + folder.name not in metadata.read_text(encoding="utf-8-sig"):
            errors.append(f"Missing invocation metadata: {folder.name}")
        for doc in ("README.md", "AGENTS.md", ".codex/AGENTS.md"):
            if folder.name not in (ROOT / doc).read_text(encoding="utf-8-sig"):
                errors.append(f"{folder.name} missing from {doc}")
    for path, expected in generated_files():
        if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != expected.replace(b"\r\n", b"\n"):
            errors.append(f"Stale/missing adapter: {path.relative_to(ROOT)}")
    for manifest in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        if json.loads((ROOT / manifest).read_text(encoding="utf-8-sig"))["version"] != package["version"]:
            errors.append(f"Version mismatch: {manifest}")
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8-sig"))
    if marketplace["plugins"][0]["version"] != package["version"]:
        errors.append("Version mismatch: Claude marketplace")
    for required in ("skills/", ".codex/", ".cursor/", ".opencode/", "scripts/"):
        if required not in package["files"]:
            errors.append(f"Missing package resource tree: {required}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Framework checked: {len(skills)} skills, consistent adapters/resources, version {package['version']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
