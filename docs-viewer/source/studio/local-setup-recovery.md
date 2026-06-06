---
doc_id: local-setup-recovery
title: Local Setup Recovery
added_date: 2026-05-19
last_updated: 2026-05-19
parent_id: local-setup
---
# Local Setup Recovery

## Recovery after Xcode / Command Line Tools updates

Major macOS, Xcode, or Command Line Tools updates can disturb local shell startup behavior and tool resolution. The most common symptoms are:

- `brew`, `conda`, `rbenv`, `ruby`, or `python3` suddenly not found
- `bundle` starts using `/usr/bin/ruby` instead of the repo Ruby
- the shell stops loading exports from `.bashrc`, `.bash_profile`, or `.zshrc`
- previously working `ffmpeg` or `heif-convert` commands disappear from `PATH`

Recommended recovery checklist:

1. Confirm the shell you are actually using:

```bash
echo "$SHELL"
ps -p $$ -o command=
```

2. Re-open the terminal, then check whether the expected tools resolve:

```bash
which brew
which python3
which conda
which rbenv
which ruby
which bundle
```

3. If Homebrew is missing from `PATH`, restore the standard shell init line and reload the shell:

```bash
eval "$(/opt/homebrew/bin/brew shellenv)"
```

For persistence, that line should usually live in your shell startup file.

4. If `conda` no longer initializes correctly, re-run:

```bash
conda init zsh
```

Or for `bash`:

```bash
conda init bash
```

Then open a new shell and reactivate the environment:

```bash
conda activate dotlineform
```

5. If `rbenv` no longer initializes correctly, ensure your shell startup file contains:

```bash
eval "$(rbenv init - bash)"
```

For `zsh`, use:

```bash
eval "$(rbenv init - zsh)"
```

Then open a new shell and re-check:

```bash
rbenv version
ruby -v
bundle -v
```

6. If `bundle` is using the wrong Ruby after the update, reset to the repo version:

```bash
rbenv local 3.1.6
hash -r
ruby -v
bundle exec jekyll -v
```

7. If the update affected the Apple developer tools themselves, re-run:

```bash
xcode-select --install
```

If the CLT path looks wrong, check:

```bash
xcode-select -p
```

8. If `ffmpeg` or `heif-convert` disappeared after the update, verify the Homebrew installs:

```bash
brew list --versions ffmpeg libheif
ffmpeg -version | head -n 1
heif-convert --version
```

### Shell startup file note

On macOS, login-shell behavior often causes confusion:

- `zsh` usually reads `~/.zshrc`
- `bash` often reads `~/.bash_profile` for login shells, not `~/.bashrc`

If you keep your exports in `~/.bashrc`, make sure `~/.bash_profile` sources it:

```bash
if [ -f ~/.bashrc ]; then
  . ~/.bashrc
fi
```

That is one of the most likely fixes if a system update makes it look like your env vars or init hooks have vanished.

### Fast post-update validation

After any Xcode/CLT update, this is a good minimal smoke test:

```bash
which python3
python3 -V
python3 -c "import openpyxl; print(openpyxl.__version__)"
which ruby
ruby -v
bundle -v
ffmpeg -version | head -n 1
heif-convert --version
$HOME/miniconda3/bin/python3 admin-app/checks/audit_site_consistency.py --strict
```
