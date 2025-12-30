#!/usr/bin/env bash
# Post-create command for Home Assistant custom integration development
# This script runs once when the container is first created

set -e

echo "=== Home Assistant ABC Emergency Integration - Dev Container Setup ==="

# Activate the Home Assistant virtual environment
export PATH="/home/vscode/.local/ha-venv/bin:$PATH"

# ============================================================================
# GitHub Token Configuration (Idempotent)
# ============================================================================
# This ensures the GitHub token is available for CLI tools, MCP servers, etc.
# The same setup runs in postStartCommand.sh for existing environments.

setup_github_token_export() {
    local rc_file="$1"
    local marker="# GitHub Token Export (devcontainer)"
    local export_line='export GITHUB_TOKEN="${GITHUB_TOKEN:-$(gh auth token 2>/dev/null || echo "")}"'

    # Create the file if it doesn't exist
    touch "$rc_file"

    # Check if our marker already exists (idempotent check)
    if grep -qF "$marker" "$rc_file" 2>/dev/null; then
        return 0  # Already configured
    fi

    # Add the configuration block
    {
        echo ""
        echo "$marker"
        echo "$export_line"
    } >> "$rc_file"
}

# Configure GitHub token export for both shells
echo "Configuring GitHub token for shell sessions..."
setup_github_token_export "/home/vscode/.bashrc"
setup_github_token_export "/home/vscode/.zshrc"

# Export for the current session
if [ -n "$GITHUB_TOKEN" ]; then
    export GITHUB_TOKEN
elif command -v gh &>/dev/null; then
    GITHUB_TOKEN=$(gh auth token 2>/dev/null || echo "")
    export GITHUB_TOKEN
fi

# Create config directory if it doesn't exist
mkdir -p /workspaces/homeassistant-abcemergency/config/custom_components

# Link the custom component for development
if [ -d "/workspaces/homeassistant-abcemergency/custom_components" ]; then
    echo "Linking custom_components to Home Assistant config..."
    ln -sf /workspaces/homeassistant-abcemergency/custom_components/* /workspaces/homeassistant-abcemergency/config/custom_components/ 2>/dev/null || true
fi

# Install project dependencies if pyproject.toml or requirements exist
if [ -f "pyproject.toml" ]; then
    echo "Installing project dependencies with uv..."
    uv pip install -e ".[dev]" 2>/dev/null || uv pip install -e . 2>/dev/null || true
elif [ -f "requirements.txt" ]; then
    echo "Installing requirements.txt..."
    pip install -r requirements.txt 2>/dev/null || true
fi

# Install dev requirements if present
if [ -f "requirements_dev.txt" ]; then
    echo "Installing dev requirements..."
    pip install -r requirements_dev.txt 2>/dev/null || true
fi

# Install Home Assistant component dependencies needed by default_config
echo "Installing Home Assistant component dependencies..."
pip install ha-ffmpeg 2>/dev/null || true

if [ -f "requirements_test.txt" ]; then
    echo "Installing test requirements..."
    pip install -r requirements_test.txt 2>/dev/null || true
fi

# Setup pre-commit hooks if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    pre-commit install 2>/dev/null || true
fi

# Create basic Home Assistant configuration if it doesn't exist
if [ ! -f "/workspaces/homeassistant-abcemergency/config/configuration.yaml" ]; then
    echo "Creating default Home Assistant configuration..."
    cat > /workspaces/homeassistant-abcemergency/config/configuration.yaml << 'EOF'
# Home Assistant Development Configuration
# This configuration is for testing custom integrations

homeassistant:
  name: Dev Instance
  unit_system: metric
  time_zone: UTC

# Enable default config components
default_config:

# Enable debug logging for development
logger:
  default: info
  logs:
    custom_components.abcemergencymedia: debug
    homeassistant.components.media_player: debug

# Debugger configuration for VS Code
debugpy:
  start: true
  wait: false
EOF
fi

# Verify tools are available
echo ""
echo "=== Verifying installed tools ==="
echo "Python: $(python --version 2>&1 || echo 'not found')"
echo "Home Assistant: $(python -c 'import homeassistant; print(homeassistant.__version__)' 2>&1 || echo 'not found')"
echo "uv: $(uv --version 2>&1 || echo 'not found')"
echo "pnpm: $(pnpm --version 2>&1 || echo 'not found')"
echo "claude: $(claude --version 2>&1 || echo 'not found')"
echo "ruff: $(ruff --version 2>&1 || echo 'not found')"
echo "pytest: $(pytest --version 2>&1 || echo 'not found')"

echo ""
echo "=== Setup Complete ==="
echo "To start Home Assistant: ha"
echo "To run tests: pytest"
echo "To check code: ruff check ."
