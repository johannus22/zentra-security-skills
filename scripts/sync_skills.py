"""Generate platform adapters from canonical skills; --check never writes."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generated_files(root=ROOT):
    for skill in sorted((root / "skills").glob("zentra-*")):
        source = (skill / "SKILL.md").read_text(encoding="utf-8-sig")
        _, front, body = source.split("---", 2)
        metadata = dict(line.split(":", 1) for line in front.strip().splitlines())
        name = metadata["name"].strip()
        description = json.loads(metadata["description"].strip())
        body = body.strip() + "\n"
        body = body.replace("](references/", f"]({name}/references/").replace("](scripts/", f"]({name}/scripts/")
        yield root / ".codex" / f"{name}.md", body.encode()
        cursor = f"---\ndescription: {json.dumps(description)}\nalwaysApply: false\n---\n\n{body}"
        yield root / ".cursor/rules" / f"{name}.mdc", cursor.encode()
        command = (f"---\ndescription: {json.dumps(description)}\n---\n\n"
                   f"Load and execute the {name} skill. $ARGUMENTS\n")
        yield root / ".opencode/commands" / f"{name}.md", command.encode()
        # Keep resources alongside the flat legacy entrypoints. Native installs
        # already carry the complete skill directory.
        for folder in ("scripts", "references"):
            for asset in sorted((skill / folder).rglob("*")):
                if not asset.is_file() or "__pycache__" in asset.parts:
                    continue
                relative = asset.relative_to(skill)
                for destination in (".codex", ".cursor/rules"):
                    yield root / destination / name / relative, asset.read_bytes()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, expected in generated_files():
        actual = path.read_bytes() if path.exists() else None
        # Git checkout line-ending conversion does not make an adapter stale.
        if actual is not None and actual.replace(b"\r\n", b"\n") == expected.replace(b"\r\n", b"\n"):
            continue
        stale.append(str(path.relative_to(ROOT)))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if args.check and stale:
        parser.exit(1, "Stale adapters: " + ", ".join(stale) + "\n")
    print(f"Platform adapters {'checked' if args.check else 'synchronized'} ({len(stale)} changes).")


if __name__ == "__main__":
    main()
