#!/bin/bash
# Install pharma-cli SKILL.md for Claude Code integration

set -e

SKILL_DIR="$HOME/.claude/skills/data-analysis/pharma-cli"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing pharma-cli SKILL.md..."

# Create directory
mkdir -p "$SKILL_DIR"

# Copy SKILL.md
cp "$SCRIPT_DIR/skills/pharma-cli/SKILL.md" "$SKILL_DIR/"

echo "SKILL.md installed to: $SKILL_DIR"
echo ""
echo "To use pharma-cli with Claude Code:"
echo "1. Install pharma-cli: pip install -e ."
echo "2. Open Claude Code in any project"
echo "3. Ask for statistical analysis (e.g., '帮我做统计分析')"
echo ""
echo "Done!"
