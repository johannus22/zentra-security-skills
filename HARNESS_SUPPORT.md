# Harness support

Zentra's canonical `skills/zentra-*/` directories follow the Agent Skills format.
Each bundle includes its `SKILL.md`, scripts, references and optional metadata.
Installation does not configure a provider, copy API credentials or launch an
agent. The same skills work with whichever model the selected harness supports.

## Install from Releases (recommended)

Download [zentra-installer.zip](https://github.com/johannus22/zentra-security-skills/releases/latest/download/zentra-installer.zip)
from the [latest release](https://github.com/johannus22/zentra-security-skills/releases/latest)
and extract it. On Windows, double-click `Install-Zentra.cmd` in its `zentra`
folder. On macOS/Linux, run `bash install.sh` there. Choose one or more harnesses
from the menu using comma-separated numbers or names.

Python 3.11+ is required. Installation is offline and uses no Git, npm, or checkout
to keep around. All skill resources are copied, so you can delete the extracted
installer folder afterward. Git is still needed by the source-verification gate
when it assesses a repository.

The release also provides `zentra-installer.pyz` for direct terminal use:

```text
python zentra-installer.pyz
python zentra-installer.pyz --target claude --target opencode
python zentra-installer.pyz --target pi --target kimi --dry-run
python zentra-installer.pyz --target agents --scope project --project-root /path/to/project
python zentra-installer.pyz --list
```

Use `python3` where appropriate. The release application's additional targets are:

| Target | User root | Project root |
|---|---|---|
| `claude` | `~/.claude/skills/` (honors `CLAUDE_CONFIG_DIR`) | `.claude/skills/` |
| `codex` | `~/.agents/skills/` | `.agents/skills/` |
| `cursor` | `~/.cursor/skills/` | `.cursor/skills/` |
| `opencode` | `~/.config/opencode/skills/` | `.opencode/skills/` |

These roots follow [Claude Code](https://code.claude.com/docs/en/skills),
[Codex](https://learn.chatgpt.com/docs/build-skills),
[Cursor](https://cursor.com/docs/skills) and [OpenCode](https://opencode.ai/docs/skills/)
native discovery. Source-checkout plugin and legacy rule integrations remain
available below. The release application does not register plugins, add legacy
slash wrappers, or rewrite configuration. Ask the host to load a skill by name
or use its native skill catalog. A pre-existing source-linked/unmanaged skill is
preserved; update its checkout or choose another supported root if it conflicts.

To update, download the latest installer and run it again. Checksums for both
downloads are published in `SHA256SUMS`.

## Native skill targets

The following layouts were checked against primary documentation on 2026-11-16.
Select the native target or the shared Agent Skills directory; installing the same
skills in multiple search roots can create name collisions or precedence effects.

| Target | Harness | User skills directory | Project skills directory | Invocation |
|---|---|---|---|---|
| `pi` | Pi | `~/.pi/agent/skills/` | `.pi/skills/` | `/skill:zentra-dev` or ask by name |
| `deepseek` | Official DeepSeek Harness | `~/.dsh/skills/` | `.dsh/skills/` | Ask to load `zentra-dev` using its skill tool |
| `kimi` | Kimi Code | `~/.kimi-code/skills/` | `.kimi-code/skills/` | `/skill:zentra-dev` or ask by name |
| `gemini` | Gemini CLI | `~/.gemini/skills/` | `.gemini/skills/` | Inspect `/skills list`, then ask by name |
| `qwen` | Qwen Code | `~/.qwen/skills/` | `.qwen/skills/` | Inspect `/skills`, then ask by name |
| `agents` | Compatible Agent Skills harnesses | `~/.agents/skills/` | `.agents/skills/` | Use the host's native discovery/invocation |

Pi, DeepSeek Harness, Kimi Code, Gemini CLI and Qwen Code also document shared
`.agents/skills` discovery. Other tools need explicit support for that location
or a configured custom skills root; compatibility is not implied by model name.
Claude Code, OpenCode, Cursor and Codex retain their existing installer routes.

Primary references: [Pi skills](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md),
[Pi packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md),
[DeepSeek filesystem provider](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md),
[Kimi Code skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills),
[Gemini CLI skills](https://geminicli.com/docs/cli/skills/),
[Qwen Code skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/).

## Install from a source checkout (optional)

From the Zentra checkout, with Python 3.11+ available:

```bash
# macOS / Linux: repeat --target to install for several harnesses.
bash install.sh --target pi --target deepseek --target kimi
bash install.sh --target gemini --target qwen

# One shared installation for harnesses that discover ~/.agents/skills.
bash install.sh --target agents
```

```powershell
# Windows / PowerShell
.\install.ps1 -Target pi,deepseek,kimi
.\install.ps1 -Target gemini,qwen
.\install.ps1 -Target agents
```

The Python backend is also directly callable on either platform:

```text
python scripts/install_skills.py --list
python scripts/install_skills.py --target pi --target kimi --dry-run
python scripts/install_skills.py --target all
```

`--target all` selects detected native harnesses, using their command or profile
directory; it excludes the shared target to avoid duplicate installations. The
top-level interactive installers include both existing integrations and detected
new harnesses in their All option. Explicit targets can be installed before the
agent executable is present. No harness is downloaded or installed by Zentra.

## Project-local and custom installations

```bash
bash install.sh --target deepseek --scope project --project-root /path/to/project
bash install.sh --target agents --scope project --project-root /path/to/project
```

```powershell
.\install.ps1 -Target kimi -Scope project -ProjectRoot C:\Projects\my-app
```

When a project root is omitted, the installer uses the nearest ancestor containing
`.git`, or the working directory when outside Git. Harness-specific project trust
and skill activation settings still apply; Zentra does not change them.

The native user targets honor `PI_CODING_AGENT_DIR`, `DSH_HOME` and
`KIMI_CODE_HOME` as configuration roots and append `skills/`. Project targets use
the project path regardless of user configuration roots. Existing older Kimi CLI
versions may use a different directory; use their documented root explicitly:

```text
python scripts/install_skills.py --target kimi --skills-dir /absolute/path/to/legacy-kimi/skills
python scripts/install_skills.py --target agents --skills-dir /absolute/path/to/custom/skills
```

Use `--skills-dir` for one target only. `--home` (PowerShell `-ProfileRoot`) selects
an alternate user profile; explicit harness environment overrides take precedence.
Use `--list` or `-List` to inspect destinations before installation.

## Pi package installation

Zentra's `package.json` declares `pi.skills: ["./skills"]` and the `pi-package`
keyword. Pi can load the checkout as a skill-only package:

```text
pi install .
```

From another directory, provide its absolute checkout path. For published Git
versions, Pi also supports `pi install git:github.com/johannus22/zentra-security-skills@<tag>`;
replace `<tag>` with an existing release tag. This route uses Pi's package manager
and settings; use either it or Zentra's native Pi directory installer to avoid
loading the same skill names twice. The native installer requires no npm package
installation and does not edit Pi settings.

## Updates and local edits

The new native targets copy complete skill bundles and record owned file hashes
in `.zentra-install.json` within each installed skill. Rerun the same command after
updating the checkout. Untouched owned files are updated, missing resources are
repaired, and unchanged obsolete owned files are removed. Unrelated files are
retained. A pre-existing link to this exact canonical skill is retained as a live
link instead of replacing its target.

If a skill is unmanaged, has local edits, or contains an unexpected symlink or
Windows junction, installation stops before applying the planned updates. Review
or relocate that conflicting skill rather than removing the marker to bypass the
check. There is no force-overwrite mode. The installer preflights all selected
destinations; an I/O failure during application can still leave a partial update
and returns failure. Do not run concurrent installers against the same root.

## Verification and support boundaries

Native discovery preserves the original skill safety rules. Pipeline discovery
may run sequentially if delegation is unavailable; strict acceptance still needs
actual fresh reviewer sessions. A host without those sessions leaves verification
incomplete. Installation never grants live-target testing or remediation approval.

Regression tests cover destination resolution, resource preservation, updates,
conflicts, path/link handling and Bash/PowerShell entrypoints using temporary
profiles. These are installation compatibility tests, not live-model accuracy or
end-to-end provider evaluations. After installation, use the host's skill listing
or explicit invocation to confirm discovery in your selected version/configuration.
