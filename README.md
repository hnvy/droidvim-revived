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


# Building Vim and the APK with GitHub Actions

`.github/workflows/build-vim-apk.yml` cross-compiles Vim (default `v9.2.0501`) for
arm64-v8a, armeabi-v7a, x86_64 and x86 with the Android NDK, rebuilds the Vim
runtime archives, puts both into this tree and builds the DroidVim APK.

- It runs on every push. To pick another Vim version, add Lua, pass extra
  `configure` flags or skip patches that no longer apply, use
  **Actions → Build Vim for Android + DroidVim APK → Run workflow**.
- Results are under **Artifacts** on the run page: `DroidVim-vim<version>-<debug|release>`
  (the APK), plus `vim-android-<abi>` and `vim-runtime`.
- Without repository secrets the APK is debug-signed with a key that changes on
  every run, so uninstall the previous build first. Add the `KEYSTORE`
  (base64 of the .jks), `SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS` and
  `SIGNING_KEY_PASSWORD` secrets to get a signed release APK instead.
- The APK needs the prebuilt files from the `build` branch (resources, bash,
  grep, scripts, ...). `.github/check-payload.sh` lists anything missing.
- `patches/` holds the Android patches for Vim 9.2 (`patches/vim-9.1/` has the
  originals for 9.1).
