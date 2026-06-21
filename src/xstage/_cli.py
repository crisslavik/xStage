"""
Lightweight CLI entry point for xstage.

Must NOT import pxr at module level.

Handles two environment problems automatically via os.execve() — both before
any heavy imports so the fixes compose cleanly:

1. Wrong Python interpreter (e.g., system Python 3.12 from a stale
   ~/.local/bin/xstage install):  re-execs with the project's .venv Python.
2. Missing imaging shared libraries (.xstage_usd not in LD_LIBRARY_PATH):
   re-execs with the correct LD_LIBRARY_PATH and PYTHONPATH.

The sentinel XSTAGE_ENV_READY prevents infinite re-exec loops.
"""

import os
import sys
from pathlib import Path


def _repo_root() -> Path:
    # src/xstage/_cli.py → src/xstage → src → repo-root
    return Path(__file__).resolve().parent.parent.parent


def _find_custom_usd():
    """Return (usd_lib, usd_python, python_lib_or_None) if .xstage_usd exists."""
    usd_dir = _repo_root() / ".xstage_usd"
    if not (usd_dir / "lib" / "python" / "pxr").exists():
        return None
    python_dir = _repo_root() / ".xstage_python"
    python_lib = str(python_dir / "lib") if (python_dir / "lib").exists() else None
    return str(usd_dir / "lib"), str(usd_dir / "lib" / "python"), python_lib


def _find_venv_python():
    """Return venv Python path if it exists AND differs from the current interpreter."""
    venv_python = _repo_root() / ".venv" / "bin" / "python3"
    if not venv_python.exists():
        return None
    if os.path.realpath(str(venv_python)) == os.path.realpath(sys.executable):
        return None  # already on the right Python
    return str(venv_python)


def _imaging_env(custom):
    """Return an env dict with imaging USD paths prepended."""
    usd_lib, usd_python, python_lib = custom
    root = _repo_root()
    usd_dir = root / ".xstage_usd"
    env = os.environ.copy()
    env["XSTAGE_ENV_READY"] = "1"

    ld_parts = [p for p in [usd_lib, python_lib] if p]
    existing_ld = env.get("LD_LIBRARY_PATH", "")
    if existing_ld:
        ld_parts.append(existing_ld)
    env["LD_LIBRARY_PATH"] = ":".join(ld_parts)

    existing_py = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = ":".join([usd_python, existing_py] if existing_py else [usd_python])

    # Override plugin search path so our USD 25.11 runtime never loads plugins
    # from a system OpenUSD install (e.g. v0_26_2 at /home/.../OpenUSD/Install/).
    # Mixing plugin .so files across USD versions causes ABI symbol errors.
    env["PXR_PLUGINPATH_NAME"] = ":".join([
        str(usd_dir / "plugin" / "usd"),
        str(usd_dir / "lib" / "usd"),
    ])
    return env


def main(argv=None):
    if "XSTAGE_ENV_READY" not in os.environ:
        custom = _find_custom_usd()

        # Step 1 — wrong Python?  Re-exec with .venv/bin/python3.
        # This makes a stale ~/.local/bin/xstage (Python 3.12) transparently
        # redirect to the project venv (Python 3.11) that has all imaging deps.
        venv_python = _find_venv_python()
        if venv_python:
            env = _imaging_env(custom) if custom else os.environ.copy()
            env["XSTAGE_ENV_READY"] = "1"
            os.execve(venv_python, [venv_python] + sys.argv, env)
            # execve replaces the process; never reached.

        # Step 2 — right Python but imaging libs not yet in env?  Re-exec with paths.
        if custom:
            os.execve(sys.executable, [sys.executable] + sys.argv, _imaging_env(custom))
            # execve replaces the process; never reached.

    # Environment is ready (or no custom USD found) — safe to import pxr.
    from xstage.core.viewer import main as viewer_main

    viewer_main(argv)
