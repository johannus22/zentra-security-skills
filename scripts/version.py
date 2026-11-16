"""Keep semantic release versions and GitHub tag/changelog metadata consistent.

Python 3.11+, standard library only. Never commits, tags, pushes or publishes.
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ("package.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json",
             ".claude-plugin/marketplace.json")
RELEASE_FILES = (*MANIFESTS, "VERSION", "CHANGELOG.md", "README.md")
README_VERSION = re.compile(r"(?m)^(\*\*Version )(\S+)( [^\n]*\*\*)$")
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)


def parse_version(value):
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError("Use MAJOR.MINOR.PATCH, optionally followed by -rc.1 or another SemVer prerelease.")
    if match[4] and any(item.isdigit() and len(item) > 1 and item.startswith("0") for item in match[4].split(".")):
        raise ValueError("Numeric prerelease identifiers cannot have leading zeroes.")
    return match


def current_version(root=ROOT):
    value = (root / "VERSION").read_text(encoding="utf-8-sig").strip()
    parse_version(value)
    return value


def manifests(root):
    result = {}
    for relative in MANIFESTS:
        data = json.loads((root / relative).read_text(encoding="utf-8-sig"))
        if relative.endswith("marketplace.json"):
            entries = [item for item in data["plugins"] if item.get("name") == "zentra"]
            if len(entries) != 1:
                raise ValueError("Claude marketplace must contain exactly one Zentra entry.")
            target = entries[0]
        else:
            target = data
        result[relative] = (data, target)
    return result


def release_notes(version, root=ROOT):
    parse_version(version)
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8-sig")
    headers = list(re.finditer(r"(?m)^## \[([^\]]+)\][^\n]*\n", changelog))
    matches = [index for index, item in enumerate(headers) if item[1] == version]
    if len(matches) != 1:
        raise ValueError(f"CHANGELOG.md must contain exactly one [{version}] entry.")
    index = matches[0]
    end = headers[index + 1].start() if index + 1 < len(headers) else len(changelog)
    notes = changelog[headers[index].end():end].strip()
    if not re.search(r"(?m)^[-*] \S", notes):
        raise ValueError(f"Add release notes under [{version}] before releasing.")
    return f"# Zentra Security Skills v{version}\n\n{notes}\n"


def check(root=ROOT, tag=None):
    version = current_version(root)
    errors = []
    for relative, (_, target) in manifests(root).items():
        if target.get("version") != version:
            errors.append(f"{relative}: expected version {version}, found {target.get('version')!r}")
    readme = (root / "README.md").read_text(encoding="utf-8-sig")
    headings = list(README_VERSION.finditer(readme))
    if len(headings) != 1:
        errors.append("README.md must contain exactly one '**Version MAJOR.MINOR.PATCH ...**' heading.")
    elif headings[0][2] != version:
        errors.append(f"README.md: expected version {version}, found {headings[0][2]!r}")
    if tag is not None and tag != "v" + version:
        errors.append(f"Tag must be v{version}, received {tag!r}.")
    try:
        release_notes(version, root)
    except ValueError as error:
        errors.append(str(error))
    if errors:
        raise ValueError("\n".join(errors))
    return version


def set_version(version, root=ROOT):
    parse_version(version)
    # Preflight every input before writing any manifest. Preserve unrelated keys.
    values = manifests(root)
    changelog_path = root / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8-sig")
    readme_path = root / "README.md"
    readme = readme_path.read_text(encoding="utf-8-sig")
    if len(list(README_VERSION.finditer(readme))) != 1:
        raise ValueError("README.md must contain exactly one '**Version MAJOR.MINOR.PATCH ...**' heading.")
    readme = README_VERSION.sub(lambda match: match[1] + version + match[3], readme)
    current_version(root)
    heading = re.compile(r"(?m)^## \[" + re.escape(version) + r"\][^\n]*(?:\n|$)")
    if not heading.search(changelog):
        title = f"## [{version}] - {date.today().isoformat()}\n"
        unreleased = re.compile(r"(?m)^## \[Unreleased\][^\n]*\n")
        if unreleased.search(changelog):
            changelog = unreleased.sub(lambda _: title, changelog, count=1)
        else:
            if not changelog.startswith("# Changelog\n"):
                raise ValueError("Expected CHANGELOG.md to start with '# Changelog'.")
            changelog = changelog.replace("# Changelog\n", "# Changelog\n\n" + title + "\n### Changed\n\n", 1)
    updates = {root / "VERSION": version + "\n", changelog_path: changelog, readme_path: readme}
    for relative, (data, target) in values.items():
        target["version"] = version
        updates[root / relative] = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    for path, content in updates.items():
        path.write_text(content, encoding="utf-8", newline="\n")


def bump_version(part, root=ROOT):
    match = parse_version(current_version(root))
    if match[4]:
        raise ValueError("Use 'set' to choose a version when the current version is a prerelease.")
    numbers = [int(match[index]) for index in (1, 2, 3)]
    index = ("major", "minor", "patch").index(part)
    numbers[index] += 1
    numbers[index + 1:] = [0] * (2 - index)
    version = ".".join(map(str, numbers))
    set_version(version, root)
    return version


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    verify = subcommands.add_parser("check", help="Check versions, release notes and an optional v-prefixed tag")
    verify.add_argument("--tag")
    subcommands.add_parser("show", help="Print the canonical version")
    subcommands.add_parser("notes", help="Print changelog-derived release notes")
    choose = subcommands.add_parser("set", help="Synchronize an explicit version; never create a Git tag")
    choose.add_argument("version")
    increment = subcommands.add_parser("bump", help="Increment a stable release; edit changelog notes afterward")
    increment.add_argument("part", choices=("patch", "minor", "major"))
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            print(f"Release metadata checked: v{check(tag=args.tag)}")
        elif args.command == "show":
            print(current_version())
        elif args.command == "notes":
            print(release_notes(current_version()), end="")
        else:
            version = bump_version(args.part) if args.command == "bump" else args.version
            if args.command == "set":
                set_version(version)
            print(f"Version set to {version}. Review CHANGELOG.md and run 'python scripts/version.py check'.")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
