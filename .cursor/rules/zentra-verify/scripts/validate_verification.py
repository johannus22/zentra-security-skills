"""Validate evidence consistency and acceptance policy; never execute report commands.

This is not execution attestation or a sandbox. See verification-format.md.
Python 3.11+; standard library only. Exit 0 pass, 1 policy failure, 2 incomplete.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from urllib.parse import urlsplit

MAX_BYTES = 16 * 1024 * 1024
SCHEMA = Path(__file__).resolve().parents[1] / "references/verification.schema.json"
SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def digest(value):
    """Canonical JSON: sorted keys, UTF-8, no whitespace, no NaN/Infinity."""
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, "JSON exceeds size bound")
    def reject_constant(value):
        raise Invalid(f"invalid JSON constant: {value}")
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)


def validate_shape(value, rule, schema, location="run"):
    """Implement only the JSON Schema keywords used by the bundled v1 schema."""
    if "$ref" in rule:
        target = schema
        for key in rule["$ref"].removeprefix("#/").split("/"):
            target = target[key]
        validate_shape(value, target, schema, location)
        return
    if "anyOf" in rule:
        for branch in rule["anyOf"]:
            try:
                validate_shape(value, branch, schema, location)
                return
            except Invalid:
                pass
        raise Invalid(f"{location}: does not match an allowed type")
    if "const" in rule:
        require(type(value) is type(rule["const"]) and value == rule["const"], f"{location}: invalid constant")
    if "enum" in rule:
        require(any(type(value) is type(item) and value == item for item in rule["enum"]), f"{location}: invalid enum")
    if "type" in rule:
        types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
        require(type(value) is types[rule["type"]], f"{location}: expected {rule['type']}")
    if isinstance(value, dict):
        require(set(rule.get("required", [])) <= value.keys(), f"{location}: missing required field")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            require(value.keys() <= properties.keys(), f"{location}: unknown field")
        for key, child in value.items():
            if key in properties:
                validate_shape(child, properties[key], schema, f"{location}.{key}")
    elif isinstance(value, list):
        require(rule.get("minItems", 0) <= len(value) <= rule.get("maxItems", 100000), f"{location}: array bound")
        if rule.get("uniqueItems"):
            require(len({digest(item) for item in value}) == len(value), f"{location}: duplicate item")
        for index, child in enumerate(value):
            validate_shape(child, rule.get("items", {}), schema, f"{location}[{index}]")
    elif isinstance(value, str):
        require(rule.get("minLength", 0) <= len(value) <= rule.get("maxLength", MAX_BYTES), f"{location}: text bound")
        if rule.get("minLength", 0):
            require(bool(value.strip()), f"{location}: blank text")
        if "pattern" in rule:
            require(re.fullmatch(rule["pattern"], value) is not None, f"{location}: invalid pattern")
    elif type(value) is int and "minimum" in rule:
        require(value >= rule["minimum"], f"{location}: below minimum")


def relative_path(name):
    require(isinstance(name, str) and bool(name), "empty path")
    require(not any(ord(char) < 32 for char in name), "control character in path")
    require("\\" not in name and ":" not in name, "paths must be relative POSIX paths without streams")
    path = PurePosixPath(name)
    require(not path.is_absolute() and all(part not in ("", ".", "..") for part in name.split("/")), "unsafe relative path")
    require(path.parts[0].casefold() != ".git", "Git metadata cannot be evidence")
    require(all(not part.endswith((" ", ".")) for part in path.parts), "ambiguous Windows path")
    return path


def rooted(root, name):
    relative = relative_path(name)
    current = root
    for part in relative.parts:
        current = current / part
        try:
            mode = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(mode.st_mode), f"symlink forbidden: {name}")
        require(not (getattr(mode, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)), f"reparse point forbidden: {name}")
    require(current.resolve().is_relative_to(root), f"path escapes root: {name}")
    return current


def read_artifact(root, artifact):
    path = rooted(root, artifact["path"])
    require(path.is_file(), f"missing evidence: {artifact['path']}")
    require(path.stat().st_size <= MAX_BYTES, f"oversized evidence: {artifact['path']}")
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, f"oversized evidence: {artifact['path']}")
    require(hashlib.sha256(raw).hexdigest() == artifact["sha256"], f"changed evidence: {artifact['path']}")
    return raw


def git(root, *arguments):
    # Do not invoke repository-configured filesystem monitor commands or allow
    # optional index writes while constructing a supposedly read-only snapshot.
    result = subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                             "-c", "core.untrackedCache=false", "-C", str(root), *arguments],
                            capture_output=True, timeout=30, check=False)
    require(result.returncode == 0, "Git inventory/revision unavailable")
    return result.stdout


def exclusions_list(entries):
    paths = []
    for entry in entries:
        name = entry["path"].removesuffix("/")
        relative_path(name)
        require(bool(entry["reason"].strip()), "exclusion needs a reason")
        paths.append(name)
    require(len(set(paths)) == len(paths), "duplicate exclusions")
    return paths


def inventory(root, kind, exclusions):
    require(git(root, "rev-parse", "--show-prefix").strip() == b"", "root must be the repository root")
    revision = git(root, "rev-parse", "HEAD").decode().strip()
    if kind == "repository":
        raw = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    else:
        raw = b"".join(git(root, *args) for args in (
            ("diff", "--no-ext-diff", "--no-textconv", "--name-only", "--no-renames", "-z"),
            ("diff", "--cached", "--no-ext-diff", "--no-textconv", "--name-only", "--no-renames", "-z"),
            ("ls-files", "--others", "--exclude-standard", "-z")))
    names = sorted(set(name.decode("utf-8") for name in raw.split(b"\0") if name))
    files = []
    for name in names:
        # Assessment evidence cannot change its own source snapshot.
        if name == ".zentra" or name.startswith(".zentra/"):
            continue
        if any(name == item or name.startswith(item + "/") for item in exclusions):
            continue
        path = rooted(root, name)
        require(not path.exists() or path.is_file(), f"unsupported source entry: {name}")
        # Source hashing is streamed: large regular files do not require unbounded RAM.
        if path.exists():
            with path.open("rb") as handle:
                value = hashlib.file_digest(handle, "sha256").hexdigest()
        else:
            value = None  # Tracked deletion remains part of the inventory.
        files.append({"path": name, "sha256": value})
    return {"kind": kind, "revision": revision, "files": files}


def indexed(items, label):
    result = {item["id"]: item for item in items}
    require(len(result) == len(items), f"duplicate {label} ID")
    return result


def record_digest(item, snapshot):
    """Bind identity, disposition/assessment author, record and source snapshot."""
    envelope = {key: value for key, value in item.items() if key not in ("record_sha256", "reviews")}
    return digest({"snapshot_sha256": snapshot, "item": envelope})


def validate_reviews(reviews, accepted, author, read_paths, label, author_sessions=()):
    require(len(reviews) == 2 and [review["role"] for review in reviews] == ["adversarial", "final"], f"two ordered fresh reviews required: {label}")
    sessions = [review["session_id"] for review in reviews]
    require(len(set(sessions + [author])) == 3, f"reviewer/author sessions overlap: {label}")
    require(not set(sessions).intersection(author_sessions), f"reviewer is an implementer: {label}")
    for review in reviews:
        require(review["accepted_sha256"] == accepted, f"review digest mismatch: {label}")
        require(read_paths <= set(review["read_paths"]), f"reviewer missing independent evidence reads: {label}")


def review_record(item, snapshot, author, read_paths, author_sessions=()):
    accepted = record_digest(item, snapshot)
    require(item["record_sha256"] == accepted, f"changed record: {item['id']}")
    validate_reviews(item["reviews"], accepted, author, read_paths, item["id"], author_sessions)


def run_digest(run):
    return digest({key: value for key, value in run.items() if key not in ("run_sha256", "reviews")})


def evaluate(run, root, fail_on="high"):
    schema = read_json(SCHEMA)
    validate_shape(run, schema, schema)
    scope = run["scope"]
    excluded = exclusions_list(scope["exclusions"])
    current = inventory(root, scope["kind"], excluded)
    require(scope["revision"] == current["revision"], "stale revision")
    require(scope["files"] == current["files"], "stale or incomplete source inventory")
    snapshot = digest(current)
    require(run["snapshot_sha256"] == snapshot, "snapshot digest mismatch")
    incomplete = []
    blocked = []
    if run["status"] != "complete" or not scope["coverage_complete"]:
        incomplete.append("run or discovery coverage incomplete")
    checks = indexed(run["checks"], "check")
    run_paths = ({entry["path"] for entry in scope["files"] if entry["sha256"] is not None}
                 if scope["kind"] == "changes" else set())
    evidence_refs = []
    requirements = indexed(scope["requirements"], "requirement")
    require(requirements, "requirements cannot be empty")
    for requirement in requirements.values():
        ids = requirement["check_ids"]
        require(ids and set(ids) <= checks.keys(), "requirement has missing checks")
        require(all(checks[key]["required"] for key in ids), "requirement check was downgraded to optional")
    for check in checks.values():
        require(check["snapshot_sha256"] == snapshot, f"stale check: {check['id']}")
        if check["status"] in ("passed", "failed"):
            require(check["receipt"] is not None and check["exit_code"] is not None, "executed check needs receipt/exit code")
            require(check["receipt"]["path"].startswith(".zentra/evidence/"), "check receipts must be captured under .zentra/evidence/")
            read_artifact(root, check["receipt"])
            if check["status"] == "passed":
                require(check["exit_code"] == 0, "passing check has nonzero exit")
        else:
            require(check["exit_code"] is None, "unexecuted check has exit code")
            if check["receipt"] is not None:
                read_artifact(root, check["receipt"])
        if check["receipt"] is not None:
            run_paths.add(check["receipt"]["path"])
            evidence_refs.append(check["receipt"])
        if check["required"]:
            if check["status"] == "failed":
                blocked.append(f"failed check {check['id']}")
            elif check["status"] != "passed":
                incomplete.append(f"required check not run {check['id']}")
    candidates = indexed(run["candidates"], "candidate")
    require(set(scope["candidate_ids"]) == candidates.keys(), "discovered candidate inventory does not match records")
    source_paths = {entry["path"] for entry in scope["files"] if entry["sha256"] is not None}
    for item in candidates.values():
        record = item["record"]
        verdict = item["disposition"]
        paths = set()
        for citation in record["citations"]:
            evidence_refs.append(citation)
            raw = read_artifact(root, citation)
            text = raw.decode("utf-8-sig")
            lines = text.splitlines()
            quote = citation["quote"].splitlines()
            start = citation["line"] - 1
            require(quote and lines[start:start + len(quote)] == quote, f"citation mismatch: {item['id']}")
            paths.add(citation["path"])
        for receipt in record["receipts"]:
            evidence_refs.append(receipt)
            read_artifact(root, receipt)
            paths.add(receipt["path"])
        require(set(record["check_ids"]) <= checks.keys(), "unknown candidate check")
        paths.update(checks[key]["receipt"]["path"] for key in record["check_ids"] if checks[key]["receipt"] is not None)
        run_paths.update(paths)
        require(item["record_sha256"] == record_digest(item, snapshot), f"changed record: {item['id']}")
        if verdict in ("needs_validation", "incomplete"):
            require(record["severity"] is None and record["blockers"], "unresolved candidate needs blockers and no assessed severity")
            incomplete.append(f"unresolved candidate {item['id']}")
            continue
        require(paths, "final disposition has no evidence")
        review_record(item, snapshot, item["discovered_by"], paths, scope["author_sessions"])
        if verdict == "rejected":
            require(record["severity"] is None, "rejected candidate has assessed severity")
            continue
        require(record["severity"] in SEVERITY, "verified candidate needs severity")
        require(any(citation["path"] in source_paths for citation in record["citations"]), "verified finding needs an in-scope source citation")
        require(not record["blockers"], "verified finding still has blockers")
        if verdict == "runtime_verified":
            require(record["receipts"] and record["check_ids"], "runtime verification needs execution evidence")
            require(all(checks[key]["status"] == "passed" for key in record["check_ids"]), "runtime reproduction check did not pass")
            receipt_paths = {receipt["path"] for receipt in record["receipts"]}
            require(any(checks[key]["receipt"]["path"] in receipt_paths for key in record["check_ids"]), "runtime receipt not bound to reproduction check")
        if SEVERITY[record["severity"]] >= SEVERITY[fail_on]:
            blocked.append(f"{record['severity']} finding {item['id']}")
    controls = indexed(run["controls"], "control")
    require(set(scope["control_ids"]) == controls.keys(), "selected control inventory does not match control records")
    for item in controls.values():
        record = item["record"]
        require(set(record["check_ids"]) <= checks.keys(), "unknown control check")
        url = urlsplit(record["reference_url"])
        require(url.scheme == "https" and url.hostname and not url.username and not url.password, "control needs a primary HTTPS reference")
        paths = set()
        for artifact in record["evidence"]:
            evidence_refs.append(artifact)
            read_artifact(root, artifact)
            paths.add(artifact["path"])
        paths.update(checks[key]["receipt"]["path"] for key in record["check_ids"] if checks[key]["receipt"] is not None)
        run_paths.update(paths)
        require(item["record_sha256"] == record_digest(item, snapshot), f"changed control record: {item['id']}")
        if record["status"] == "not_assessed":
            incomplete.append(f"control not assessed {item['id']}")
            continue
        require(record["evidence"], "assessed control needs affirmative evidence")
        review_record(item, snapshot, item["assessed_by"], paths, scope["author_sessions"])
        if record["status"] == "satisfied":
            require(record["check_ids"] and all(checks[key]["status"] == "passed" for key in record["check_ids"]), "satisfied control needs passed checks")
        elif record["status"] == "unsatisfied":
            require(record["check_ids"] and any(checks[key]["status"] == "failed" for key in record["check_ids"]), "unsatisfied control needs a failed control check")
            blocked.append(f"unsatisfied control {item['id']}")
    require(run["run_sha256"] == run_digest(run), "changed run digest")
    # Complete zero-finding runs still need independent review of requirements,
    # exclusions, test evidence and coverage. Do not let an empty list bypass it.
    if run["status"] == "complete":
        validate_reviews(run["reviews"], run["run_sha256"], run["created_by"], run_paths, run["run_id"], scope["author_sessions"])
    for artifact in evidence_refs:
        read_artifact(root, artifact)
    # Detect ordinary mutation during validation, without claiming race-proof isolation.
    require(inventory(root, scope["kind"], excluded) == current, "source changed during validation")
    return (2, incomplete + blocked) if incomplete else ((1, blocked) if blocked else (0, []))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--fail-on", choices=list(SEVERITY), default="high")
    parser.add_argument("--inventory", choices=("repository", "changes"))
    parser.add_argument("--exclude", action="append", default=[], help="explicit path prefix for --inventory only")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        if args.inventory:
            require(args.record is None, "--inventory does not accept a record")
            excluded = exclusions_list([{"path": path, "reason": "CLI inventory exclusion"} for path in args.exclude])
            value = inventory(root, args.inventory, excluded)
            print(json.dumps({**value, "snapshot_sha256": digest(value)}, indent=2))
            return 0
        require(not args.exclude, "--exclude is only valid with --inventory; record exclusions are authoritative")
        require(args.record is not None, "record path required")
        record_path = Path(os.path.abspath(args.record))
        require(record_path.is_relative_to(root), "record must be inside assessed root")
        rooted(root, record_path.relative_to(root).as_posix())
        code, reasons = evaluate(read_json(record_path), root, args.fail_on)
        print(json.dumps({"gate": {0: "pass", 1: "blocked", 2: "incomplete"}[code], "exit_code": code, "reasons": reasons}))
        return code
    except (Invalid, OSError, UnicodeError, ValueError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as error:
        # Error messages never include source/receipt contents or credentials.
        print(json.dumps({"gate": "incomplete", "exit_code": 2, "reasons": [str(error)]}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
