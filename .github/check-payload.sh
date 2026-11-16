#!/usr/bin/env bash
# Checks that the DroidVim tree contains the resources that come from
# upstream's `build` branch and that build-vim-apk.yml cannot generate
# (app layouts/strings/icons and DroidVim's settings archives).
# Vim, the command-line tools and the helper scripts are produced by the
# workflow. Prints what is missing; exits 1 if anything is.

missing=0

need() {  # need <description> <find arguments...>
  local what=$1; shift
  if [ -z "$(find "$@" -print -quit 2>/dev/null)" ]; then
    echo "missing: $what"
    missing=1
  fi
}

need "term/src/main/res/ (app layouts, strings, icons, preferences)" \
  term/src/main/res -type f -path '*/layout/*'
need "term/src/main/res/raw/terminfo_min.zip (terminal definitions)" \
  term/src/main/res/raw -type f -name 'terminfo_min*'
need "term/src/vim/res/raw/shell_vim.zip (DroidVim shell scripts)" \
  term/src/vim/res/raw -type f -name 'shell_vim*'
need "term/src/vim/res/raw/runtime_extra.zip (DroidVim's Vim settings)" \
  term/src/vim/res/raw -type f -name 'runtime_extra*'

if [ "$missing" -eq 0 ]; then
  echo "DroidVim resources look complete."
fi
exit "$missing"
