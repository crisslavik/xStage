"""Shared pytest fixtures for the xStage test suite.

Several tests instantiate ``QWidget`` subclasses (e.g. ``ViewportOverlay``).
Qt aborts the whole process if a ``QApplication`` does not exist before the
first widget is constructed, which previously crashed the entire test run.
This autouse, session-scoped fixture guarantees a single ``QApplication`` is
available for every test.
"""

import os

import pytest

# Run Qt without a real display in CI / headless environments.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Provide a singleton QApplication for the whole test session."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        # PySide6 not installed; widget tests will skip/handle this themselves.
        yield None
        return

    app = QApplication.instance() or QApplication([])
    yield app
