"""Build offline release installers using only the Python standard library."""
import argparse
import hashlib
import io
from pathlib import Path
import stat
import zipapp
import zipfile

import install_skills
from version import check as check_version

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_LAUNCHER = r'''@echo off
setlocal
if defined ZENTRA_PYTHON goto custom
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 goto python
py -3 "%~dp0zentra-installer.pyz" %*
goto done
:python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if errorlevel 1 goto missing
python "%~dp0zentra-installer.pyz" %*
goto done
:custom
"%ZENTRA_PYTHON%" "%~dp0zentra-installer.pyz" %*
goto done
:missing
echo Python 3.11 or newer is required. Download it from https://www.python.org/downloads/.
set "ZENTRA_EXIT=1"
goto finish
:done
set "ZENTRA_EXIT=%errorlevel%"
:finish
if "%~1"=="" pause
exit /b %ZENTRA_EXIT%
'''
UNIX_LAUNCHER = '''#!/usr/bin/env bash
set -euo pipefail
zentra_directory="$(cd "$(dirname "$0")" && pwd)"
if [ -n "${ZENTRA_PYTHON:-}" ]; then
    zentra_python="$ZENTRA_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    zentra_python="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    zentra_python="$(command -v python)"
else
    echo "Python 3.11+ is required: https://www.python.org/downloads/" >&2
    exit 1
fi
exec "$zentra_python" "$zentra_directory/zentra-installer.pyz" "$@"
'''
INSTALL_README = '''Zentra {version} - offline installer

1. Extract this ZIP completely.
2. Windows: double-click Install-Zentra.cmd.
   macOS/Linux: open a terminal in this folder and run: bash install.sh
3. Select your coding harness from the menu.

Requires Python 3.11+. No Git, npm, administrator access or network connection
is needed to install. Download Python from https://www.python.org/downloads/.

Advanced examples:
  python zentra-installer.pyz --target pi --target kimi
  python zentra-installer.pyz --target codex --dry-run
  python zentra-installer.pyz --target agents --scope project --project-root /path/to/project
  python zentra-installer.pyz --list

All 14 skills and verifier resources are bundled. Existing locally edited or
unmanaged skills are protected. This installer copies native skills; it does not
register plugins, change provider credentials, or install legacy slash wrappers.
After installation you can delete this extracted folder; installed skills are
self-contained. To update, download the latest release and run its installer.

Source, documentation and published checksums:
https://github.com/johannus22/zentra-security-skills/releases

License notices are in LICENSE, NOTICE and LICENSES/zentra-upstream-MIT.txt.
'''


def zip_entry(zipped, name, raw, mode=0o644):
    entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    entry.create_system = 3
    entry.external_attr = (stat.S_IFREG | mode) << 16
    entry.compress_type = zipfile.ZIP_DEFLATED
    zipped.writestr(entry, raw)


def build(output, root=ROOT):
    version = check_version(root)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    source = io.BytesIO()
    with zipfile.ZipFile(source, "w") as zipped:
        zip_entry(zipped, "__main__.py", b"from release_installer import main\nraise SystemExit(main())\n")
        for name in ("install_skills.py", "release_installer.py"):
            zip_entry(zipped, name, (root / "scripts" / name).read_bytes())
        for name in ("VERSION", "package.json", "LICENSE", "NOTICE", "LICENSES/zentra-upstream-MIT.txt"):
            zip_entry(zipped, "bundle/" + name, (root / name).read_bytes())
        for name, (folder, files) in install_skills.payloads(root).items():
            for relative, raw in files.items():
                mode = (folder / relative).stat().st_mode & 0o777
                zip_entry(zipped, f"bundle/skills/{name}/{relative}", raw, mode)
    source.seek(0)
    application = output / "zentra-installer.pyz"
    zipapp.create_archive(source, application, interpreter="/usr/bin/env python3")
    application.chmod(0o755)
    archive = output / "zentra-installer.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zip_entry(zipped, "zentra/zentra-installer.pyz", application.read_bytes(), 0o755)
        zip_entry(zipped, "zentra/Install-Zentra.cmd", WINDOWS_LAUNCHER.replace("\n", "\r\n").encode())
        zip_entry(zipped, "zentra/install.sh", UNIX_LAUNCHER.encode(), 0o755)
        zip_entry(zipped, "zentra/README.txt", INSTALL_README.format(version=version).encode())
        for name in ("LICENSE", "NOTICE", "LICENSES/zentra-upstream-MIT.txt"):
            zip_entry(zipped, "zentra/" + name, (root / name).read_bytes())
    checksums = []
    assets = [application, archive]
    package_asset = output / f"zentra-security-{version}.tgz"
    if package_asset.is_file():
        assets.append(package_asset)
    for asset in sorted(assets):
        checksums.append(f"{hashlib.sha256(asset.read_bytes()).hexdigest()}  {asset.name}\n")
    (output / "SHA256SUMS").write_text("".join(checksums), encoding="utf-8", newline="\n")
    return version


def add_installation_notes(path, version):
    content = path.read_text(encoding="utf-8")
    heading, separator, rest = content.partition("\n\n")
    if heading != f"# Zentra Security Skills v{version}" or not separator:
        raise ValueError("Release notes must match the built version")
    if rest.startswith("## Install without cloning\n"):
        return
    base = f"https://github.com/johannus22/zentra-security-skills/releases/download/v{version}"
    instructions = (
        "## Install without cloning\n\n"
        f"**[Download zentra-installer.zip]({base}/zentra-installer.zip)**\n\n"
        "1. Extract the ZIP completely.\n"
        "2. Windows: double-click `Install-Zentra.cmd`. macOS/Linux: run `bash install.sh` inside the extracted `zentra` folder.\n"
        "3. Choose your coding harness from the menu.\n\n"
        "Requires **Python 3.11+**. All 14 skills are bundled; installation works offline without Git, npm, or a repository checkout. "
        "The extracted folder can be deleted afterward.\n\n"
        f"For terminal use, download [zentra-installer.pyz]({base}/zentra-installer.pyz) and run `python zentra-installer.pyz`. "
        "SHA-256 checksums for every asset are in `SHA256SUMS`.\n\n"
    )
    path.write_text(heading + separator + instructions + rest, encoding="utf-8", newline="\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "release-artifacts")
    parser.add_argument("--notes-file", type=Path, help="prepend release download/installation steps to version-matched changelog notes")
    args = parser.parse_args()
    version = build(args.output_dir)
    if args.notes_file is not None:
        add_installation_notes(args.notes_file, version)
    print(f"Built Zentra {version}: zentra-installer.zip, zentra-installer.pyz and SHA256SUMS in {args.output_dir}")


if __name__ == "__main__":
    main()
