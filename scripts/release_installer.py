"""Offline entrypoint bundled into the downloadable Zentra Python zip application."""
from contextlib import contextmanager
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile

import install_skills as installer

ROOT = Path(__file__).resolve().parents[1]
EXTRA_TARGETS = {
    "claude": {"label": "Claude Code", "commands": ("claude",), "user": ".claude/skills", "project": ".claude/skills", "env": "CLAUDE_CONFIG_DIR"},
    "codex": {"label": "Codex", "commands": ("codex",), "user": ".agents/skills", "project": ".agents/skills", "detect_dir": ".codex"},
    "cursor": {"label": "Cursor", "commands": ("cursor", "agent"), "user": ".cursor/skills", "project": ".cursor/skills"},
    "opencode": {"label": "OpenCode", "commands": ("opencode",), "user": ".config/opencode/skills", "project": ".opencode/skills"},
}
MAX_FILES = 5000
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024


def extract_bundle(archive, destination):
    """Extract only regular bundle files after validating the complete inventory."""
    planned = []
    seen = set()
    total = 0
    with zipfile.ZipFile(archive) as zipped:
        for entry in zipped.infolist():
            if not entry.orig_filename.startswith("bundle/"):
                continue  # Application modules are imported from the zip, not extracted.
            installer.require(entry.orig_filename == entry.filename, "Noncanonical installer resource path")
            installer.require("\\" not in entry.orig_filename, "Noncanonical installer resource path")
            name = entry.filename.removesuffix("/")
            key = name.casefold()
            installer.require(key not in seen, "Duplicate or case-colliding installer resource")
            seen.add(key)
            installer.require(len(seen) <= MAX_FILES, "Installer file-count limit exceeded")
            relative = name.removeprefix("bundle/")
            installer.require(relative and relative != "bundle", "Invalid bundle path")
            for part in PurePosixPath(relative).parts:
                stem = part.split(".", 1)[0].rstrip(" ").upper()
                installer.require(stem not in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}, "Reserved Windows resource path")
            installer.safe_child(destination, relative)
            mode = entry.external_attr >> 16
            kind = stat.S_IFMT(mode)
            allowed = (0, stat.S_IFDIR) if entry.is_dir() else (0, stat.S_IFREG)
            installer.require(kind in allowed and not entry.flag_bits & 1, "Linked, special or encrypted installer resource")
            installer.require(0 <= entry.file_size <= MAX_FILE_BYTES, "Installer resource is too large")
            total += entry.file_size
            installer.require(total <= MAX_TOTAL_BYTES, "Installer size limit exceeded")
            planned.append((entry, relative, mode))
        installer.require(planned, "Installer contains no bundled skills")
        for entry, relative, mode in planned:
            path = installer.safe_child(destination, relative)
            if entry.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            with zipped.open(entry) as handle:
                raw = handle.read(MAX_FILE_BYTES + 1)
            installer.require(len(raw) == entry.file_size, "Installer resource size mismatch")
            installer.atomic_write(path, raw, (mode & 0o777) if mode else 0o644)


def validate_bundle(root):
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    installer.require(re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?", version), "Invalid bundled version")
    package = json.loads((root / "package.json").read_text(encoding="utf-8"))
    installer.require(package.get("name") == "zentra-security" and package.get("version") == version, "Bundled version metadata disagrees")
    for name in ("LICENSE", "NOTICE", "LICENSES/zentra-upstream-MIT.txt", "skills/zentra-verify/scripts/validate_verification.py", "skills/zentra-verify/references/verification.schema.json"):
        installer.require(installer.safe_child(root, name).is_file(), f"Installer is missing {name}")
    installer.require(len(installer.payloads(root)) == 14, "Installer must contain all 14 skills")
    return version


@contextmanager
def bundle_source(archive=None):
    archive = Path(sys.argv[0]) if archive is None else Path(archive)
    if archive.is_file() and zipfile.is_zipfile(archive):
        with tempfile.TemporaryDirectory(prefix="zentra-offline-install-") as temporary:
            root = Path(temporary) / "bundle"
            extract_bundle(archive, root)
            yield root
    else:
        yield ROOT


@contextmanager
def configured_installer(root):
    previous_root = installer.ROOT
    previous_targets = installer.HARNESSES
    installer.ROOT = root
    installer.HARNESSES = {**EXTRA_TARGETS, **previous_targets}
    try:
        yield
    finally:
        installer.ROOT = previous_root
        installer.HARNESSES = previous_targets


def main(argv=None):
    try:
        installer.require(sys.version_info >= (3, 11), "Python 3.11 or newer is required. Install it from https://www.python.org/downloads/.")
        with bundle_source() as root:
            version = validate_bundle(root)
            arguments = sys.argv[1:] if argv is None else argv
            if "--list" not in arguments and "--detect" not in arguments:
                print(f"Zentra {version} - offline skill installer")
                print("No Git, npm or network connection required. Skills are copied to the selected harness.")
            with configured_installer(root):
                return installer.main(argv, interactive=True)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print(f"Installation stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
