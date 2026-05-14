---
doc_id: testing-pytest
title: Pytest
added_date: 2026-05-14
last_updated: "2026-05-14 15:25"
parent_id: testing
sort_order: 20
---
# Pytest

Pytest is a good fit for this repo if the Python test set keeps growing.
It should be added as a thin collection and reporting layer over the existing lightweight checks, not as a replacement for `./scripts/run_checks.py`.

## Current State

The current test framework does not require pytest.
Python checks live under `tests/python/`, use plain `assert`, and many files are directly executable with the configured Python interpreter.
`./scripts/run_checks.py` remains the top-level runner because it also coordinates Ruby/Jekyll builds, browser smoke checks, JSON parsing checks, diff checks, and local run logs under `var/test-runs/`.

That structure should remain the source of truth for Codex close-out unless a future change explicitly replaces it.

## Benefits

Pytest would improve the Python layer in ways that fit the existing test style:

- automatic discovery of `test_*` functions across `tests/python/`
- clearer assertion failure output than direct script execution
- `-k` filtering for one behavior or module name
- reusable fixtures for temporary repos, sample docs trees, generated payloads, and fake services
- parametrized tests for repeated config or route cases
- built-in skip and expected-failure markers for environment-sensitive checks
- easier future plugin support, such as coverage reporting, without changing every test file

The biggest practical benefit is local debugging speed.
Instead of adding one-off direct runners for a file without a `__main__` block, Codex could run a focused command such as:

```bash
python -m pytest tests/python/test_docs_management_server.py -k source_config_settings
```

## Integration Model

Keep `./scripts/run_checks.py` as the user-facing framework.
Add pytest underneath it only for Python test collection.

A conservative integration path:

1. Install pytest in the active local Python environment.
2. Confirm existing tests collect cleanly with `python -m pytest tests/python`.
3. Add a `pytest` check command to `./scripts/run_checks.py` for the Python-heavy profiles.
4. Keep the existing direct-script commands during a transition period.
5. Remove duplicated direct-script commands only after pytest collection is stable.

The first useful profile change would be narrow:

- keep `quick` mostly as-is
- add a focused pytest command to the `docs` profile for `tests/python/test_docs_management_server.py` and nearby Docs Viewer modules
- expand only after collection behavior is predictable

This avoids turning every change into a broad suite run.
Profiles should still stay proportional to risk.

## Test File Compatibility

Most existing Python tests already use pytest-compatible shapes:

- functions named `test_*`
- plain `assert`
- temporary directories from the standard library
- no test class inheritance requirement

Direct `if __name__ == "__main__"` blocks can stay.
Pytest ignores those blocks during collection, while direct script execution remains available.

The main compatibility risks are import-time side effects, assumptions about the current working directory, and tests that rely on process-global module state.
Those should be fixed in the tests rather than papered over in pytest config.

## Install In Current Miniconda Env

Activate or target the current Miniconda environment, then install pytest with pip:

```bash
python -m pip install pytest
```

Verify the installed command is attached to the same interpreter:

```bash
python -m pytest --version
```

Run one focused check:

```bash
python -m pytest tests/python/test_docs_management_server.py
```

Run all Python tests:

```bash
python -m pytest tests/python
```

If the environment should be reproducible for other machines, add pytest to the repo's Python dependency story in the same change that makes `run_checks.py` depend on it.
Until then, treat pytest as a local developer convenience rather than a project requirement.

## Not Yet Needed

Do not add pytest just to run a single script once.
The direct-script pattern is still enough when a focused file can be executed with:

```bash
python tests/python/test_docs_management_server.py
```

Add pytest when collection, focused selection, fixture reuse, or failure readability would reduce repeated work across multiple test files.
