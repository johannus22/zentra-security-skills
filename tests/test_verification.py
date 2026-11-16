"""Exercise the gate against isolated Git repositories and synthetic reviews.

Fixture reviewer IDs only test consistency rules; they are not real attestations.
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/zentra-verify/scripts/validate_verification.py"
SPEC = importlib.util.spec_from_file_location("gate", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="zentra-gate-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.git("init", "--quiet")
        self.write("policy.py", 'def allowed(user, resource):\n    return user.tenant == resource.tenant\n')
        self.git("add", "policy.py")
        self.git("-c", "user.name=Zentra Test", "-c", "user.email=test@example.invalid",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                 "commit", "--quiet", "-m", "test fixture")
        self.write(".zentra/evidence/check.txt", "tool: fixture\nexpected: denied\nobserved: denied\n")
        self.current = gate.inventory(self.root, "repository", [])
        self.snapshot = gate.digest(self.current)
        self.run = {
            "schema_version": 1, "run_id": "fixture-run", "created_by": "fixture-author",
            "status": "complete", "snapshot_sha256": self.snapshot,
            "scope": {**self.current, "exclusions": [], "coverage_complete": True,
                      "requirements": [{"id": "R1", "description": "Cross-tenant access denied", "check_ids": ["T1"]}],
                      "candidate_ids": [], "control_ids": [], "author_sessions": ["fixture-implementer"]},
            "checks": [{"id": "T1", "status": "passed", "required": True, "reason": "Task security invariant",
                        "command": "fixture-check", "exit_code": 0, "receipt": self.artifact(".zentra/evidence/check.txt"),
                        "expected": "Cross-tenant read denied", "observed": "Cross-tenant read denied",
                        "snapshot_sha256": self.snapshot}],
            "candidates": [], "controls": [], "run_sha256": "", "reviews": []}
        self.seal()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True).stdout

    def artifact(self, name):
        return {"path": name, "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest()}

    def reviews(self, accepted, paths):
        return [{"session_id": "fixture-" + role, "role": role, "accepted_sha256": accepted,
                 "read_paths": sorted(paths)} for role in ("adversarial", "final")]

    def sign_item(self, item):
        item["record_sha256"] = gate.record_digest(item, self.snapshot)
        record = item["record"]
        paths = {entry["path"] for key in ("citations", "receipts", "evidence") for entry in record.get(key, [])}
        paths.update(check["receipt"]["path"] for check in self.run["checks"]
                     if check["id"] in record["check_ids"] and check["receipt"])
        item["reviews"] = self.reviews(item["record_sha256"], paths)

    def seal(self):
        paths = {entry["path"] for entry in self.run["scope"]["files"] if entry["sha256"] is not None}
        paths.update(check["receipt"]["path"] for check in self.run["checks"] if check["receipt"])
        for item in self.run["candidates"] + self.run["controls"]:
            for key in ("citations", "receipts", "evidence"):
                paths.update(entry["path"] for entry in item["record"].get(key, []))
        self.run["run_sha256"] = gate.run_digest(self.run)
        self.run["reviews"] = self.reviews(self.run["run_sha256"], paths)

    def candidate(self, disposition="source_verified", severity="high"):
        item = {"id": "F1", "discovered_by": "fixture-discoverer", "disposition": disposition,
                "record": {"title": "Fixture finding", "severity": severity, "rationale": "Fixture rationale",
                           "recommendation": "Fixture correction", "principal": "Tenant B user", "input": "Tenant A resource ID",
                           "boundary": "Tenant isolation", "resource": "Tenant A record", "impact": "Unauthorized read",
                           "controls_reviewed": "Fixture service policy", "citations": [
                               {**self.artifact("policy.py"), "line": 2, "quote": "    return user.tenant == resource.tenant"}],
                           "receipts": [], "check_ids": [], "blockers": [], "next_step": "Fix and retest"},
                "record_sha256": "", "reviews": []}
        self.run["candidates"].append(item)
        self.run["scope"]["candidate_ids"].append(item["id"])
        self.sign_item(item)
        self.seal()
        return item

    def control(self, status="satisfied"):
        item = {"id": "ASVS-fixture", "assessed_by": "fixture-assessor",
                "record": {"framework": "ASVS fixture", "version": "5.0.0", "reference_url": "https://asvs.owasp.org/",
                           "status": status, "rationale": "Fixture control result", "period": "Point-in-time fixture",
                           "evidence": [self.artifact("policy.py")], "check_ids": ["T1"]},
                "record_sha256": "", "reviews": []}
        self.run["controls"].append(item)
        self.run["scope"]["control_ids"].append(item["id"])
        self.sign_item(item)
        self.seal()
        return item

    def evaluate(self, expected):
        self.assertEqual(gate.evaluate(self.run, self.root)[0], expected)

    def invalid(self, contains=None):
        with self.assertRaises(gate.Invalid) as caught:
            gate.evaluate(self.run, self.root)
        if contains:
            self.assertIn(contains, str(caught.exception))

    def test_complete_zero_finding_run_passes_with_reviewed_checks(self):
        self.evaluate(0)

    def test_zero_findings_cannot_bypass_overall_reviews(self):
        self.run["reviews"] = []
        self.invalid("fresh reviews")

    def test_overall_reviewer_cannot_be_author(self):
        self.run["reviews"][0]["session_id"] = self.run["created_by"]
        self.invalid("overlap")

    def test_missing_overall_receipt_read(self):
        self.run["reviews"][1]["read_paths"] = []
        self.invalid("evidence reads")

    def test_high_source_finding_blocks(self):
        self.candidate()
        self.evaluate(1)

    def test_low_finding_below_policy(self):
        self.candidate(severity="low")
        self.evaluate(0)

    def test_configured_threshold(self):
        self.candidate(severity="medium")
        self.assertEqual(gate.evaluate(self.run, self.root, "medium")[0], 1)

    def test_runtime_requires_receipt_and_check(self):
        self.candidate("runtime_verified")
        self.invalid("execution evidence")

    def test_runtime_reproduction_is_bound_to_check(self):
        item = self.candidate("runtime_verified")
        item["record"]["receipts"] = [self.artifact(".zentra/evidence/check.txt")]
        item["record"]["check_ids"] = ["T1"]
        self.sign_item(item)
        self.seal()
        self.evaluate(1)

    def test_unrelated_runtime_receipt_rejected(self):
        item = self.candidate("runtime_verified")
        self.write(".zentra/evidence/unrelated.txt", "Unrelated tool output")
        item["record"]["receipts"] = [self.artifact(".zentra/evidence/unrelated.txt")]
        item["record"]["check_ids"] = ["T1"]
        self.sign_item(item)
        self.seal()
        self.invalid("not bound")

    def test_source_verification_requires_source_citation(self):
        item = self.candidate()
        item["record"]["citations"] = []
        item["record"]["receipts"] = [self.artifact(".zentra/evidence/check.txt")]
        self.sign_item(item)
        self.seal()
        self.invalid("source citation")

    def test_rejection_requires_counterevidence_and_reviews(self):
        self.candidate("rejected", None)
        self.evaluate(0)
        self.run["candidates"][0]["reviews"] = []
        self.seal()
        self.invalid("fresh reviews")

    def test_needs_validation_is_incomplete_without_assessed_severity(self):
        item = self.candidate("needs_validation", None)
        item["record"]["blockers"] = ["Deployment permission unknown"]
        item["reviews"] = []
        item["record_sha256"] = gate.record_digest(item, self.snapshot)
        self.seal()
        self.evaluate(2)

    def test_unresolved_severity_cannot_be_used_as_verified(self):
        item = self.candidate("needs_validation")
        item["record"]["blockers"] = ["Missing deployment evidence"]
        self.sign_item(item)
        self.seal()
        self.invalid("no assessed severity")

    def test_failure_to_run_check_is_incomplete(self):
        check = self.run["checks"][0]
        check.update(status="not_run", receipt=None, exit_code=None, reason="Tool unavailable")
        self.seal()
        self.evaluate(2)

    def test_required_check_cannot_be_marked_not_applicable(self):
        self.run["checks"][0].update(status="not_applicable", exit_code=None)
        self.seal()
        self.evaluate(2)

    def test_failed_required_assertion_blocks_even_with_exit_zero(self):
        self.run["checks"][0]["status"] = "failed"
        self.seal()
        self.evaluate(1)

    def test_false_passing_exit_code(self):
        self.run["checks"][0]["exit_code"] = 3
        self.seal()
        self.invalid("nonzero exit")

    def test_optional_downgrade_cannot_satisfy_requirement(self):
        self.run["checks"][0]["required"] = False
        self.seal()
        self.invalid("downgraded")

    def test_empty_requirement_checks_rejected(self):
        self.run["scope"]["requirements"][0]["check_ids"] = []
        self.seal()
        self.invalid("missing checks")

    def test_unknown_requirement_check_rejected(self):
        self.run["scope"]["requirements"][0]["check_ids"] = ["missing"]
        self.seal()
        self.invalid("missing checks")

    def test_same_reviewer_session_rejected(self):
        item = self.candidate()
        item["reviews"][1]["session_id"] = item["reviews"][0]["session_id"]
        self.seal()
        self.invalid("overlap")

    def test_discoverer_cannot_review_own_finding(self):
        item = self.candidate()
        item["reviews"][0]["session_id"] = item["discovered_by"]
        self.seal()
        self.invalid("overlap")

    def test_implementer_cannot_independently_review_a_scanners_finding(self):
        item = self.candidate()
        item["reviews"][0]["session_id"] = "fixture-implementer"
        self.seal()
        self.invalid("implementer")

    def test_changed_record_invalidates_approval(self):
        item = self.candidate()
        item["record"]["severity"] = "low"
        self.seal()
        self.invalid("changed record")

    def test_changed_disposition_invalidates_approval(self):
        item = self.candidate()
        item["disposition"] = "rejected"
        self.seal()
        self.invalid("changed record")

    def test_changed_accepted_digest_rejected(self):
        item = self.candidate()
        item["reviews"][1]["accepted_sha256"] = "0" * 64
        self.seal()
        self.invalid("digest mismatch")

    def test_final_reviewer_must_read_source(self):
        item = self.candidate()
        item["reviews"][1]["read_paths"] = []
        self.seal()
        self.invalid("evidence reads")

    def test_wrong_source_quote_rejected(self):
        item = self.candidate()
        item["record"]["citations"][0]["quote"] = "invented statement"
        self.sign_item(item)
        self.seal()
        self.invalid("citation mismatch")

    def test_wrong_source_line_rejected(self):
        item = self.candidate()
        item["record"]["citations"][0]["line"] = 1
        self.sign_item(item)
        self.seal()
        self.invalid("citation mismatch")

    def test_changed_receipt_is_incomplete(self):
        self.write(".zentra/evidence/check.txt", "tampered")
        self.invalid("changed evidence")

    def test_missing_receipt_is_incomplete(self):
        (self.root / ".zentra/evidence/check.txt").unlink()
        self.invalid("missing evidence")

    def test_changed_source_invalidates_snapshot(self):
        self.write("policy.py", "changed\n")
        self.invalid("source inventory")

    def test_new_untracked_file_cannot_be_silently_omitted(self):
        self.write("new-route.py", "route = 'admin'\n")
        self.invalid("source inventory")

    def test_revision_change_invalidates_snapshot(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
                 "-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "--quiet", "-m", "new revision")
        self.invalid("stale revision")

    def test_deleted_source_still_in_inventory(self):
        (self.root / "policy.py").unlink()
        actual = gate.inventory(self.root, "changes", [])
        self.assertEqual(actual["files"], [{"path": "policy.py", "sha256": None}])

    def test_changes_include_staged_unstaged_untracked_and_lockfiles(self):
        self.write("policy.py", "staged\n")
        self.git("add", "policy.py")
        self.write("policy.py", "unstaged\n")
        self.write("package-lock.json", "{}")
        actual = gate.inventory(self.root, "changes", [])
        self.assertEqual([entry["path"] for entry in actual["files"]], ["package-lock.json", "policy.py"])
        self.assertEqual(actual["files"][1], self.artifact("policy.py"))

    def test_new_assessment_artifacts_do_not_invalidate_source(self):
        self.write(".zentra/reports/summary.md", "report")
        self.evaluate(0)

    def test_declared_exclusions_are_prefixes_not_globs(self):
        self.write("dist/generated.js", "generated")
        actual = gate.inventory(self.root, "repository", ["dist"])
        self.assertEqual(actual["files"], self.current["files"])

    def test_traversal_absolute_and_windows_stream_paths_rejected(self):
        for name in ("../secret", "/secret", "C:/secret", "policy.py:stream", "a/../policy.py", "a\\b", "a//b", "policy.py."):
            with self.subTest(name=name), self.assertRaises(gate.Invalid):
                gate.rooted(self.root, name)

    def test_symlink_evidence_rejected_when_supported(self):
        link = self.root / ".zentra/evidence/link.txt"
        try:
            link.symlink_to(self.root / "policy.py")
        except OSError:
            self.skipTest("Host does not permit unprivileged symlink creation")
        with self.assertRaises(gate.Invalid):
            gate.read_artifact(self.root, {"path": ".zentra/evidence/link.txt", "sha256": self.artifact("policy.py")["sha256"]})

    def test_satisfied_control_requires_affirmative_evidence(self):
        item = self.control()
        self.evaluate(0)
        item["record"]["evidence"] = []
        self.sign_item(item)
        self.seal()
        self.invalid("affirmative evidence")

    def test_unassessed_control_is_incomplete(self):
        item = self.control("not_assessed")
        item["reviews"] = []
        self.seal()
        self.evaluate(2)

    def test_not_applicable_control_requires_reviewed_evidence(self):
        item = self.control("not_applicable")
        self.evaluate(0)
        item["reviews"] = []
        self.seal()
        self.invalid("fresh reviews")

    def test_unsatisfied_control_blocks(self):
        self.run["checks"][0]["status"] = "failed"
        self.control("unsatisfied")
        self.evaluate(1)

    def test_unsatisfied_control_needs_failed_check(self):
        self.control("unsatisfied")
        self.invalid("failed control check")

    def test_missing_selected_control_cannot_disappear(self):
        self.run["scope"]["control_ids"] = ["missing"]
        self.seal()
        self.invalid("control inventory")

    def test_discovered_candidate_cannot_silently_disappear(self):
        self.candidate()
        self.run["candidates"] = []
        self.seal()
        self.invalid("candidate inventory")

    def test_git_inventory_does_not_execute_configured_monitor_or_diff(self):
        self.git("config", "core.fsmonitor", "echo unsafe > .zentra/monitor-executed.txt")
        self.git("config", "diff.external", "echo unsafe > .zentra/diff-executed.txt")
        self.write("policy.py", "changed\n")
        gate.inventory(self.root, "changes", [])
        self.assertFalse((self.root / ".zentra/monitor-executed.txt").exists())
        self.assertFalse((self.root / ".zentra/diff-executed.txt").exists())

    def test_unknown_fields_and_boolean_version_rejected(self):
        for change in ({"schema_version": True}, {"schema_version": 2}, {"auto_pass": True}):
            with self.subTest(change=change):
                original = copy.deepcopy(self.run)
                self.run.update(change)
                self.invalid()
                self.run = original

    def test_incomplete_takes_precedence_over_verified_finding(self):
        self.candidate()
        self.run["scope"]["coverage_complete"] = False
        self.seal()
        self.evaluate(2)

    def test_duplicate_ids_rejected(self):
        self.run["checks"].append(copy.deepcopy(self.run["checks"][0]))
        self.seal()
        self.invalid("duplicate check")

    def test_duplicate_json_keys_and_nonstandard_constants_rejected(self):
        for raw in ('{"status": "complete", "status": "incomplete"}', '{"value": NaN}'):
            self.write(".zentra/invalid.json", raw)
            with self.assertRaises(gate.Invalid):
                gate.read_json(self.root / ".zentra/invalid.json")

    def test_changed_run_policy_invalidates_overall_approval(self):
        self.run["checks"][0]["expected"] = "A weaker assertion"
        self.invalid("changed run digest")

    def test_validator_never_executes_recorded_commands(self):
        self.run["checks"][0]["command"] = "create-file .zentra/executed.txt"
        self.seal()
        self.evaluate(0)
        self.assertFalse((self.root / ".zentra/executed.txt").exists())

    def test_cli_exit_codes_and_json_output(self):
        for expected in (0, 1, 2):
            if expected == 1:
                self.candidate()
            elif expected == 2:
                self.run["status"] = "incomplete"
                self.seal()
            record = self.write(".zentra/verification.json", json.dumps(self.run))
            result = subprocess.run([sys.executable, str(SCRIPT), str(record), "--root", str(self.root)], capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["exit_code"], expected)

    def test_cli_malformed_input_fails_closed(self):
        record = self.write(".zentra/broken.json", "{")
        with contextlib.redirect_stdout(io.StringIO()) as captured:
            code = gate.main([str(record), "--root", str(self.root)])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(captured.getvalue())["gate"], "incomplete")

    def test_installed_native_and_flat_adapter_resources_execute(self):
        record = self.write(".zentra/verification.json", json.dumps(self.run))
        project = SCRIPT.parents[3]
        for source in (SCRIPT.parent.parent, project / ".codex/zentra-verify", project / ".cursor/rules/zentra-verify"):
            with self.subTest(source=source):
                destination = self.root / ".zentra/installed" / source.parent.name / "zentra-verify"
                shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
                result = subprocess.run([sys.executable, str(destination / "scripts/validate_verification.py"),
                                         str(record), "--root", str(self.root)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
