---
doc_id: testing-pytest
title: Pytest
added_date: 2026-05-14
last_updated: "2026-05-14 16:10"
parent_id: testing
sort_order: 20
---
# Pytest

Pytest is the Python test collection layer for this repo.
It sits underneath the existing lightweight check framework rather than replacing `./scripts/run_checks.py`.

## Current State

The current test framework requires pytest for grouped Python profile checks.
Python checks live under `tests/python/`, use plain `assert`, and many files remain directly executable with the configured Python interpreter.
`./scripts/run_checks.py` remains the top-level runner because it also coordinates Ruby/Jekyll builds, browser smoke checks, JSON parsing checks, diff checks, and local run logs under `var/test-runs/`.

That structure should remain the source of truth for Codex close-out unless a future change explicitly replaces it.

## Benefits

Pytest improves the Python layer in ways that fit the existing test style:

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
Use pytest underneath it for Python test collection.

Current integration:

- `quick` runs one grouped `quick-python-pytest` command after Python syntax checks.
- `catalogue` runs one grouped `catalogue-python-pytest` command before the representative build preview.
- `docs` runs one grouped `docs-python-pytest` command before the Studio docs payload/search rebuilds.
- `studio-smoke` remains browser-smoke oriented and does not use pytest directly.

This keeps profile selection proportional to risk without turning every change into a broad suite run.
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

There are two safe ways to use the current Miniconda environment.

Option 1: activate the environment in the shell, then use `python` normally.

```bash
source /path/to/miniconda3/bin/activate
conda activate base
python -m pip install pytest
python -m pytest --version
```

Replace `base` with a named environment if the project is using one.
Confirm which interpreter is active before installing:

```bash
python -c "import sys; print(sys.executable)"
```

Option 2: target the Miniconda interpreter directly without activating the shell.
This is often clearer for Codex checks because the command names the interpreter explicitly:

```bash
/path/to/miniconda3/bin/python -m pip install pytest
/path/to/miniconda3/bin/python -m pytest --version
```

Use the same interpreter for install and test commands.
Do not install with one `python` and test with another.

After install, run one focused check:

```bash
python -m pytest tests/python/test_docs_management_server.py
```

Or, when targeting the interpreter directly:

```bash
/path/to/miniconda3/bin/python -m pytest tests/python/test_docs_management_server.py
```

Run all Python tests:

```bash
python -m pytest tests/python
```

Pytest is listed in `requirements.txt` because `run_checks.py` now depends on it for grouped Python checks.

## Not Yet Needed

Do not add pytest just to run a single script once.
The direct-script pattern is still enough when a focused file can be executed with:

```bash
python tests/python/test_docs_management_server.py
```

Add pytest when collection, focused selection, fixture reuse, or failure readability would reduce repeated work across multiple test files.
