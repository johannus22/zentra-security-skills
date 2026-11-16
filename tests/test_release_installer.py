"""Test the downloaded installer from empty workspaces and temporary profiles."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

PROJECT = Path(__file__).resolve().parents[1]
with mock.patch.object(sys, "path", [str(PROJECT / "scripts"), *sys.path]):
    import build_release
    import release_installer


class OfflineReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = tempfile.TemporaryDirectory(prefix="zentra-built-installers-")
        cls.addClassCleanup(cls.assets.cleanup)
        cls.output = Path(cls.assets.name)
        cls.version = build_release.build(cls.output)
        cls.application = cls.output / "zentra-installer.pyz"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="zentra-release-install-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.home = self.root / "test profile"
        self.home.mkdir()
        self.work = self.root / "empty workspace"
        self.work.mkdir()
        overrides = {profile["env"]: "" for profile in release_installer.installer.HARNESSES.values() if "env" in profile}
        overrides.update({profile["env"]: "" for profile in release_installer.EXTRA_TARGETS.values() if "env" in profile})
        self.environment = {**os.environ, **overrides, "HOME": str(self.home), "USERPROFILE": str(self.home),
                            "ZENTRA_PYTHON": sys.executable.replace("\\", "/")}
        self.environment.pop("PYTHONPATH", None)

    def run_application(self, *args, selection=None, no_path=False):
        environment = dict(self.environment)
        if no_path:
            environment["PATH"] = str(Path(sys.executable).parent)
        return subprocess.run([sys.executable, str(self.application), *args, "--home", str(self.home)],
                              cwd=self.work, env=environment, input=selection, capture_output=True, text=True, timeout=60)

    def malformed_bundle(self, entries):
        archive = self.root / "invalid.pyz"
        with zipfile.ZipFile(archive, "w") as zipped:
            for name, raw in entries:
                entry = zipfile.ZipInfo("placeholder")
                entry.filename = name  # Preserve hostile raw names instead of platform normalization.
                zipped.writestr(entry, raw)
        return archive

    def test_pyz_installs_all_skills_without_checkout_git_npm_or_network(self):
        result = self.run_application("--target", "pi", no_path=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        skills = self.home / ".pi/agent/skills"
        self.assertEqual(len(list(skills.glob("zentra-*/SKILL.md"))), 14)
        self.assertEqual((skills / "zentra-verify/scripts/validate_verification.py").read_bytes(),
                         (PROJECT / "skills/zentra-verify/scripts/validate_verification.py").read_bytes())
        self.assertFalse(any(path.is_symlink() for path in skills.rglob("*")))
        self.assertEqual(list(self.work.iterdir()), [])

    def test_installed_verifier_survives_application_and_temporary_bundle_removal(self):
        result = self.run_application("--target", "deepseek")
        self.assertEqual(result.returncode, 0, result.stderr)
        script = self.home / ".dsh/skills/zentra-verify/scripts/validate_verification.py"
        process = subprocess.run([sys.executable, str(script), "--help"], cwd=self.work, env=self.environment, capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--inventory", process.stdout)

    def test_offline_menu_accepts_names_and_preserves_cancellation(self):
        result = self.run_application(selection="0\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Claude Code", result.stdout)
        self.assertIn("Kimi Code", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        result = self.run_application(selection="pi,kimi\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".pi/agent/skills/zentra-dev/SKILL.md").is_file())
        self.assertTrue((self.home / ".kimi-code/skills/zentra-dev/SKILL.md").is_file())

    def test_machine_readable_list_has_all_ten_targets(self):
        result = self.run_application("--list")
        self.assertEqual(result.returncode, 0, result.stderr)
        targets = json.loads(result.stdout)
        self.assertEqual({entry["target"] for entry in targets}, {"claude", "codex", "cursor", "opencode", "pi", "deepseek", "kimi", "gemini", "qwen", "agents"})
        self.assertEqual(list(self.home.iterdir()), [])

    def test_additional_harnesses_use_native_directories(self):
        for name, profile in release_installer.EXTRA_TARGETS.items():
            with self.subTest(target=name):
                result = self.run_application("--target", name)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue((self.home / profile["user"] / "zentra-dev/SKILL.md").is_file())

    def test_codex_and_shared_target_do_not_duplicate_one_root(self):
        result = self.run_application("--target", "codex", "--target", "agents")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("Installed 14"), 1)

    def test_project_target_does_not_write_user_profile(self):
        result = self.run_application("--target", "codex", "--scope", "project", "--project-root", str(self.work))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.work / ".agents/skills/zentra-dev/SKILL.md").is_file())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_update_preserves_local_edits(self):
        first = self.run_application("--target", "kimi")
        self.assertEqual(first.returncode, 0, first.stderr)
        changed = self.home / ".kimi-code/skills/zentra-dev/SKILL.md"
        changed.write_text("Keep this customization", encoding="utf-8")
        second = self.run_application("--target", "kimi")
        self.assertEqual(second.returncode, 1)
        self.assertIn("Locally edited", second.stderr)
        self.assertEqual(changed.read_text(encoding="utf-8"), "Keep this customization")

    def test_dry_run_does_not_install(self):
        result = self.run_application("--target", "cursor", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Would install", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_checksums_cover_both_downloads(self):
        names = set()
        for line in (self.output / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            expected, name = line.split()
            names.add(name)
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(names, {"zentra-installer.pyz", "zentra-installer.zip"})

    def test_windows_and_unix_launchers_are_in_the_friendly_zip(self):
        with zipfile.ZipFile(self.output / "zentra-installer.zip") as zipped:
            self.assertIn("zentra/Install-Zentra.cmd", zipped.namelist())
            self.assertIn("zentra/install.sh", zipped.namelist())
            self.assertEqual(zipped.read("zentra/zentra-installer.pyz"), self.application.read_bytes())
            self.assertTrue(zipped.read("zentra/LICENSE"))
            self.assertTrue(zipped.read("zentra/NOTICE"))
            self.assertTrue(zipped.read("zentra/LICENSES/zentra-upstream-MIT.txt"))
            self.assertEqual((zipped.getinfo("zentra/install.sh").external_attr >> 16) & 0o111, 0o111)

    def test_release_notes_lead_with_the_exact_version_download(self):
        notes = self.root / "release-notes.md"
        notes.write_text(f"# Zentra Security Skills v{self.version}\n\n### Added\n- A change.\n", encoding="utf-8")
        build_release.add_installation_notes(notes, self.version)
        text = notes.read_text(encoding="utf-8")
        self.assertIn(f"/download/v{self.version}/zentra-installer.zip", text)
        self.assertLess(text.index("Install without cloning"), text.index("### Added"))
        self.assertIn("Install-Zentra.cmd", text)
        build_release.add_installation_notes(notes, self.version)
        self.assertEqual(text, notes.read_text(encoding="utf-8"))

    def test_wrong_release_notes_version_is_not_modified(self):
        notes = self.root / "release-notes.md"
        notes.write_text("# Zentra Security Skills v0.0.1\n\n- Old change.\n", encoding="utf-8")
        before = notes.read_bytes()
        with self.assertRaises(ValueError):
            build_release.add_installation_notes(notes, self.version)
        self.assertEqual(before, notes.read_bytes())

    def test_checksums_exclude_unrelated_old_packages_without_deleting_them(self):
        output = self.root / "build"
        output.mkdir()
        old = output / "zentra-security-0.0.1.tgz"
        old.write_bytes(b"older release fixture")
        current = output / f"zentra-security-{self.version}.tgz"
        current.write_bytes(b"current package fixture")
        build_release.build(output)
        manifest = (output / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertNotIn(old.name, manifest)
        self.assertIn(current.name, manifest)
        self.assertEqual(old.read_bytes(), b"older release fixture")

    def test_path_traversal_absolute_and_windows_stream_entries_rejected(self):
        for index, name in enumerate(("bundle/../escape", "bundle//absolute", "bundle/C:/drive", "bundle/name:stream", "bundle/a\\b", "bundle/CON.txt")):
            with self.subTest(name=name):
                archive = self.malformed_bundle([(name, b"bad")])
                target = self.root / f"extract-{index}"
                with self.assertRaises(ValueError):
                    release_installer.extract_bundle(archive, target)
                self.assertFalse(target.exists())

    def test_case_colliding_entries_rejected_before_extraction(self):
        archive = self.malformed_bundle([("bundle/file", b"a"), ("bundle/FILE", b"b")])
        target = self.root / "extract"
        with self.assertRaises(ValueError):
            release_installer.extract_bundle(archive, target)
        self.assertFalse(target.exists())

    def test_zip_symlink_and_size_limits_rejected_before_extraction(self):
        archive = self.root / "symlink.pyz"
        with zipfile.ZipFile(archive, "w") as zipped:
            entry = zipfile.ZipInfo("bundle/link")
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            zipped.writestr(entry, "../outside")
        with self.assertRaises(ValueError):
            release_installer.extract_bundle(archive, self.root / "extract")
        archive = self.malformed_bundle([("bundle/large", b"too large")])
        with mock.patch.object(release_installer, "MAX_FILE_BYTES", 2), self.assertRaises(ValueError):
            release_installer.extract_bundle(archive, self.root / "extract")

    def test_bundle_must_include_matching_version_and_license_notices(self):
        with release_installer.bundle_source(self.application) as source:
            self.assertEqual(release_installer.validate_bundle(source), self.version)
            (source / "VERSION").write_text("999.0.0", encoding="utf-8")
            with self.assertRaises(ValueError):
                release_installer.validate_bundle(source)

    def test_installer_configuration_restores_backend_state(self):
        original_root = release_installer.installer.ROOT
        original_targets = release_installer.installer.HARNESSES
        with release_installer.configured_installer(self.work):
            self.assertEqual(release_installer.installer.ROOT, self.work)
            self.assertIn("claude", release_installer.installer.HARNESSES)
        self.assertIs(release_installer.installer.ROOT, original_root)
        self.assertIs(release_installer.installer.HARNESSES, original_targets)

    def test_extracted_unix_launcher_runs_from_space_path(self):
        candidates = (Path("C:/Program Files/Git/bin/bash.exe"), Path("/bin/bash"))
        bash = next((str(path) for path in candidates if path.is_file()), None)
        if not bash:
            self.skipTest("Bash unavailable")
        extracted = self.root / "download with spaces"
        with zipfile.ZipFile(self.output / "zentra-installer.zip") as zipped:
            zipped.extractall(extracted)  # Trusted test artifact produced above, not an arbitrary download.
        result = subprocess.run([bash, str(extracted / "zentra/install.sh"), "--target", "pi", "--home", str(self.home)],
                                cwd=self.work, env=self.environment, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".pi/agent/skills/zentra-dev/SKILL.md").is_file())

    @unittest.skipUnless(os.name == "nt", "Windows launcher exercised on Windows")
    def test_extracted_windows_launcher_runs_from_space_path(self):
        extracted = self.root / "download with spaces"
        with zipfile.ZipFile(self.output / "zentra-installer.zip") as zipped:
            zipped.extractall(extracted)
        result = subprocess.run([str(extracted / "zentra/Install-Zentra.cmd"), "--target", "kimi", "--home", str(self.home)],
                                cwd=self.work, env=self.environment, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".kimi-code/skills/zentra-dev/SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
