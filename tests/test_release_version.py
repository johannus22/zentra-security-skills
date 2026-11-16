"""Release metadata tests run only against isolated copies, never the working tree."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_version", PROJECT / "scripts/version.py")
version = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(version)


class ReleaseVersionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="zentra-release-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name in version.RELEASE_FILES:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((PROJECT / name).read_bytes())

    def test_current_metadata_and_matching_tag(self):
        current = version.current_version(self.root)
        self.assertEqual(version.check(self.root, "v" + current), current)

    def test_wrong_or_unprefixed_tag_rejected(self):
        for tag in ("v99.0.0", version.current_version(self.root), "v3.0.0;echo injected"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                version.check(self.root, tag)

    def test_manifest_drift_blocks_release(self):
        target = self.root / ".codex-plugin/plugin.json"
        data = json.loads(target.read_text(encoding="utf-8"))
        data["version"] = "0.0.1"
        target.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "expected version"):
            version.check(self.root)

    def test_readme_version_drift_blocks_release(self):
        target = self.root / "README.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(version.README_VERSION.sub(lambda match: match[1] + "0.0.1" + match[3], text), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "README.md: expected version"):
            version.check(self.root)

    def test_explicit_prerelease_synchronizes_all_manifests(self):
        version.set_version("4.0.0-rc.1", self.root)
        self.assertEqual(version.current_version(self.root), "4.0.0-rc.1")
        for _, (_, data) in version.manifests(self.root).items():
            self.assertEqual(data["version"], "4.0.0-rc.1")
        heading = version.README_VERSION.search((self.root / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(heading[2], "4.0.0-rc.1")
        with self.assertRaisesRegex(ValueError, "Add release notes"):
            version.check(self.root)

    def test_unreleased_notes_are_promoted_and_can_be_released(self):
        changelog = self.root / "CHANGELOG.md"
        text = changelog.read_text(encoding="utf-8")
        text = text.replace("# Changelog\n", "# Changelog\n\n## [Unreleased]\n\n### Fixed\n- Corrected a release defect.\n", 1)
        changelog.write_text(text, encoding="utf-8")
        version.set_version("4.1.0", self.root)
        self.assertEqual(version.check(self.root, "v4.1.0"), "4.1.0")
        notes = version.release_notes("4.1.0", self.root)
        self.assertIn("Corrected a release defect.", notes)
        self.assertNotIn("## [3.0.0]", notes)

    def test_empty_notes_block_release(self):
        version.set_version("99.0.0", self.root)
        with self.assertRaisesRegex(ValueError, "Add release notes"):
            version.check(self.root)

    def test_duplicate_release_entries_block_release(self):
        changelog = self.root / "CHANGELOG.md"
        current = version.current_version(self.root)
        text = changelog.read_text(encoding="utf-8")
        changelog.write_text(text + f"\n## [{current}]\n\n- Duplicate.\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            version.check(self.root)

    def test_bump_resets_lower_components(self):
        expected = {"patch": "3.2.6", "minor": "3.3.0", "major": "4.0.0"}
        for part, target in expected.items():
            with self.subTest(part=part):
                version.set_version("3.2.5", self.root)
                self.assertEqual(version.bump_version(part, self.root), target)
                self.assertEqual(version.current_version(self.root), target)

    def test_bump_prerelease_requires_an_explicit_version(self):
        version.set_version("4.0.0-rc.1", self.root)
        with self.assertRaisesRegex(ValueError, "Use 'set'"):
            version.bump_version("patch", self.root)

    def test_invalid_versions_do_not_modify_files(self):
        before = {name: (self.root / name).read_bytes() for name in version.RELEASE_FILES}
        for candidate in ("v4.0.0", "04.0.0", "4.0", "4.0.0-01", "4.0.0;rm", "../4.0.0", "4.0.0\n"):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                version.set_version(candidate, self.root)
        after = {name: (self.root / name).read_bytes() for name in before}
        self.assertEqual(before, after)

    def test_malformed_manifest_does_not_partially_write_versions(self):
        (self.root / version.MANIFESTS[-1]).write_text("{", encoding="utf-8")
        before = {name: (self.root / name).read_bytes() for name in version.RELEASE_FILES}
        with self.assertRaises(ValueError):
            version.set_version("99.0.0", self.root)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in before})

    def test_ambiguous_readme_does_not_partially_write_versions(self):
        target = self.root / "README.md"
        text = target.read_text(encoding="utf-8")
        target.write_text(text + "\n**Version 99.0.0 - Duplicate heading**\n", encoding="utf-8")
        before = {name: (self.root / name).read_bytes() for name in version.RELEASE_FILES}
        with self.assertRaisesRegex(ValueError, "exactly one"):
            version.set_version("99.0.0", self.root)
        self.assertEqual(before, {name: (self.root / name).read_bytes() for name in before})

    def test_setting_current_version_preserves_other_metadata(self):
        target = self.root / "package.json"
        before = json.loads(target.read_text(encoding="utf-8"))
        version.set_version(version.current_version(self.root), self.root)
        self.assertEqual(before, json.loads(target.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
