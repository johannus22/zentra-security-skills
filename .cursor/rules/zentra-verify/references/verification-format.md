# Verification record v1

Python 3.11+ and Git are required. The authoritative structure is
[verification.schema.json](verification.schema.json). The validator implements the
schema keywords used in this file with the Python standard library; it is not a
general JSON Schema engine. No packages, scanners or target scripts are installed
or executed by the validator.

This protocol adapts the separation of candidate discovery, fresh source review,
runtime receipts and final publication in the adjacent `zentra-cli` repository:
`specs/finding-verification.md`, `specs/dast-verification.md` and
`schemas/verification-record.json`. It is a separate skill-pack format, not CLI
wire compatibility. It does not implement the CLI's host-enforced tool gate,
receipt registry, session isolation, provider runtime or atomic persistence.

## Capture scope

From the assessed repository root, run:

```text
python <skill-dir>/scripts/validate_verification.py --root . --inventory changes
python <skill-dir>/scripts/validate_verification.py --root . --inventory repository --exclude node_modules --exclude dist
```

Capture this output in memory or under `.zentra/`. Git revision and file hashes
are produced, including staged/unstaged/untracked nonignored files and tracked
deletions (`sha256: null`). Repository inventory includes tracked files even if
they match ignore rules. Existing ignored untracked files are outside the Git
inventory: disclose security-relevant ignored/generated/deployed inputs separately
and assess them with evidence. Submodules, symlinks, reparse points and nonregular
entries require a separate explicitly rooted assessment; they cannot be silently
followed or treated as reviewed. The root must be the repository root.

Exclusions are exact relative paths or directory prefixes, not glob patterns.
Each `scope.exclusions` entry has `path` and a nonempty policy `reason`.
`.zentra/` is always excluded from the source snapshot to avoid self-reference;
its evidence files remain hash-checked. Exclusion appropriateness and completeness
of the user's requirements must be reviewed; the validator cannot discover
omitted user requirements or dishonest policy decisions from editable JSON.

`scope` contains `kind`, `revision`, sorted `files`, `exclusions`, `requirements`,
`candidate_ids`, `control_ids`, `author_sessions`, and `coverage_complete`. Keep
the coordinator's full discovered candidate inventory in `candidate_ids`; every
ID needs a disposition record, even when unresolved or rejected. List all known
implementer/author session IDs in `author_sessions` (empty only for assessments
with no agent-authored change). These sessions cannot independently review items
or the overall run. Each requirement has `id`, `description`
and a nonempty list of required `check_ids`. All selected control IDs must have a
control record; use an empty list only when audit controls are outside scope.
Do not remove requirements or controls to make a gate pass.

## Checks and receipts

Each check has `id`, `status`, `required`, `reason`, `command`, `exit_code`,
`receipt`, `expected`, `observed`, and `snapshot_sha256`.

- `passed` and `failed` mean a check was executed or directly inspected, with a
  receipt `{path, sha256}` under `.zentra/evidence/` and an integer exit code.
  For a manual inspection, record `command` as `manual:<procedure>` and capture
  the actual observation and evidence location; exit 0 records procedure
  completion, not proof that the control is effective. Independent reviewers
  must inspect the underlying evidence. A failed semantic assertion may have
  exit 0; a passing check must have exit 0.
- `not_run` and `not_applicable` have `exit_code: null`, an optional receipt or
  `null`, and an explanation. Required checks with either status are incomplete;
  applicability must be settled in the reviewed policy before a requirement is
  made optional. Tool/infrastructure errors are `not_run`, not `failed` security
  assertions and not `passed`.
- Record the redacted output, actual tool/version, time, environment/target,
  expected and observed behavior. For runtime reproduction also include
  principal label, exact request/endpoint/resource and observed protected effect.
  Do not store secrets, auth headers or sensitive customer data. Do not hash a
  raw secret into a public artifact as a substitute for redaction.

The source snapshot must be captured before checks and verified unchanged after
them. `--inventory` recomputes it. Do not overwrite old evidence with unrelated
test output. The validator verifies hashes and references, not that a command
really executed or that the prose correctly interprets the output. Trusted CI
capture and independently reading receipts establish that part of the process.

## Candidate records

Each candidate has `id`, `discovered_by` (actual author session identity),
`disposition`, `record`, `record_sha256` and `reviews`.

`record` fields are `title`, `severity`, `rationale`, `recommendation`, `principal`,
`input`, `boundary`, `resource`, `impact`, `controls_reviewed`, `citations`,
`receipts`, `check_ids`, `blockers`, and `next_step`. Use explicit unknown facts
and named next actions rather than inventing evidence.

Citations are `{path, sha256, line, quote}`. Paths use relative POSIX syntax,
lines are one-based, and quotes match complete consecutive UTF-8 source lines
(line ending differences are tolerated). Hashes cover original file bytes.
Source/runtime-verified records need at least one existing in-scope source
citation, assessed severity and no blockers. Source verification makes no runtime
claim. Runtime verification additionally needs a passed reproduction check whose
receipt is present in the record. Evidence interpretation, endpoint binding,
observed effect and control analysis are reviewer responsibilities.

For secret candidates, never persist a secret-bearing source line as a quote.
Cite exact nonsensitive neighboring context and identify the sensitive location
by path/line in the rationale; the source hash binds the original file. Reviewers
inspect the sensitive line in memory through redaction-safe tooling, without
echoing it into reports or logs. Do not insert a redacted quote that cannot match
the source. If safe evidence inspection is unavailable, keep verification
incomplete rather than exposing a credential to satisfy the schema.

Rejected records need checked counterevidence and both fresh reviews, with
`severity: null`. Needs-validation/incomplete records have `severity: null`,
nonempty `blockers`, and a concrete `next_step`; reviews may be empty. They always
make strict acceptance incomplete. Tool errors cannot be model-authored rejection.

Do not delete fixed candidates to obtain a pass. For remediation, retain the
original finding/history and submit its current-state counterevidence as a freshly
reviewed rejected candidate with explicit fixed-and-retested rationale; the
remediation report links that current record to the original open issue. If
counterevidence is incomplete, keep the current candidate unresolved. The gate
has no field that silently discounts an applied patch.

## Audit controls

Each control has `id`, `assessed_by`, `record`, `record_sha256`, and `reviews`.
Its record contains `framework`, `version`, `reference_url`, `status`, `rationale`,
`period`, `evidence` (hashed artifact references), and `check_ids`.

Use exact control IDs and a verified primary HTTPS requirement URL. The validator
checks URL syntax, not publisher authority or normative text. Capture the
requirement/interpretation and relevant primary source evidence for reviewer
inspection; record licensed/unavailable text as a blocker rather than inventing it.

- `satisfied`: affirmative evidence, passed checks and both fresh reviews.
- `unsatisfied`: affirmative evidence, at least one failed control check and both
  reviews; blocks acceptance regardless of the severity threshold.
- `not_applicable`: affirmative applicability evidence and both reviews.
- `not_assessed`: incomplete assurance; evidence/reviews can be empty.

The period is an explicit date/range or a clearly stated point-in-time design
assessment. Reviewers must reject using a point-in-time source check to claim
period operating effectiveness. A blank report or no findings can never satisfy
a selected control.

## Digests and independent reviews

Use the installed validator module's `digest`, `record_digest`, and `run_digest`
functions to compute hashes in a trusted coordinator. Do not manually approximate
the canonical serialization:

```python
import importlib.util
spec = importlib.util.spec_from_file_location("gate", validator_path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

# source_inventory is the kind/revision/files object returned by --inventory,
# without its snapshot_sha256 field.
snapshot = gate.digest(source_inventory)
candidate["record_sha256"] = gate.record_digest(candidate, snapshot)
control["record_sha256"] = gate.record_digest(control, snapshot)
# After actual candidate/control reviews and final run assembly:
run["run_sha256"] = gate.run_digest(run)
```

Canonical JSON uses sorted keys, UTF-8, no whitespace and no NaN/Infinity. The
snapshot hashes `{kind, revision, files}`. Item digests hash
`{snapshot_sha256, item}` where item contains all candidate/control fields except
`record_sha256` and `reviews`. Thus changing ID, author or disposition invalidates
approval. The run digest hashes every top-level field except `run_sha256` and
`reviews`, binding policy/scope, status, checks, candidate/control decisions and
their reviews. Changing any of those requires fresh overall acceptance.

Each finalized item has exactly two ordered reviews: `adversarial`, then `final`.
A review contains actual `session_id`, `role`, `accepted_sha256` and `read_paths`.
The two sessions must differ from each other and the item's author. Every cited
source, receipt and linked check receipt must appear in each review's independent
reads. Actual read-only investigation must occur; editing `read_paths` or inventing
identities is not verification. Replacements need new approvals of the new digest.

Complete runs, including zero-finding runs, also need two overall reviews by
sessions distinct from `created_by`. They challenge requirement completeness,
exclusions, scope and all evidence; in changes scope they read the changed source
files as well. Reviewers must read all evidence referred to by checks/items;
scope inventory alone does not mean every repository file was analyzed. Record
discovery coverage truthfully. When reviewers are unavailable, keep status
`incomplete`; never synthesize approvals to satisfy the validator.

## Final publication and CI

Required top-level fields: `schema_version: 1`, `run_id`, `created_by`, `status`,
`scope`, `snapshot_sha256`, `checks`, `candidates`, `controls`, `run_sha256`, and
`reviews`. Start with `status: incomplete`, empty reviews and appropriately
computed hashes. On completion obtain actual reviews, write the final JSON, then
run the validator immediately before publishing derived Markdown:

```text
python <skill-dir>/scripts/validate_verification.py .zentra/verification.json --root . --fail-on high
```

Use the process status directly in CI: 0 pass, 1 policy failure, 2 invalid/stale/
unresolved/incomplete. Never use `|| true` or parse report prose as acceptance.
Exit 2 takes precedence when both incompleteness and verified problems exist.
Upload redacted artifacts even on failure with access appropriate to their
contents. A report-only consumer may present results without enforcing a merge
gate, but cannot turn failure into a verified pass.

This helper rejects duplicate JSON keys, unknown fields, invalid types, unsafe
paths, missing files/quotes, stale hashes/revisions/inventories, missing reviewers,
approval digests, unlinked required checks and missing selected control records.
It checks source again before completion. It is not race-proof filesystem isolation
or tamper-resistant attestation: a trusted runner must establish actual execution,
truthful sessions, requirement inventory, receipt interpretation, deployment
binding and policy provenance. Hashes do not authenticate their own author.
