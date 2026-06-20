#!/bin/bash
# xStage USD Viewer Uninstall Script
# Removes the self-contained virtual environment and launchers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.xstage_venv"
DESKTOP_FILE="$HOME/.local/share/applications/usd-viewer.desktop"
LAUNCH_SCRIPT="${SCRIPT_DIR}/launch_usd_viewer.sh"

echo "Removing xStage USD Viewer (self-contained installation)..."
echo "  Removing virtual environment: $VENV_DIR"
rm -rf "$VENV_DIR"
echo "  Removing desktop launcher: $DESKTOP_FILE"
rm -f "$DESKTOP_FILE"
echo "  Removing launch script: $LAUNCH_SCRIPT"
rm -f "$LAUNCH_SCRIPT"
echo "  Removing uninstall script: $UNINSTALL_SCRIPT"
rm -f "$UNINSTALL_SCRIPT"
echo ""
echo "✓ xStage USD Viewer uninstalled"
echo "  Note: No system-wide packages or symlinks were removed (everything was self-contained)"
