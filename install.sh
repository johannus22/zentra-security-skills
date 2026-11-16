#!/usr/bin/env bash
set -euo pipefail

ZENTRA_DIR="$(cd "$(dirname "$0")" && pwd)"

# Explicit native targets also work before a harness is installed. The Python
# helper owns the shared discovery paths and complete bundle update checks.
ZENTRA_PYTHON="${ZENTRA_PYTHON:-}"
if [ -n "$ZENTRA_PYTHON" ]; then
    :
elif command -v python3 >/dev/null 2>&1; then
    ZENTRA_PYTHON="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    ZENTRA_PYTHON="$(command -v python)"
fi
if [ "$#" -gt 0 ]; then
    if [ -z "$ZENTRA_PYTHON" ]; then
        echo "Python 3.11+ is required for native harness installation." >&2
        exit 1
    fi
    exec "$ZENTRA_PYTHON" "$ZENTRA_DIR/scripts/install_skills.py" "$@"
fi

native_label() {
    case "$1" in
        pi) echo "Pi" ;;
        deepseek) echo "DeepSeek Harness" ;;
        kimi) echo "Kimi Code" ;;
        gemini) echo "Gemini CLI" ;;
        qwen) echo "Qwen Code" ;;
    esac
}
NATIVE_TARGETS=()
NATIVE_COUNT=0
if [ -n "$ZENTRA_PYTHON" ]; then
    if native_detected=$("$ZENTRA_PYTHON" "$ZENTRA_DIR/scripts/install_skills.py" --detect); then
        while IFS= read -r native_target; do
            native_target="${native_target%$'\r'}"
            if [ -n "$native_target" ]; then
                NATIVE_TARGETS+=("$native_target")
                NATIVE_COUNT=$((NATIVE_COUNT + 1))
            fi
        done <<< "$native_detected"
    else
        echo "Native harness discovery unavailable; Python 3.11+ is required." >&2
        ZENTRA_PYTHON=""
    fi
fi

cat << "EOF"
 ______  ______   ___   __    _________  ______    ________
/_____/\/_____/\ /__/\ /__/\ /________/\/_____/\  /_______/\
\:::__\/\::::_\/_\::\_\\  \ \\__.::.__\/\:::_ \ \ \::: _  \ \
   /: /  \:\/___/\\:. `-\  \ \  \::\ \   \:(_) ) )_\::(_)  \ \
  /::/___ \::___\/_\:. _    \ \  \::\ \   \: __ `\ \\:: __  \ \
 /_:/____/\\:\____/\\. \`-\  \ \  \::\ \   \ \ `\ \ \\:.\ \  \ \
 \_______\/ \_____\/ \__\/ \__\/   \__\/    \_\/ \_\/ \__\/\__\/

            Zentra Security Skills - Installer
EOF
echo "================================================================"
echo ""

# --- Progress bar ---
show_progress() {
    local current=$1
    local total=$2
    local width=40
    local pct=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))
    printf "\r  [%s%s] %3d%%" "$(printf '#%.0s' $(seq 1 "$filled" 2>/dev/null) )" "$(printf '.%.0s' $(seq 1 "$empty" 2>/dev/null) )" "$pct"
}

# --- Detection phase ---
HAS_CLAUDE=false
HAS_OPENCODE=false
CLAUDE_EXISTS=false
OPENCODE_EXISTS=false

if command -v claude &>/dev/null; then
    HAS_CLAUDE=true
    if [ -L "$HOME/.claude/plugins/zentra" ] || [ -d "$HOME/.claude/plugins/zentra" ]; then
        CLAUDE_EXISTS=true
    fi
fi

if command -v opencode &>/dev/null; then
    HAS_OPENCODE=true
    if [ -d "$HOME/.config/opencode/skills/zentra-code-recon" ] || [ -L "$HOME/.config/opencode/skills/zentra-code-recon" ]; then
        OPENCODE_EXISTS=true
    fi
fi

HAS_CURSOR=false
CURSOR_EXISTS=false

if [ -d "$HOME/.cursor" ]; then
    HAS_CURSOR=true
    if [ -d "$HOME/.cursor/rules" ] && ls "$HOME/.cursor/rules"/zentra-*.mdc &>/dev/null; then
        CURSOR_EXISTS=true
    fi
fi

HAS_CODEX=false
CODEX_EXISTS=false

if command -v codex &>/dev/null || [ -d "$HOME/.codex" ]; then
    HAS_CODEX=true
    if [ -d "$HOME/.codex/skills/zentra-code-recon" ] || [ -d "$HOME/plugins/zentra" ] || { [ -d "$HOME/.codex/zentra" ] && ls "$HOME/.codex/zentra"/zentra-*.md &>/dev/null; }; then
        CODEX_EXISTS=true
    fi
fi

# --- Show detected agents ---
echo "Detected agents:"
echo ""

if $HAS_CLAUDE; then
    if $CLAUDE_EXISTS; then
        echo "  [+] Claude Code  (Zentra already installed — will update)"
    else
        echo "  [+] Claude Code  (fresh install)"
    fi
else
    echo "  [ ] Claude Code  (not found)"
fi

if $HAS_OPENCODE; then
    if $OPENCODE_EXISTS; then
        echo "  [+] OpenCode     (Zentra already installed — will update)"
    else
        echo "  [+] OpenCode     (fresh install)"
    fi
else
    echo "  [ ] OpenCode     (not found)"
fi

if $HAS_CURSOR; then
    if $CURSOR_EXISTS; then
        echo "  [+] Cursor IDE   (Zentra already installed — will update)"
    else
        echo "  [+] Cursor IDE   (fresh install)"
    fi
else
    echo "  [ ] Cursor IDE   (not found)"
fi

if $HAS_CODEX; then
    if $CODEX_EXISTS; then
        echo "  [+] Codex CLI    (Zentra already installed — will update)"
    else
        echo "  [+] Codex CLI    (fresh install)"
    fi
else
    echo "  [ ] Codex CLI    (not found)"
fi

echo ""

# --- No agents found ---
if ! $HAS_CLAUDE && ! $HAS_OPENCODE && ! $HAS_CURSOR && ! $HAS_CODEX && [ -z "$ZENTRA_PYTHON" ]; then
    echo "No supported agents found."
    echo "Install a supported agent, or Python 3.11+ to install portable Agent Skills."
    exit 1
fi

# --- Build menu ---
echo "Where would you like to install Zentra?"
echo ""

OPTIONS=()

# Build options list based on what's detected
if $HAS_CLAUDE;    then OPTIONS+=("Claude Code"); fi
if $HAS_OPENCODE;  then OPTIONS+=("OpenCode"); fi
if $HAS_CURSOR;    then OPTIONS+=("Cursor IDE"); fi
if $HAS_CODEX;    then OPTIONS+=("Codex CLI"); fi
for native_target in ${NATIVE_TARGETS[@]+"${NATIVE_TARGETS[@]}"}; do
    OPTIONS+=("$(native_label "$native_target")")
done
if [ -n "$ZENTRA_PYTHON" ]; then OPTIONS+=("Shared Agent Skills"); fi

# Add "All" if more than one platform detected
PLATFORM_COUNT=0
$HAS_CLAUDE   && PLATFORM_COUNT=$((PLATFORM_COUNT + 1))
$HAS_OPENCODE && PLATFORM_COUNT=$((PLATFORM_COUNT + 1))
$HAS_CURSOR   && PLATFORM_COUNT=$((PLATFORM_COUNT + 1))
$HAS_CODEX    && PLATFORM_COUNT=$((PLATFORM_COUNT + 1))
PLATFORM_COUNT=$((PLATFORM_COUNT + NATIVE_COUNT))
if [ "$PLATFORM_COUNT" -gt 1 ]; then
    OPTIONS+=("All")
fi

OPTIONS+=("Cancel")

for i in "${!OPTIONS[@]}"; do
    echo "  $((i + 1))) ${OPTIONS[$i]}"
done

echo ""
read -rp "Select [1-${#OPTIONS[@]}]: " choice
choice="${choice%$'\r'}"

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#OPTIONS[@]}" ]; then
    echo "Invalid selection. Exiting."
    exit 1
fi

SELECTED="${OPTIONS[$((choice - 1))]}"

if [ "$SELECTED" = "Cancel" ]; then
    echo "Installation cancelled."
    exit 0
fi

for native_target in ${NATIVE_TARGETS[@]+"${NATIVE_TARGETS[@]}"}; do
    if [ "$SELECTED" = "$(native_label "$native_target")" ]; then
        exec "$ZENTRA_PYTHON" "$ZENTRA_DIR/scripts/install_skills.py" --target "$native_target"
    fi
done
if [ "$SELECTED" = "Shared Agent Skills" ]; then
    exec "$ZENTRA_PYTHON" "$ZENTRA_DIR/scripts/install_skills.py" --target agents
fi
if [ "$SELECTED" = "All" ] && [ "$NATIVE_COUNT" -gt 0 ]; then
    "$ZENTRA_PYTHON" "$ZENTRA_DIR/scripts/install_skills.py" --target all
    if ! $HAS_CLAUDE && ! $HAS_OPENCODE && ! $HAS_CURSOR && ! $HAS_CODEX; then exit 0; fi
fi

INSTALL_CLAUDE=false
INSTALL_OPENCODE=false
INSTALL_CURSOR=false
INSTALL_CODEX=false

case "$SELECTED" in
    "Claude Code") INSTALL_CLAUDE=true ;;
    "OpenCode")    INSTALL_OPENCODE=true ;;
    "Cursor IDE")  INSTALL_CURSOR=true ;;
    "Codex CLI")   INSTALL_CODEX=true ;;
    "All")         INSTALL_CLAUDE=$HAS_CLAUDE; INSTALL_OPENCODE=$HAS_OPENCODE; INSTALL_CURSOR=$HAS_CURSOR; INSTALL_CODEX=$HAS_CODEX ;;
esac

echo ""

# --- Count total steps for progress ---
TOTAL_STEPS=0
CURRENT_STEP=0

if $INSTALL_CLAUDE; then
    TOTAL_STEPS=$((TOTAL_STEPS + 1))
fi

if $INSTALL_OPENCODE; then
    # skills + commands + agents
    skill_count=$(find "$ZENTRA_DIR/skills" -maxdepth 1 -type d -name "zentra-*" 2>/dev/null | wc -l)
    cmd_count=0
    agent_count=0
    [ -d "$ZENTRA_DIR/.opencode/commands" ] && cmd_count=$(find "$ZENTRA_DIR/.opencode/commands" -name "*.md" 2>/dev/null | wc -l)
    [ -d "$ZENTRA_DIR/.opencode/agents" ] && agent_count=$(find "$ZENTRA_DIR/.opencode/agents" -name "*.md" 2>/dev/null | wc -l)
    TOTAL_STEPS=$((TOTAL_STEPS + skill_count + cmd_count + agent_count))
fi

if $INSTALL_CURSOR; then
    cursor_mdc_count=$(find "$ZENTRA_DIR/.cursor/rules" -name "zentra-*.mdc" 2>/dev/null | wc -l)
    TOTAL_STEPS=$((TOTAL_STEPS + cursor_mdc_count))
fi

if $INSTALL_CODEX; then
    codex_skill_count=$(find "$ZENTRA_DIR/skills" -maxdepth 1 -type d -name "zentra-*" 2>/dev/null | wc -l)
    codex_legacy_count=$(find "$ZENTRA_DIR/.codex" -name "zentra-*.md" 2>/dev/null | wc -l)
    TOTAL_STEPS=$((TOTAL_STEPS + codex_skill_count + codex_legacy_count + 3))
fi

# --- Silent install functions ---
install_claude() {
    CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins"
    mkdir -p "$CLAUDE_PLUGINS_DIR"

    local target="$CLAUDE_PLUGINS_DIR/zentra"
    if [ -L "$target" ] || [ -d "$target" ]; then
        rm -rf "$target"
    fi

    ln -s "$ZENTRA_DIR" "$target"
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
}

install_opencode() {
    OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skills"
    mkdir -p "$OPENCODE_SKILLS_DIR"

    for skill_dir in "$ZENTRA_DIR"/skills/zentra-*/; do
        skill_name=$(basename "$skill_dir")
        target="$OPENCODE_SKILLS_DIR/$skill_name"
        if [ -L "$target" ] || [ -d "$target" ]; then
            rm -rf "$target"
        fi
        ln -s "$skill_dir" "$target"
        CURRENT_STEP=$((CURRENT_STEP + 1))
        show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
    done

    if [ -d "$ZENTRA_DIR/.opencode/commands" ]; then
        OPENCODE_COMMANDS_DIR="$HOME/.config/opencode/commands"
        mkdir -p "$OPENCODE_COMMANDS_DIR"
        for cmd_file in "$ZENTRA_DIR"/.opencode/commands/*.md; do
            cp "$cmd_file" "$OPENCODE_COMMANDS_DIR/$(basename "$cmd_file")"
            CURRENT_STEP=$((CURRENT_STEP + 1))
            show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
        done
    fi

    if [ -d "$ZENTRA_DIR/.opencode/agents" ]; then
        OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"
        mkdir -p "$OPENCODE_AGENTS_DIR"
        for agent_file in "$ZENTRA_DIR"/.opencode/agents/*.md; do
            cp "$agent_file" "$OPENCODE_AGENTS_DIR/$(basename "$agent_file")"
            CURRENT_STEP=$((CURRENT_STEP + 1))
            show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
        done
    fi
}

install_cursor() {
    CURSOR_RULES_DIR="$HOME/.cursor/rules"
    mkdir -p "$CURSOR_RULES_DIR"

    for mdc_file in "$ZENTRA_DIR"/.cursor/rules/zentra-*.mdc; do
        [ -f "$mdc_file" ] || continue
        cp "$mdc_file" "$CURSOR_RULES_DIR/$(basename "$mdc_file")"
        CURRENT_STEP=$((CURRENT_STEP + 1))
        show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
    done
    for resource_dir in "$ZENTRA_DIR"/.cursor/rules/zentra-*/; do
        [ -d "$resource_dir" ] || continue
        cp -R "${resource_dir%/}" "$CURSOR_RULES_DIR/"
    done
}

install_codex() {
    CODEX_SKILLS_DIR="$HOME/.codex/skills"
    mkdir -p "$CODEX_SKILLS_DIR"

    for skill_dir in "$ZENTRA_DIR"/skills/zentra-*/; do
        [ -d "$skill_dir" ] || continue
        skill_name=$(basename "$skill_dir")
        target="$CODEX_SKILLS_DIR/$skill_name"
        if [ -L "$target" ] || [ -d "$target" ]; then
            rm -rf "$target"
        fi
        ln -s "$skill_dir" "$target"
        CURRENT_STEP=$((CURRENT_STEP + 1))
        show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
    done

    AGENTS_HOME_DIR="$HOME/.agents/plugins"
    PLUGINS_HOME_DIR="$HOME/plugins"
    mkdir -p "$AGENTS_HOME_DIR" "$PLUGINS_HOME_DIR"

    local plugin_target="$PLUGINS_HOME_DIR/zentra"
    if [ -L "$plugin_target" ] || [ -d "$plugin_target" ]; then
        rm -rf "$plugin_target"
    fi
    ln -s "$ZENTRA_DIR" "$plugin_target"
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress "$CURRENT_STEP" "$TOTAL_STEPS"

    MARKETPLACE_PATH="$AGENTS_HOME_DIR/marketplace.json"
    if command -v python3 &>/dev/null; then
        python3 - "$MARKETPLACE_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1]).expanduser()
path.parent.mkdir(parents=True, exist_ok=True)

entry = {
    "name": "zentra",
    "source": {
        "source": "local",
        "path": "./plugins/zentra"
    },
    "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
    },
    "category": "Security"
}

if path.exists():
    data = json.loads(path.read_text(encoding="utf-8"))
else:
    data = {
        "name": "local-marketplace",
        "interface": {
            "displayName": "Local Plugins"
        },
        "plugins": []
    }

plugins = data.setdefault("plugins", [])
plugins = [plugin for plugin in plugins if plugin.get("name") != "zentra"]
plugins.append(entry)
data["plugins"] = plugins

if not isinstance(data.get("interface"), dict):
    data["interface"] = {"displayName": "Local Plugins"}
else:
    data["interface"].setdefault("displayName", "Local Plugins")
data.setdefault("name", "local-marketplace")

path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
PY
    else
        echo ""
        echo "Warning: python3 was not found, so Codex marketplace.json was not updated."
        echo "Add a local plugin entry for ~/plugins/zentra to ~/.agents/plugins/marketplace.json manually."
    fi
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress "$CURRENT_STEP" "$TOTAL_STEPS"

    CODEX_ZENTRA_DIR="$HOME/.codex/zentra"
    mkdir -p "$CODEX_ZENTRA_DIR"

    for skill_file in "$ZENTRA_DIR"/.codex/zentra-*.md; do
        [ -f "$skill_file" ] || continue
        cp "$skill_file" "$CODEX_ZENTRA_DIR/$(basename "$skill_file")"
        CURRENT_STEP=$((CURRENT_STEP + 1))
        show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
    done
    for resource_dir in "$ZENTRA_DIR"/.codex/zentra-*/; do
        [ -d "$resource_dir" ] || continue
        cp -R "${resource_dir%/}" "$CODEX_ZENTRA_DIR/"
    done

    CODEX_AGENTS="$HOME/.codex/AGENTS.md"
    MARKER_START="<!-- zentra:start -->"
    MARKER_END="<!-- zentra:end -->"
    ZENTRA_SECTION=$(cat "$ZENTRA_DIR/.codex/AGENTS.md")

    if [ ! -f "$CODEX_AGENTS" ]; then
        printf '%s\n%s\n%s\n' "$MARKER_START" "$ZENTRA_SECTION" "$MARKER_END" > "$CODEX_AGENTS"
    elif grep -qF "$MARKER_START" "$CODEX_AGENTS"; then
        awk -v start="$MARKER_START" -v end="$MARKER_END" -v content="$ZENTRA_SECTION" '
            $0 == start { skip=1; print start; print content; print end; next }
            $0 == end   { skip=0; next }
            !skip        { print }
        ' "$CODEX_AGENTS" > "$CODEX_AGENTS.tmp" && mv "$CODEX_AGENTS.tmp" "$CODEX_AGENTS"
    else
        printf '\n\n%s\n%s\n%s\n' "$MARKER_START" "$ZENTRA_SECTION" "$MARKER_END" >> "$CODEX_AGENTS"
    fi

    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress "$CURRENT_STEP" "$TOTAL_STEPS"
}

# --- Execute ---
local_action="Installing"
if ($INSTALL_CLAUDE && $CLAUDE_EXISTS) || ($INSTALL_OPENCODE && $OPENCODE_EXISTS) || ($INSTALL_CURSOR && $CURSOR_EXISTS) || ($INSTALL_CODEX && $CODEX_EXISTS); then
    local_action="Updating"
fi
echo "$local_action Zentra..."
echo ""

if $INSTALL_CLAUDE; then
    install_claude
fi

if $INSTALL_OPENCODE; then
    install_opencode
fi

if $INSTALL_CURSOR; then
    install_cursor
fi

if $INSTALL_CODEX; then
    install_codex
fi

echo ""
echo ""

sleep 2

echo "================================================================"
echo ""
echo "  Thank you for installing Zentra! -rafael@kodecraft.dev"
echo ""
echo "================================================================"
echo ""
echo "Quick start:"
echo "  /zentra-code-recon    — Run OWASP Top 10 static analysis"
echo "  /zentra-dev           — Quick scan of changed files"
echo "  /zentra               — Show pipeline status"
echo ""
echo "Cursor IDE: Ask the AI 'run zentra-code-recon' — rules are now in ~/.cursor/rules/"
echo "Codex CLI: Ask the AI 'run zentra-code-recon' - native skills are in ~/.codex/skills/ and the plugin is linked at ~/plugins/zentra"
