#!/usr/bin/env bash
set -euo pipefail

ZENTRA_DIR="$(cd "$(dirname "$0")" && pwd)"

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

echo ""

# --- No agents found ---
if ! $HAS_CLAUDE && ! $HAS_OPENCODE; then
    echo "No supported agents found."
    echo "Install Claude Code (https://claude.ai/code) or OpenCode (https://opencode.ai) first."
    exit 1
fi

# --- Build menu ---
echo "Where would you like to install Zentra?"
echo ""

OPTIONS=()
if $HAS_CLAUDE && $HAS_OPENCODE; then
    OPTIONS+=("Claude Code")
    OPTIONS+=("OpenCode")
    OPTIONS+=("Both")
    OPTIONS+=("Cancel")
    echo "  1) Claude Code"
    echo "  2) OpenCode"
    echo "  3) Both"
    echo "  4) Cancel"
elif $HAS_CLAUDE; then
    OPTIONS+=("Claude Code")
    OPTIONS+=("Cancel")
    echo "  1) Claude Code"
    echo "  2) Cancel"
elif $HAS_OPENCODE; then
    OPTIONS+=("OpenCode")
    OPTIONS+=("Cancel")
    echo "  1) OpenCode"
    echo "  2) Cancel"
fi

echo ""
read -rp "Select [1-${#OPTIONS[@]}]: " choice

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "${#OPTIONS[@]}" ]; then
    echo "Invalid selection. Exiting."
    exit 1
fi

SELECTED="${OPTIONS[$((choice - 1))]}"

if [ "$SELECTED" = "Cancel" ]; then
    echo "Installation cancelled."
    exit 0
fi

INSTALL_CLAUDE=false
INSTALL_OPENCODE=false

case "$SELECTED" in
    "Claude Code") INSTALL_CLAUDE=true ;;
    "OpenCode")    INSTALL_OPENCODE=true ;;
    "Both")        INSTALL_CLAUDE=true; INSTALL_OPENCODE=true ;;
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

# --- Execute ---
local_action="Installing"
if ($INSTALL_CLAUDE && $CLAUDE_EXISTS) || ($INSTALL_OPENCODE && $OPENCODE_EXISTS); then
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
