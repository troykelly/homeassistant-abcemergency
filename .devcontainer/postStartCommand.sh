#!/usr/bin/env bash
# Post-start command for Home Assistant custom integration development
# This script runs each time the container starts

set -e

# Activate the Home Assistant virtual environment
export PATH="/home/vscode/.local/ha-venv/bin:$PATH"

# ============================================================================
# GitHub Token Configuration (Idempotent)
# ============================================================================
# This ensures the GitHub token is available for CLI tools, MCP servers, etc.
# Works for both new and existing devcontainer environments.

setup_github_token_export() {
    local rc_file="$1"
    local marker="# GitHub Token Export (devcontainer)"
    local export_line='export GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null || echo "")}"'

    # Create the file if it doesn't exist
    touch "$rc_file"

    # Check if our marker already exists (idempotent check)
    if grep -qF "$marker" "$rc_file" 2>/dev/null; then
        # Already configured, update the export line in case it changed
        # Use a temp file for portability
        local tmp_file
        tmp_file=$(mktemp)
        awk -v marker="$marker" -v export_line="$export_line" '
            $0 ~ marker { print; getline; print export_line; next }
            { print }
        ' "$rc_file" > "$tmp_file" && mv "$tmp_file" "$rc_file"
    else
        # Add the configuration block
        {
            echo ""
            echo "$marker"
            echo "$export_line"
        } >> "$rc_file"
    fi
}

# Configure GitHub token export for both shells
echo "Configuring GitHub token availability..."
setup_github_token_export "/home/vscode/.bashrc"
setup_github_token_export "/home/vscode/.zshrc"

# Export for the current session as well
if [ -n "$GITHUB_TOKEN" ]; then
    export GITHUB_TOKEN
elif command -v gh &>/dev/null; then
    GITHUB_TOKEN=$(gh auth token 2>/dev/null || echo "")
    export GITHUB_TOKEN
fi

# Ensure custom_components symlink is up to date
if [ -d "/workspaces/homeassistant-abcemergency/custom_components" ]; then
    mkdir -p /workspaces/homeassistant-abcemergency/config/custom_components
    ln -sf /workspaces/homeassistant-abcemergency/custom_components/* /workspaces/homeassistant-abcemergency/config/custom_components/ 2>/dev/null || true
fi

# Update development dependencies if requirements changed
if [ -f "pyproject.toml" ]; then
    uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e . 2>/dev/null || true
fi

echo "Dev container started. Use 'ha' to start Home Assistant or 'pytest' to run tests."
