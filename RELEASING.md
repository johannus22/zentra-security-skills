# Releasing Zentra Security Skills

`VERSION` is the source of truth. Use [semantic versions](https://semver.org/spec/v2.0.0.html): breaking changes increment
the major version, compatible features the minor version, and fixes the patch.
The pending version is recorded in [VERSION](VERSION). Evidence format `schema_version: 1` has its own
compatibility contract and does not change automatically with a package release.

## Prepare a version

```text
python scripts/version.py show
python scripts/version.py check --tag v3.0.0
```

For later releases, use `python scripts/version.py bump patch` (or `minor`/`major`),
or set a specific version with `python scripts/version.py set 3.1.0-rc.1`.
This updates VERSION, npm/plugin manifests, the Claude marketplace and the README
version heading together. Validation rejects drift between these versions.
An `[Unreleased]` changelog entry is promoted when present; otherwise an empty
version entry is created. Add meaningful release notes before validation can pass.
The tool never commits, creates tags, pushes or publishes.

## Validate and publish the tag

After reviewing and committing the intended release changes on `main`, run:

```text
python scripts/version.py check
python scripts/check_framework.py
python -m unittest discover -s tests -v
git diff --check
git status --short
```

The working tree should be clean and the intended release commit should include
the version, changelog, workflows, skills and generated adapters. Push the commit,
then create and push its matching annotated tag:

```text
git push origin main
git tag -a v3.0.0 -m "Zentra Security Skills v3.0.0"
git push origin v3.0.0
```

Use the actual version from VERSION for subsequent tags. Do not move a published
tag; prepare a new version for corrections. Prerelease versions use tags such as
`v3.1.0-rc.1`.

## Review the draft release

The tag workflow validates the framework on Windows/Linux and Python 3.11/3.13,
checks that the tag matches all manifests and the changelog, and builds a `.tgz`
package, a self-contained `zentra-installer.pyz`, a friendly `zentra-installer.zip`
with Windows/macOS/Linux launchers, and SHA-256 checksums for all assets. It then creates a **draft GitHub release** with
changelog notes and assets. Open the draft in the repository's Releases page,
review it, and publish it when ready. Prerelease tags are marked as prereleases.
There is no automatic npm publication.

Build the standalone installers locally with
`python scripts/build_release.py --output-dir release-artifacts`. The builder uses
the checked version, canonical skills and standard Python library. Test generated
applications and extracted launchers in disposable profiles before publishing.
Installation must work from an empty workspace with no Git or npm on PATH. No
provider credentials or user configuration belong in the release bundle.

Workflow actions are pinned to commit hashes. Validation and packaging use read
permissions; only the final draft job has `contents: write`, and that job does
not check out or run repository code. Repository/organization Actions settings
must allow that workflow permission. Existing releases are not overwritten.

The distribution includes the remote's Apache-2.0 LICENSE plus NOTICE and the
retained original MIT notice in LICENSES/zentra-upstream-MIT.txt. Keep all license
notices in release packages.
