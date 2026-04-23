#!/usr/bin/env bash
set -euo pipefail

EDWARD_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALLED=()

echo "Edward Security Framework — Installer"
echo "======================================="
echo ""

# Detect Claude Code
if command -v claude &>/dev/null; then
    echo "[+] Claude Code detected"

    CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins"
    mkdir -p "$CLAUDE_PLUGINS_DIR"

    if [ -L "$CLAUDE_PLUGINS_DIR/edward" ] || [ -d "$CLAUDE_PLUGINS_DIR/edward" ]; then
        rm -rf "$CLAUDE_PLUGINS_DIR/edward"
    fi

    ln -s "$EDWARD_DIR" "$CLAUDE_PLUGINS_DIR/edward"
    echo "    Linked: $CLAUDE_PLUGINS_DIR/edward -> $EDWARD_DIR"
    INSTALLED+=("Claude Code")
else
    echo "[ ] Claude Code not found (skipping)"
fi

echo ""

# Detect OpenCode
if command -v opencode &>/dev/null; then
    echo "[+] OpenCode detected"

    OPENCODE_SKILLS_DIR="$HOME/.config/opencode/skills"
    mkdir -p "$OPENCODE_SKILLS_DIR"

    # Symlink each skill individually
    for skill_dir in "$EDWARD_DIR"/skills/edward-*/; do
        skill_name=$(basename "$skill_dir")
        target="$OPENCODE_SKILLS_DIR/$skill_name"

        if [ -L "$target" ] || [ -d "$target" ]; then
            rm -rf "$target"
        fi

        ln -s "$skill_dir" "$target"
        echo "    Linked: $target"
    done

    # Copy commands if .opencode/commands exists
    OPENCODE_COMMANDS_DIR="$HOME/.config/opencode/commands"
    if [ -d "$EDWARD_DIR/.opencode/commands" ]; then
        mkdir -p "$OPENCODE_COMMANDS_DIR"
        for cmd_file in "$EDWARD_DIR"/.opencode/commands/*.md; do
            cmd_name=$(basename "$cmd_file")
            cp "$cmd_file" "$OPENCODE_COMMANDS_DIR/$cmd_name"
            echo "    Copied: $OPENCODE_COMMANDS_DIR/$cmd_name"
        done
    fi

    # Copy agent definition
    OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"
    if [ -d "$EDWARD_DIR/.opencode/agents" ]; then
        mkdir -p "$OPENCODE_AGENTS_DIR"
        for agent_file in "$EDWARD_DIR"/.opencode/agents/*.md; do
            agent_name=$(basename "$agent_file")
            cp "$agent_file" "$OPENCODE_AGENTS_DIR/$agent_name"
            echo "    Copied: $OPENCODE_AGENTS_DIR/$agent_name"
        done
    fi

    INSTALLED+=("OpenCode")
else
    echo "[ ] OpenCode not found (skipping)"
fi

echo ""

if [ ${#INSTALLED[@]} -eq 0 ]; then
    echo "No supported agents found."
    echo "Install Claude Code (https://claude.ai/code) or OpenCode (https://opencode.ai) first."
    exit 1
fi

echo "Done! Edward installed for: ${INSTALLED[*]}"
echo ""
echo "Quick start:"
echo "  /edward-code-recon    — Run OWASP Top 10 static analysis"
echo "  /edward-dev           — Quick scan of changed files"
echo "  /edward               — Show pipeline status"
