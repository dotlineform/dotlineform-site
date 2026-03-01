## General behaviour

- do not make code changes without first confirming what will be changed.
- instructions like 'check' and 'confirm' DO NOT imply you carry out code changes. always ask for confirmation to proceed.
- consider the prompt requirements and ask for clarification, raise potential issues or unintended side-effects.
- a ? in the prompt always indicates that some analysis is needed on reasons for observed behaviour of code, or clarification of the best course of action.

## Runtime and Paths

- Use `/Users/dlf/miniconda3/bin/python3` for all Python commands.
- Run project commands from `dotlineform-site/` unless explicitly told otherwise.

## Ruby / Jekyll Toolchain

- This repo expects:
  - `.ruby-version` = `3.1.6`
  - Bundler = `2.6.9`
- In Codex/sandbox runs, do not rely on system `ruby`/`bundle` (`/usr/bin/*`), which can cause false failures.
- Use rbenv shims explicitly for verification commands:
  - `/Users/dlf/.rbenv/shims/ruby -v`
  - `/Users/dlf/.rbenv/shims/bundle -v`
  - `/Users/dlf/.rbenv/shims/bundle exec jekyll build --quiet`
- If a build fails with “Could not find bundler 2.6.9” or shows `/usr/bin/ruby`, rerun using the shim commands before reporting an issue.
- Local shell should load rbenv (for interactive use), but Codex checks should still prefer explicit shim paths.

## Safety Defaults

- Prefer dry-run behavior for generators unless explicitly asked to write.
- Do not overwrite prose includes in `_includes/work_prose`, `_includes/series_prose`, or `_includes/moments_prose` unless explicitly requested.
- Do not delete generated or source files unless explicitly requested.

## Pipeline Conventions

- Treat `data/works.xlsx` as canonical source for generated collections.
- Treat worksheets `Works`, `Series`, `WorkDetails`, and `Moments` as canonical.
- Keep generated output deterministic (stable ordering, stable checksums, stable formatting).

## Moments-Specific Rules

- Generate `_moments/*.md` from worksheet `Moments`.
- Moment prose content lives in `_includes/moments_prose/<slug>.md`.
- Moment layout should use srcset variants `800`, `1200`, `1600` only.
- Do not add a `2400` variant for moments unless explicitly requested.

## Validation Checklist

- After changing Python scripts, run a syntax check with the configured interpreter.
- After generator changes, run a dry-run and summarize what would be written.
- After layout/template changes, verify behavior on desktop and mobile.
- Include changed file paths (and line references when useful) in summaries.

## Git and Change Hygiene

- Do not commit unless explicitly requested.
- Do not amend commits unless explicitly requested.
- Never use destructive git commands (`reset --hard`, checkout/revert of unrelated changes) without explicit approval.
- Ignore unrelated dirty files and do not revert user changes.

## Implementation Style

- Preserve existing Jekyll/Liquid conventions in this repo.
- Prefer shared JS/CSS logic over duplicated inline logic.
- Keep comments concise and implementation-focused.
