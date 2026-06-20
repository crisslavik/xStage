"""Centralized logging configuration for xStage.

xStage historically used ``print()`` for all diagnostics, which made it
impossible to control verbosity, route messages to a file, or distinguish
informational noise from real errors. This module provides a single place to
configure logging for the whole application.

Usage::

    from xstage.logging_config import get_logger, configure_logging

    configure_logging(level="INFO")          # once, at startup
    log = get_logger(__name__)               # in every module
    log.info("stage loaded: %s", path)

Library code should only ever call :func:`get_logger` and log to it. The
application entry point owns :func:`configure_logging`; importing xStage as a
library never reconfigures the root logger or steals the user's handlers.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

__all__ = ["get_logger", "configure_logging", "DEFAULT_FORMAT"]

DEFAULT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
_ROOT_LOGGER_NAME = "xstage"
_configured = False


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger namespaced under ``xstage``.

    Passing ``__name__`` from any submodule yields a hierarchical logger such
    as ``xstage.core.viewer`` so messages can be filtered per-subsystem.
    """
    if not name or name == "__main__":
        return logging.getLogger(_ROOT_LOGGER_NAME)
    if name == _ROOT_LOGGER_NAME or name.startswith(_ROOT_LOGGER_NAME + "."):
        return logging.getLogger(name)
    # Map "xstage.core.viewer" style dotted module paths onto our namespace,
    # and nest anything else underneath it so it is still captured.
    if name.startswith("xstage"):
        return logging.getLogger(name)
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")


def _coerce_level(level: Union[str, int, None]) -> int:
    if level is None:
        env = os.environ.get("XSTAGE_LOG_LEVEL")
        level = env if env else logging.INFO
    if isinstance(level, str):
        return logging.getLevelName(level.upper()) if not level.isdigit() else int(level)
    return int(level)


def configure_logging(
    level: Union[str, int, None] = None,
    *,
    log_file: Optional[Union[str, Path]] = None,
    fmt: str = DEFAULT_FORMAT,
    force: bool = False,
) -> logging.Logger:
    """Configure the ``xstage`` logger hierarchy.

    Idempotent: calling it more than once is a no-op unless ``force`` is set.
    Only the ``xstage`` logger is touched, never the root logger, so xStage
    behaves politely when imported into a host application (Houdini, Maya, a
    pipeline tool, etc.).

    :param level: log level name (e.g. ``"DEBUG"``) or numeric value. Falls
        back to ``$XSTAGE_LOG_LEVEL`` then ``INFO``.
    :param log_file: optional path to also write logs to a file.
    :param force: reconfigure even if already configured.
    """
    global _configured
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    resolved = _coerce_level(level)

    if _configured and not force:
        logger.setLevel(resolved)
        return logger

    # Replace our handlers only; do not disturb anything else in the process.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    formatter = logging.Formatter(fmt)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.setLevel(resolved)
    # Don't double-emit through the root logger's default handler.
    logger.propagate = False
    _configured = True
    return logger
