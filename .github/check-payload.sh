#!/usr/bin/env bash
# Checks that the DroidVim tree contains the resources and prebuilt files
# that come from upstream's `build` branch and are NOT produced by the
# build-vim-apk workflow. Prints what is missing; exits 1 if anything is.

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
need "term/src/main/jniLibs/ (busybox and helper scripts)" \
  term/src/main/jniLibs -type f -name 'libbusybox.so'
need "term/src/bash/jniLibs/ (bash)" \
  term/src/bash/jniLibs -type f -name 'libbash.tar.so'
need "term/src/cmd-tools/jniLibs/ (grep, diff, ctags)" \
  term/src/cmd-tools/jniLibs -type f -name 'libgrep.so'
need "term/src/vim/res/raw/shell_vim.* (DroidVim shell scripts)" \
  term/src/vim/res/raw -type f -name 'shell_vim*'
need "term/src/vim/jniLibs/<abi>/libvim.app.so (Vim launcher script)" \
  term/src/vim/jniLibs -type f -name 'libvim.app.so'

if [ "$missing" -eq 0 ]; then
  echo "DroidVim tree looks complete."
fi
exit "$missing"
