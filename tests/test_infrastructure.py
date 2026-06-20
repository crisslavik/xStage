"""Tests for cross-cutting infrastructure: logging config and the CLI entry point."""

import logging

import pytest


def test_get_logger_namespaced():
    from xstage.logging_config import get_logger

    assert get_logger("xstage.core.viewer").name == "xstage.core.viewer"
    # __main__ and empty names collapse to the root xstage logger.
    assert get_logger("__main__").name == "xstage"
    assert get_logger(None).name == "xstage"
    # Arbitrary names are nested under the xstage namespace.
    assert get_logger("converter").name == "xstage.converter"


def test_configure_logging_is_idempotent():
    from xstage.logging_config import configure_logging

    logger = configure_logging(level="WARNING", force=True)
    assert logger.level == logging.WARNING
    handler_count = len(logger.handlers)

    # Second call without force must not stack new handlers.
    configure_logging(level="DEBUG")
    assert len(logger.handlers) == handler_count
    # ...but it should still update the level.
    assert logger.level == logging.DEBUG

    # It must never touch the root logger (good library citizenship).
    assert logger is not logging.getLogger()
    assert logger.propagate is False


def test_configure_logging_level_from_string():
    from xstage.logging_config import configure_logging

    assert configure_logging(level="ERROR", force=True).level == logging.ERROR


def test_cli_version(capsys):
    from xstage.core.viewer import main

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    out = capsys.readouterr()
    assert "xStage" in (out.out + out.err)


def test_cli_help(capsys):
    from xstage.core.viewer import main

    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "usd_file" in capsys.readouterr().out


def test_cli_parser_accepts_file_and_loglevel():
    from xstage.core.viewer import _parse_args

    args = _parse_args(["scene.usd", "--log-level", "DEBUG"])
    assert args.usd_file == "scene.usd"
    assert args.log_level == "DEBUG"
