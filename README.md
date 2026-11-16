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

`.github/workflows/build-vim-apk.yml` builds everything DroidVim runs on the
device, for arm64-v8a, armeabi-v7a, x86_64 and x86, and packages the APK:

| What | How |
| --- | --- |
| Vim (default `v9.2.0501`), xxd, Vim runtime | Vim source + `patches/`, Android NDK, static ncurses/libiconv/libintl |
| grep, diff, ctags | latest GNU grep, GNU diffutils and Universal Ctags, Android NDK |
| bash, readline, ncurses tools, zip, unzip, busybox, proot, am | [termux-packages](https://github.com/termux/termux-packages) built for `com.droidvim`, repackaged by `.github/droidvim-pack.py` |
| Helper scripts (`vim.app`, `sh.app`, `busybox-setup`, ...) | `payload/scripts/` |

- It runs on every push. **Actions → Build Vim for Android + DroidVim APK →
  Run workflow** lets you pick the Vim version, the termux-packages version,
  add Lua or extra Vim `configure` flags, or skip patches that no longer apply.
- Results are under **Artifacts** on the run page: `DroidVim-vim<version>-<debug|release>`
  (the APK), plus the separate `vim-android-<abi>`, `vim-runtime` and
  `termux-payload-<abi>` builds.
- The Termux-built tools need Android 7.0 (API 24) or newer. Vim, grep, diff
  and ctags are built for API 21.
- The first run takes a while (the Termux build is 30–60 minutes per ABI);
  later runs reuse cached builds until termux-packages changes.
- Without repository secrets the APK is debug-signed with a key that changes
  on every run, so uninstall the previous build first. Add the `KEYSTORE`
  (base64 of the .jks), `SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS` and
  `SIGNING_KEY_PASSWORD` secrets to get a signed release APK instead.
- App resources (`term/src/main/res`, `term/src/vim/res/raw/*.zip`, ...) are
  not generated; `.github/check-payload.sh` lists anything missing.
- `patches/` holds the Android patches for Vim 9.2 (`patches/vim-9.1/` has the
  originals for 9.1).
