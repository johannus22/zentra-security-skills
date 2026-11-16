"""Install complete Zentra skills for native Agent Skills harnesses.

Python 3.11+, standard library only. Copies reviewed local files; never launches
agents, changes model/provider settings, installs dependencies or stores secrets.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = ".zentra-install.json"
HARNESSES = {
    "pi": {"label": "Pi", "commands": ("pi",), "user": ".pi/agent/skills", "project": ".pi/skills", "env": "PI_CODING_AGENT_DIR"},
    "deepseek": {"label": "DeepSeek Harness", "commands": ("dsh",), "user": ".dsh/skills", "project": ".dsh/skills", "env": "DSH_HOME"},
    "kimi": {"label": "Kimi Code", "commands": ("kimi",), "user": ".kimi-code/skills", "project": ".kimi-code/skills", "env": "KIMI_CODE_HOME"},
    "gemini": {"label": "Gemini CLI", "commands": ("gemini",), "user": ".gemini/skills", "project": ".gemini/skills"},
    "qwen": {"label": "Qwen Code", "commands": ("qwen",), "user": ".qwen/skills", "project": ".qwen/skills"},
    "agents": {"label": "Shared Agent Skills", "commands": (), "user": ".agents/skills", "project": ".agents/skills"},
}


class InstallError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InstallError(message)


def linked(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def safe_child(root, relative):
    require(isinstance(relative, str) and relative, "Empty installation path")
    parts = relative.split("/")
    require(not PurePosixPath(relative).is_absolute() and all(part not in ("", ".", "..") for part in parts), "Unsafe installation path")
    require(not any(char in relative for char in ("\\", ":", "\0")) and not any(ord(char) < 32 for char in relative), "Unsafe installation path")
    require(all(not part.endswith((".", " ")) for part in parts), "Ambiguous installation path")
    result = root
    for part in parts:
        result = result / part
        require(not linked(result), f"Refusing linked resource: {result}")
    require(result.resolve().is_relative_to(root.resolve()), "Installation path escapes its root")
    return result


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def project_root(cwd):
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def destination(target, scope="user", *, home=None, project=None, environ=None):
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else Path(home)
    profile = HARNESSES[target]
    if scope == "project":
        base = Path(project) if project is not None else project_root(Path.cwd())
        require(base.is_dir(), f"Project root does not exist: {base}")
        return base.resolve() / profile["project"]
    override = environ.get(profile.get("env", ""), "").strip()
    if override:
        return Path(override).expanduser().absolute() / "skills"
    return home.expanduser().absolute() / profile["user"]


def detected(home=None, environ=None, which=shutil.which):
    result = []
    for name, profile in HARNESSES.items():
        if name == "agents":
            continue  # Shared discovery is an explicit choice, never a duplicate in All.
        root = destination(name, home=home, environ=environ)
        profile_root = (Path.home() if home is None else Path(home)) / profile["detect_dir"] if "detect_dir" in profile else root.parent
        if any(which(command) for command in profile["commands"]) or profile_root.is_dir():
            result.append(name)
    return result


def payloads(source=ROOT):
    result = {}
    for folder in sorted((source / "skills").glob("zentra-*")):
        require(folder.is_dir() and not linked(folder), f"Invalid canonical skill: {folder}")
        require((folder / "SKILL.md").is_file(), f"Missing SKILL.md: {folder}")
        files = {}
        for path in sorted(folder.rglob("*")):
            relative = path.relative_to(folder).as_posix()
            if "__pycache__" in path.relative_to(folder).parts or path.suffix in (".pyc", ".pyo"):
                continue
            safe_child(folder, relative)
            if path.is_file():
                require(relative != MARKER, "Installation marker cannot be a source resource")
                files[relative] = path.read_bytes()
            else:
                require(path.is_dir(), f"Nonregular source resource: {path}")
        result[folder.name] = (folder.resolve(), files)
    require(result, "No canonical Zentra skills found")
    return result


def load_marker(path):
    require(path.is_file() and path.stat().st_size <= 1024 * 1024, f"Invalid installer marker: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(type(value) is dict and value.get("schema_version") == 1 and value.get("package") == "zentra-security", f"Unrecognized installer marker: {path}")
    hashes = value.get("files")
    require(type(hashes) is dict and "SKILL.md" in hashes, f"Incomplete installer marker: {path}")
    require(all(type(key) is str and type(digest) is str and re.fullmatch(r"[a-f0-9]{64}", digest) for key, digest in hashes.items()), f"Invalid resource hashes: {path}")
    require(MARKER not in hashes, "Marker cannot manage itself")
    return hashes


def plan_install(root, bundles):
    # An explicitly selected skills root may itself be a configured alias.
    # Once resolved, no child symlink/junction is traversed during an update.
    root = root.expanduser().absolute().resolve()
    require(not root.exists() or root.is_dir(), f"Skills root is not a directory: {root}")
    plans = []
    for name, (source, files) in bundles.items():
        target = root / name
        require(not root.is_relative_to(source), "Skills destination cannot be inside a canonical skill")
        if linked(target):
            require(target.resolve() == source, f"Existing skill link has a different owner: {target}")
            plans.append(("linked", target, files, {}, source))
            continue
        require(target.resolve() != source, "Source and installation destination are identical")
        require(not target.exists() or target.is_dir(), f"Skill destination is not a directory: {target}")
        previous = {}
        if target.exists():
            marker = safe_child(target, MARKER)
            require(marker.is_file(), f"Existing unmanaged skill; leaving it untouched: {target}")
            previous = load_marker(marker)
            for relative, expected in previous.items():
                path = safe_child(target, relative)
                require(not path.exists() or path.is_file(), f"Managed resource is not a regular file: {path}")
                require(not path.exists() or sha(path.read_bytes()) == expected, f"Locally edited skill; leaving it untouched: {path}")
        for relative in files:
            path = safe_child(target, relative)
            require(not path.exists() or path.is_file(), f"Resource is not a regular file: {path}")
            require(not path.exists() or relative in previous, f"Unmanaged file conflicts with an update: {path}")
            for parent in path.parents:
                if parent == target:
                    break
                require(not parent.exists() or parent.is_dir(), f"Resource parent is not a directory: {parent}")
        # Validate even obsolete manifest paths before any file may be removed.
        for relative in previous:
            safe_child(target, relative)
        plans.append(("update" if target.exists() else "install", target, files, previous, source))
    return plans


def atomic_write(path, raw, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".zentra-write-", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
        if mode is not None:
            os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_plans(plans):
    for action, target, files, previous, source in plans:
        if action == "linked":
            continue
        target.mkdir(parents=True, exist_ok=True)
        for relative, raw in files.items():
            path = safe_child(target, relative)
            if not path.exists() or path.read_bytes() != raw:
                atomic_write(path, raw, (source / relative).stat().st_mode & 0o777)
        for relative in previous.keys() - files.keys():
            safe_child(target, relative).unlink(missing_ok=True)
        marker = {"schema_version": 1, "package": "zentra-security", "files": {name: sha(raw) for name, raw in files.items()}}
        atomic_write(safe_child(target, MARKER), (json.dumps(marker, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def choose_targets(found):
    names = list(HARNESSES)
    print("\nChoose where to install Zentra:")
    for index, name in enumerate(names, 1):
        status = " (detected)" if name in found else ""
        print(f"  {index}) {HARNESSES[name]['label']}{status}")
    print("  a) All detected harnesses\n  0) Cancel")
    raw = input("Select numbers or names, separated by commas: ").strip().lower()
    if raw in ("", "0", "cancel"):
        return []
    if raw in ("a", "all"):
        return ["all"]
    result = []
    for token in raw.split(","):
        token = token.strip()
        if token.isdigit() and 1 <= int(token) <= len(names):
            token = names[int(token) - 1]
        require(token in HARNESSES, f"Unknown selection: {token}")
        result.append(token)
    return result


def main(argv=None, *, interactive=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", choices=(*HARNESSES, "all"), help="repeat to install for multiple harnesses; all selects detected native harnesses")
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--skills-dir", type=Path, help="explicit custom skills root; one target only")
    parser.add_argument("--home", type=Path, help="alternate user profile for installation/detection")
    parser.add_argument("--dry-run", action="store_true", help="preflight and print destinations without writing")
    parser.add_argument("--detect", action="store_true", help="print detected native target IDs without writing")
    parser.add_argument("--list", action="store_true", help="print supported targets and their actual destinations as JSON")
    args = parser.parse_args(argv)
    try:
        require(sys.version_info >= (3, 11), "Python 3.11 or newer is required")
        require(args.project_root is None or args.scope == "project", "--project-root requires --scope project")
        found = detected(home=args.home)
        if args.detect:
            require(not args.target and not args.skills_dir, "--detect cannot install targets")
            print("\n".join(found), end="\n" if found else "")
            return 0
        if args.list:
            print(json.dumps([{ "target": name, "label": profile["label"], "detected": name in found,
                                "destination": str(destination(name, args.scope, home=args.home, project=args.project_root))}
                              for name, profile in HARNESSES.items()], indent=2))
            return 0
        targets = args.target or (["agents"] if args.skills_dir else [])
        if not targets and interactive:
            targets = choose_targets(found)
            if not targets:
                print("Cancelled. No skills installed.")
                return 0
        require(targets, "Select --target pi, deepseek, kimi, gemini, qwen or agents; use --list to inspect destinations")
        require("all" not in targets or len(targets) == 1, "--target all cannot be combined with another target")
        if targets == ["all"]:
            targets = found
            require(targets, "No native harness detected; choose an explicit --target or --target agents")
        targets = list(dict.fromkeys(targets))
        require(args.skills_dir is None or len(targets) == 1, "--skills-dir requires one target")
        bundles = payloads(ROOT)
        plans = []
        destinations = []
        for name in targets:
            root = args.skills_dir if args.skills_dir is not None else destination(name, args.scope, home=args.home, project=args.project_root)
            resolved = root.expanduser().absolute().resolve()
            if resolved in destinations:
                continue
            destinations.append(resolved)
            plans.extend(plan_install(root, bundles))
        if not args.dry_run:
            apply_plans(plans)
        for root in destinations:
            print(f"{'Would install' if args.dry_run else 'Installed'} {len(bundles)} Zentra skill bundles: {root}")
        print("Native discovery uses SKILL.md and its adjacent resources. Ask your harness to load zentra-dev or zentra-verify.")
        return 0
    except (InstallError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("No selection received. Use --target for unattended installation.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
