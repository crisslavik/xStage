#!/bin/bash
# xStage USD Viewer Launch Script
# All dependencies are self-contained in the xStage virtual environment
# Runs directly as a Python application (no package installation needed)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.xstage_venv"
APP_SCRIPT="${SCRIPT_DIR}/src/xstage/core/viewer.py"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: xStage virtual environment not found at $VENV_DIR"
    echo "Please run ./scripts/install.sh first"
    exit 1
fi

# Check if application script exists
if [ ! -f "$APP_SCRIPT" ]; then
    echo "Error: xStage application not found at $APP_SCRIPT"
    exit 1
fi

# Activate virtual environment (self-contained, no system packages)
source "$VENV_DIR/bin/activate"

# Set up USD environment (from built USD with imaging support)
USD_INSTALL_DIR="${SCRIPT_DIR}/.xstage_usd"
if [ -d "$USD_INSTALL_DIR" ]; then
    export PXR_PLUGINPATH_NAME="$USD_INSTALL_DIR/plugin:$PXR_PLUGINPATH_NAME"
    export LD_LIBRARY_PATH="$USD_INSTALL_DIR/lib:$LD_LIBRARY_PATH"
    export PYTHONPATH="$USD_INSTALL_DIR/lib/python:${PYTHONPATH}"
fi

# Set PYTHONPATH to include src directory so imports work
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Change to project root directory
cd "${SCRIPT_DIR}"

# Run application directly (like any other software, no package installation)
python3 "$APP_SCRIPT" "$@"
