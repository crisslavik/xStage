#!/bin/bash
# xStage USD Viewer Launch Script
# All dependencies are self-contained in the xStage virtual environment
# Runs as a Python module to support relative imports

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.xstage_venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: xStage virtual environment not found at $VENV_DIR"
    echo "Please run ./FIX_VENV.sh or ./scripts/install.sh first"
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

# Run application as a module (required for relative imports)
python3 -m xstage.core.viewer "$@"
