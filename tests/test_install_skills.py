"""Native harness installation tests use disposable user/project profiles only."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("native_install", PROJECT / "scripts/install_skills.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class NativeInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="zentra-harness-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.home = self.root / "test profile"
        self.home.mkdir()
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.bundles = installer.payloads()
        self.overrides = {profile["env"]: "" for profile in installer.HARNESSES.values() if "env" in profile}
        self.addCleanup(mock.patch.stopall)
        mock.patch.dict(os.environ, self.overrides).start()

    def invoke(self, *arguments):
        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()) as errors:
            code = installer.main([*arguments, "--home", str(self.home)])
        return code, output.getvalue(), errors.getvalue()

    def install(self, target="pi"):
        code, output, errors = self.invoke("--target", target)
        self.assertEqual(code, 0, output + errors)
        return installer.destination(target, home=self.home, environ={})

    def test_all_user_roots_and_complete_resources(self):
        for name, profile in installer.HARNESSES.items():
            with self.subTest(target=name):
                root = self.install(name)
                self.assertEqual(root, self.home / profile["user"])
                self.assertEqual({folder.name for folder in root.iterdir()}, self.bundles.keys())
                for skill, (_, files) in self.bundles.items():
                    for relative, content in files.items():
                        self.assertEqual((root / skill / relative).read_bytes(), content)
                    self.assertTrue((root / skill / installer.MARKER).is_file())

    def test_project_roots_and_environment_isolation(self):
        for name, profile in installer.HARNESSES.items():
            with self.subTest(target=name):
                code, output, errors = self.invoke("--target", name, "--scope", "project", "--project-root", str(self.project))
                self.assertEqual(code, 0, output + errors)
                self.assertTrue((self.project / profile["project"] / "zentra-verify/references/verification.schema.json").is_file())
                self.assertFalse((self.home / profile["user"]).exists())

    def test_provider_home_overrides(self):
        for name in ("pi", "deepseek", "kimi"):
            variable = installer.HARNESSES[name]["env"]
            selected = self.root / f"custom {name} home"
            self.assertEqual(installer.destination(name, home=self.home, environ={variable: str(selected)}), selected / "skills")
            self.assertEqual(installer.destination(name, "project", home=self.home, project=self.project, environ={variable: str(selected)}), self.project / installer.HARNESSES[name]["project"])

    def test_nearest_project_root_accepts_git_file_and_fallback(self):
        child = self.project / "src/nested"
        child.mkdir(parents=True)
        self.assertEqual(installer.project_root(child), child)
        (self.project / ".git").write_text("gitdir: ../external", encoding="utf-8")
        self.assertEqual(installer.project_root(child), self.project)

    def test_detection_uses_binaries_or_profile_directories(self):
        (self.home / ".dsh").mkdir()
        found = installer.detected(self.home, environ={}, which=lambda command: "/bin/pi" if command == "pi" else None)
        self.assertEqual(found, ["pi", "deepseek"])
        self.assertNotIn("agents", found)

    def test_dry_run_creates_no_files(self):
        code, output, errors = self.invoke("--target", "kimi", "--dry-run")
        self.assertEqual(code, 0, errors)
        self.assertIn("Would install", output)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_all_installs_only_detected_profiles(self):
        with mock.patch.object(installer, "detected", return_value=["pi", "kimi"]):
            code, output, errors = self.invoke("--target", "all")
        self.assertEqual(code, 0, errors)
        self.assertTrue((self.home / ".pi/agent/skills/zentra-dev/SKILL.md").is_file())
        self.assertTrue((self.home / ".kimi-code/skills/zentra-dev/SKILL.md").is_file())
        self.assertFalse((self.home / ".agents").exists())

    def test_repeated_targets_deduplicate(self):
        code, output, errors = self.invoke("--target", "pi", "--target", "pi")
        self.assertEqual(code, 0, errors)
        self.assertEqual(output.count("Installed 14"), 1)

    def test_custom_skills_root_and_profile_configuration_preserved(self):
        config = self.home / "config.toml"
        config.write_text('api_key = "fixture-only-not-a-real-secret"\n', encoding="utf-8")
        selected = self.root / "custom skills"
        code, output, errors = self.invoke("--skills-dir", str(selected))
        self.assertEqual(code, 0, errors)
        self.assertTrue((selected / "zentra-dev/SKILL.md").is_file())
        self.assertEqual(config.read_text(encoding="utf-8"), 'api_key = "fixture-only-not-a-real-secret"\n')

    def test_idempotent_updates_preserve_extra_user_files(self):
        root = self.install()
        note = root / "zentra-dev/local-notes.txt"
        note.write_text("Keep my notes", encoding="utf-8")
        self.install()
        self.assertEqual(note.read_text(encoding="utf-8"), "Keep my notes")

    def test_locally_edited_managed_file_blocks_all_updates(self):
        root = self.install()
        altered = root / "zentra-verify/scripts/validate_verification.py"
        altered.write_text("Local customization", encoding="utf-8")
        before = {str(path): path.read_bytes() for path in root.rglob("*") if path.is_file()}
        code, _, errors = self.invoke("--target", "pi")
        self.assertEqual(code, 1)
        self.assertIn("Locally edited", errors)
        self.assertEqual(before, {str(path): path.read_bytes() for path in root.rglob("*") if path.is_file()})

    def test_unmanaged_skill_prevents_any_partial_install(self):
        root = installer.destination("pi", home=self.home, environ={})
        existing = root / "zentra-verify"
        existing.mkdir(parents=True)
        (existing / "SKILL.md").write_text("User-owned skill", encoding="utf-8")
        code, _, errors = self.invoke("--target", "pi")
        self.assertEqual(code, 1)
        self.assertIn("unmanaged", errors)
        self.assertFalse((root / "zentra-api-scan").exists())

    def test_multiple_targets_preflight_before_first_write(self):
        root = installer.destination("kimi", home=self.home, environ={})
        (root / "zentra-dev").mkdir(parents=True)
        code, _, errors = self.invoke("--target", "pi", "--target", "kimi")
        self.assertEqual(code, 1)
        self.assertIn("unmanaged", errors)
        self.assertFalse((self.home / ".pi").exists())

    def test_missing_managed_resource_is_repaired(self):
        root = self.install()
        resource = root / "zentra-verify/references/verification.schema.json"
        resource.unlink()
        self.install()
        self.assertEqual(resource.read_bytes(), self.bundles["zentra-verify"][1]["references/verification.schema.json"])

    def test_obsolete_owned_file_removed_but_unowned_file_kept(self):
        root = self.install()
        skill = root / "zentra-dev"
        old = skill / "obsolete.txt"
        old.write_bytes(b"old bundled content")
        note = skill / "user.txt"
        note.write_text("retain", encoding="utf-8")
        marker = skill / installer.MARKER
        data = json.loads(marker.read_text(encoding="utf-8"))
        data["files"]["obsolete.txt"] = installer.sha(old.read_bytes())
        marker.write_text(json.dumps(data), encoding="utf-8")
        self.install()
        self.assertFalse(old.exists())
        self.assertTrue(note.is_file())

    def test_unsafe_marker_paths_do_not_escape_skill_directory(self):
        root = self.install()
        marker = root / "zentra-dev" / installer.MARKER
        data = json.loads(marker.read_text(encoding="utf-8"))
        data["files"]["../victim.txt"] = installer.sha(b"victim")
        marker.write_text(json.dumps(data), encoding="utf-8")
        victim = root / "victim.txt"
        victim.write_bytes(b"victim")
        code, _, errors = self.invoke("--target", "pi")
        self.assertEqual(code, 1)
        self.assertEqual(victim.read_bytes(), b"victim")

    def test_path_traversal_and_windows_streams_rejected(self):
        for value in ("../escape", "/absolute", "C:/absolute", "name:stream", "a\\b", "a//b", "a/./b", "file."):
            with self.subTest(path=value), self.assertRaises(installer.InstallError):
                installer.safe_child(self.root, value)

    def test_foreign_symlink_and_broken_symlink_rejected(self):
        root = installer.destination("pi", home=self.home, environ={})
        root.mkdir(parents=True)
        outside = self.root / "outside"
        outside.mkdir()
        link = root / "zentra-dev"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Unprivileged symlinks unavailable")
        code, _, _ = self.invoke("--target", "pi")
        self.assertEqual(code, 1)
        self.assertEqual(list(outside.iterdir()), [])
        outside.rmdir()
        code, _, _ = self.invoke("--target", "pi")
        self.assertEqual(code, 1)

    def test_known_link_to_canonical_skill_is_kept_without_writes(self):
        root = installer.destination("pi", home=self.home, environ={})
        root.mkdir(parents=True)
        link = root / "zentra-dev"
        try:
            link.symlink_to(self.bundles["zentra-dev"][0], target_is_directory=True)
        except OSError:
            self.skipTest("Unprivileged symlinks unavailable")
        self.install()
        self.assertTrue(link.is_symlink())
        self.assertFalse((self.bundles["zentra-dev"][0] / installer.MARKER).exists())

    def test_nested_symlink_resource_refuses_update(self):
        root = self.install()
        resource = root / "zentra-verify/references/verification.schema.json"
        outside = self.root / "outside.json"
        outside.write_bytes(resource.read_bytes())
        resource.unlink()
        try:
            resource.symlink_to(outside)
        except OSError:
            self.skipTest("Unprivileged symlinks unavailable")
        code, _, errors = self.invoke("--target", "pi")
        self.assertEqual(code, 1)
        self.assertIn("linked resource", errors)

    def test_destination_cannot_be_inside_source_bundle(self):
        source = self.bundles["zentra-dev"][0]
        with self.assertRaises(installer.InstallError):
            installer.plan_install(source / "nested", self.bundles)

    def test_installed_verifier_runs_without_harness_or_model(self):
        root = self.install("deepseek")
        script = root / "zentra-verify/scripts/validate_verification.py"
        process = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--inventory", process.stdout)

    def test_invalid_project_options_fail_without_writing(self):
        for arguments in (("--target", "pi", "--project-root", str(self.project)),
                          ("--target", "pi", "--scope", "project", "--project-root", str(self.root / "missing"))):
            with self.subTest(arguments=arguments):
                self.assertEqual(self.invoke(*arguments)[0], 1)
                self.assertEqual(list(self.home.iterdir()), [])

    def test_all_cannot_silently_ignore_an_explicit_target(self):
        code, _, errors = self.invoke("--target", "all", "--target", "pi")
        self.assertEqual(code, 1)
        self.assertIn("cannot be combined", errors)
        self.assertEqual(list(self.home.iterdir()), [])

    @unittest.skipIf(os.name == "nt", "Executable permission bits apply on Unix")
    def test_executable_helper_permissions_are_preserved(self):
        source = self.root / "source/skills/zentra-fixture"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text('---\nname: zentra-fixture\ndescription: "Fixture"\n---\n', encoding="utf-8")
        helper = source / "check.sh"
        helper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        helper.chmod(0o755)
        bundles = installer.payloads(self.root / "source")
        target = self.root / "installed"
        installer.apply_plans(installer.plan_install(target, bundles))
        self.assertEqual((target / "zentra-fixture/check.sh").stat().st_mode & 0o777, 0o755)

    def wrapper_environment(self):
        return {**os.environ, **self.overrides, "HOME": str(self.home), "USERPROFILE": str(self.home),
                "ZENTRA_PYTHON": sys.executable.replace("\\", "/")}

    def bash(self):
        candidates = (Path("C:/Program Files/Git/bin/bash.exe"), Path("/bin/bash"))
        return next((str(path) for path in candidates if path.is_file()), None)

    def test_bash_wrapper_passes_native_target_and_space_paths(self):
        bash = self.bash()
        if not bash:
            self.skipTest("Bash unavailable")
        command = [bash, str(PROJECT / "install.sh"), "--target", "pi", "--home", str(self.home)]
        result = subprocess.run(command, env=self.wrapper_environment(), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".pi/agent/skills/zentra-dev/SKILL.md").is_file())

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper exercised on Windows")
    def test_powershell_wrapper_passes_native_target_and_space_paths(self):
        result = subprocess.run(["powershell", "-NoProfile", "-File", str(PROJECT / "install.ps1"), "-Target", "kimi", "-ProfileRoot", str(self.home)],
                                env=self.wrapper_environment(), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".kimi-code/skills/zentra-dev/SKILL.md").is_file())

    @unittest.skipUnless(os.name == "nt", "PowerShell interactive menu exercised on Windows")
    def test_powershell_interactive_menu_selects_pi(self):
        (self.home / ".pi/agent").mkdir(parents=True)
        command = ["powershell", "-NoProfile", "-File", str(PROJECT / "install.ps1")]
        first = subprocess.run(command, env=self.wrapper_environment(), input="999\n", capture_output=True, text=True, timeout=60)
        choice = re.search(r"(?m)^\s*(\d+)\) Pi\s*$", first.stdout)
        self.assertIsNotNone(choice, first.stdout + first.stderr)
        result = subprocess.run(command, env=self.wrapper_environment(), input=choice[1] + "\n", capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".pi/agent/skills/zentra-dev/SKILL.md").is_file())
        self.assertFalse((self.home / ".codex").exists())

    def test_bash_interactive_menu_selects_pi_without_legacy_install(self):
        bash = self.bash()
        if not bash:
            self.skipTest("Bash unavailable")
        (self.home / ".pi/agent").mkdir(parents=True)
        command = [bash, str(PROJECT / "install.sh")]
        first = subprocess.run(command, env=self.wrapper_environment(), input="999\n", capture_output=True, text=True, timeout=60)
        choice = re.search(r"(?m)^\s*(\d+)\) Pi\s*$", first.stdout)
        self.assertIsNotNone(choice, first.stdout + first.stderr)
        result = subprocess.run(command, env=self.wrapper_environment(), input=choice[1] + "\n", capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".pi/agent/skills/zentra-dev/SKILL.md").is_file())
        self.assertFalse((self.home / ".codex").exists())


if __name__ == "__main__":
    unittest.main()
