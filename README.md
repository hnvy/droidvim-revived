# DroidVim

DroidVim is a Vim clone for Android.  
[Download the DroidVim from Google Play](https://play.google.com/store/apps/details?id=com.droidvim)

To build the "DroidVim" application, choose the `droidvim` flavor and build.  
To avoid repository bloat, the latest Vim binaries are included in the `build` branch. If you need the latest Vim binaries, please checkout to the `build` branch before building.  
The `build` branch will be rebased to the latest `master` branch.  

This code is based on the "[Terminal Emulator for Android](https://github.com/jackpal/Android-Terminal-Emulator)".  
By choosing the `terminal` flavor, you can build the "Terminal Emulator for Android" compatible application with various functions of the DroidVim.  

# Licensing

- DroidVim is licensed under the Apache License, Version 2.0. See [LICENSE](https://github.com/shiftrot/droidvim/blob/master/LICENSE) for the full license text.  
- [Terminal Emulator for Android](https://github.com/jackpal/Android-Terminal-Emulator) code is used which is released under Apache 2.0 license.  


# Building DroidVim with GitHub Actions

`.github/workflows/build-vim-apk.yml` builds what DroidVim runs on the device,
for arm64-v8a, armeabi-v7a, x86_64 and x86, and packages the APK:

| What | How | Optional |
| --- | --- | --- |
| Vim (default `v9.2.0501`), xxd, Vim runtime | Vim source + `patches/`, Android NDK | always built |
| grep, diff, ctags | latest GNU grep, GNU diffutils, Universal Ctags, Android NDK | `BUILD_CMD_TOOLS` |
| bash, ncurses tools, zip, unzip, busybox, proot, am | [termux-packages](https://github.com/termux/termux-packages) built for `com.droidvim`, repackaged by `.github/droidvim-pack.py` | `BUILD_TERMUX_TOOLS` |
| git | termux-packages, as above | `WITH_GIT` |
| Python 3 + pip | termux-packages, as above (without Tkinter and the test suite) | `WITH_PYTHON` |
| Helper scripts (`vim.app`, `sh.app`, `busybox-setup`, ...) | `payload/scripts/` | always |

## Choosing what to build

- **Run workflow** (Actions → Build Vim for Android + DroidVim APK) has a
  checkbox for each optional part and a choice for the extra tools (git,
  Python, both or none).
- **Push builds** build everything by default. To change that, add repository
  variables (Settings → Secrets and variables → Actions → Variables) set to
  `false`: `BUILD_CMD_TOOLS`, `BUILD_TERMUX_TOOLS`, `WITH_GIT`, `WITH_PYTHON`.
- When a part isn't built, the prebuilt copies already in the repository are
  used, and the run warns about any that are missing. git and Python are only
  available when the Termux tools are built.

## Notes

- Results are under **Artifacts** on the run page: `DroidVim-vim<version>-<debug|release>`
  (the APK), plus `vim-android-<abi>`, `vim-runtime` and `termux-payload-<abi>`.
- The Termux-built tools need Android 7.0 (API 24) or newer. Vim, grep, diff
  and ctags are built for API 21.
- The first Termux build is slow (1–2 hours per ABI with git and Python);
  later runs reuse cached builds until termux-packages or the options change.
- git and Python add roughly 30–50 MB to the APK.
- git, Python and the other Termux tools are unpacked into the app's `usr`
  folder: `git`, `python3`, `pip` work from the DroidVim shell. git uses
  `less` as its pager and DroidVim's `vim` as its editor.
- Without repository secrets the APK is debug-signed with a key that changes
  on every run, so uninstall the previous build first. Add the `KEYSTORE`
  (base64 of the .jks), `SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS` and
  `SIGNING_KEY_PASSWORD` secrets to get a signed release APK instead.
- App resources (`term/src/main/res`, `term/src/vim/res/raw/*.zip`, ...) are
  not generated; `.github/check-payload.sh` lists anything missing.
- `patches/` holds the Android patches for Vim 9.2 (`patches/vim-9.1/` has the
  originals for 9.1).
