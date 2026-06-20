# xStage Engineering Audit

**Author:** Senior Systems Engineer review
**Scope:** Whole repository (~22.3k LOC across 85 Python modules)
**Goal:** Bring xStage to industry-grade quality vs. peers (USDView, Omniverse, Houdini Solaris).

This document is the standing record of the codebase's health, what has been
fixed, and the prioritized roadmap for what remains. It is intended to be kept
up to date as items are closed out.

---

## Executive summary

xStage is a feature-rich USD viewer/editor, but it carried the marks of fast,
under-verified iteration: the test suite was completely unrunnable, there was
**no logging framework at all**, errors were swallowed silently in dozens of
places, and the core lives in a single 4,281-line "god file." None of these are
about features — they are about *diagnosability and trust*, which is exactly
what separates a hobby tool from a production one.

The work so far has restored a green, trustworthy test suite and laid the
foundational infrastructure (logging, a real CLI). The largest structural item
— decomposing `core/viewer.py` — is scoped below but intentionally **not** done
blind in a single pass, because it cannot be safely verified without a running
GUI.

---

## Severity legend

| Level | Meaning |
|-------|---------|
| 🔴 P0 | Blocks build/CI or causes data/visible-behavior failures |
| 🟠 P1 | Systemic quality/maintainability risk; high blast radius |
| 🟡 P2 | Localized quality issues; should be cleaned up |
| 🟢 P3 | Polish / nice-to-have |

---

## Findings & status

### 🔴 P0 — Fixed

1. **Test suite was 100% uncollectable.** `tests/__init__.py` literally
   contained the shell command `touch tests/__init__.py` as Python source — a
   `SyntaxError` that broke collection of every test module.
   *Fixed.*

2. **Hard process abort mid-test-run.** Widget tests constructed a `QWidget`
   with no `QApplication`, triggering Qt's `abort()` and killing pytest. No
   `conftest.py` existed.
   *Fixed:* added a session-scoped, autouse `QApplication` fixture
   (`tests/conftest.py`).

3. **Silent broken import dropped a public class.**
   `converters/adobe_converter.py` used `from converter import …` (missing the
   leading `.`). A `try/except ImportError` in `converters/__init__.py`
   swallowed the failure, silently removing `AdobeUSDConverter` from the API.
   *Fixed:* corrected to a relative import. This is the canonical example of why
   finding #P1-2 (silent excepts) is dangerous.

4. **CI could not import PySide6.** The workflow installed `libgl1-mesa-dev` but
   not `libEGL.so.1`, so `import PySide6` failed on the runner.
   *Fixed:* added `libegl1` + `libxkbcommon0` to the system-deps step.

5. **Stale unit tests** asserted long-removed APIs (`ThemeMode.HIGH_CONTRAST`,
   `CameraManager.get_cameras`, single-arg manager constructors, etc.).
   *Fixed:* aligned 11 tests to the current implementation.

### 🟠 P1 — In progress / foundational

1. **No logging infrastructure (276 `print()` calls, 0 modules using
   `logging`).** A production tool must be able to control verbosity, route to a
   file, and separate info from errors.
   *Done:* added `xstage/logging_config.py` (`get_logger`, idempotent
   `configure_logging`, env-driven level, optional file handler, never touches
   the root logger). The entry point now uses it.
   *Remaining:* mechanically migrate the 276 `print()` sites to
   `get_logger(__name__)` calls, subsystem by subsystem (tracked below).

2. **Silent error swallowing — 34 `except: … pass` and 53 bare `except:`.**
   Bare `except:` also catches `KeyboardInterrupt`/`SystemExit`. This pattern is
   what hid P0-3 for who-knows-how-long.
   *Done:* all 53 bare `except:` converted to `except Exception:`.
   *Remaining:* audit the 34 `except: pass` blocks — each should at minimum
   `log.debug(...)`/`log.warning(...)` so failures are observable.

3. **Brittle, hard-coded Qt platform handling.** `main()` previously *forced*
   `QT_QPA_PLATFORM=xcb` and disabled EGL ("EGL is failing on this system" — a
   workaround for the missing system lib, see P0-4). This broke Wayland and
   headless/offscreen use.
   *Done:* `main()` now respects `$QT_QPA_PLATFORM`, exposes `--platform`, and
   only defaults to `xcb` on X11 when the user expressed no preference.

4. **No real CLI.** No way to open a file from the command line, no `--version`,
   `--help`, or `--log-level` — table stakes for a pro DCC tool.
   *Done:* added `argparse` with a positional `usd_file`, `--version`,
   `--log-level`, `--log-file`, `--platform`. Covered by tests.

5. **`core/viewer.py` is a 4,281-line god file** holding `ViewerSettings`,
   `USDStageManager` (data extraction), `ViewportWidget` (OpenGL), and
   `USDViewerWindow` (137 methods total). This is the single biggest
   maintainability risk.
   *Not started — see roadmap.* Deliberately not split blind: it requires a
   running GUI to verify, and a bad split is worse than the status quo.

### 🟡 P2

1. **188 broad `except Exception`** blocks — many legitimate, but the set should
   be reviewed so genuinely-unexpected errors propagate or are logged with
   context rather than reduced to a fallback.
2. **Duplicate pytest config** (`pytest.ini` + `[tool.pytest.ini_options]` in
   `pyproject.toml`) produced a startup warning and ambiguity.
   *Fixed:* `pytest.ini` is now the single source of truth.
3. **Deprecated USD API:** `utils/validation.py` uses
   `UsdUtils.ComplianceChecker`, deprecated in favor of the USD Validation
   Framework. Will break in a future USD release.
4. **Thin test coverage.** Only construction/smoke tests exist for most
   managers; the rendering and converter logic is largely untested.

### 🟢 P3

1. Packaging/version drift: `setup.py` + `pyproject.toml` both declare
   metadata; `__version__` was missing (now added). Consider a single source
   (e.g. `setuptools_scm`, already in `build-system.requires`).
2. Many docs/markdown status files at the repo root (`UI_IMPROVEMENTS_*`,
   `REFACTORING_PROGRESS.md`, etc.) — consolidate under `docs/`.

---

## Roadmap (recommended order)

1. **Finish observability (P1-1, P1-2).** Migrate `print()` → logging per
   subsystem (`converters/` → `managers/` → `rendering/` → `core/`), adding a
   log line to each silent `except: pass`. Low risk, high diagnostic payoff.
2. **Decompose `core/viewer.py` (P1-5)** into:
   - `core/stage_data.py` — `USDStageManager` + the `_extract_*` data layer.
   - `core/main_window.py` — `USDViewerWindow` (UI orchestration only).
   - keep `ViewportWidget` with the other rendering code under `rendering/`.
   Do it one class at a time, re-exporting from `core/viewer.py` for backward
   compatibility, verifying imports + the GUI after each move.
3. **Modernize USD validation (P2-3)** onto the Validation Framework.
4. **Grow coverage (P2-4)** around converters and the data-extraction layer
   (these are headless-testable without a GPU).
5. **Consolidate packaging/docs (P3).**

## How to verify the current state

```bash
pip install -e .[dev]
QT_QPA_PLATFORM=offscreen pytest -q     # 33 passed, 4 skipped
xstage --version                        # xStage 0.1.0
xstage --help
```
