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

| What | How |
| --- | --- |
| Vim (default `v9.2.0501`), xxd, Vim runtime | Vim source + `patches/`, Android NDK; built every run |
| grep, diff, ctags | latest GNU grep, GNU diffutils, Universal Ctags, Android NDK; optional (`BUILD_CMD_TOOLS`) |
| bash, ncurses tools, zip, unzip, busybox, proot, am | [termux-packages](https://github.com/termux/termux-packages) built for `com.droidvim`, repackaged by `.github/droidvim-pack.py`; built once, then reused (see below) |
| git, Python 3 + pip | termux-packages, as above (Python without Tkinter and its test suite); optional (`WITH_GIT`, `WITH_PYTHON`) |
| Helper scripts (`vim.app`, `sh.app`, `busybox-setup`, ...) | `payload/scripts/` |

## The Termux tools: build once, then reuse

Building the Termux tools takes about an hour, so runs reuse them. The
**termux_tools** option (or the `TERMUX_TOOLS` repository variable) chooses how:

| Mode | What happens |
| --- | --- |
| `auto` (default) | Reuse the tools from the most recent earlier run that built all of them with the same git/Python choice; build them only if there is none. |
| `build` | Always build them, e.g. to update to newer versions. |
| `reuse` | Reuse from the run given in **termux_reuse_run** (a run ID or URL), or the latest one; fail if there is none. |
| `repo` | Use the prebuilt files already committed in the repository. |

- So the first run takes about an hour, later runs only a few minutes. To
  update bash, git, Python & co., run once with `termux_tools: build`.
- A run marks its tools as reusable only if every ABI built completely. A
  partly failed build can still be reused by giving its run ID.
- What's stored and reused are the Termux packages themselves; every run
  converts them into DroidVim's format with `.github/droidvim-pack.py`, so
  fixes to that script apply without rebuilding. Tools stored by versions of
  this workflow before that change can't be reused: run once with `build`.
- Reuse works for as long as the run's artifacts are kept (90 days by
  default; Settings → Actions → General). Once they expire, `auto` simply
  builds again. Each reusable run stores roughly 100–250 MB of artifacts;
  on private repositories this counts towards your Actions storage quota.
- For something permanent, download the `termux-payload-*` artifacts of a
  good run, commit their contents into `term/src/...`, and use `repo` mode.
- In `auto` mode, giving a termux-packages version other than `master` builds
  (cached per termux-packages commit, so repeating it is fast).
- Pushes wait for a running build to finish instead of cancelling it.

## Publishing releases

Built APKs can be published on the repository's **Releases** page, with
release notes listing the Vim and tool versions, where the Termux tools came
from, the signing key and a SHA-256 checksum:

- **Push a tag**, e.g. `git tag v2.6.0 && git push origin v2.6.0`: the run
  publishes a release named after the tag. The app's own version still comes
  from `versionName`/`versionCode` in `build.gradle`, so bump those first.
- **Run workflow** with **release** set to `prerelease` or `release`: the
  release gets a tag like `v2.5.0-vim9.2.0501-build42` on the built commit.
- **Every push to a branch**: set the repository variable `PUBLISH_RELEASE`
  to `prerelease` or `release` (default `none`).
- Re-running a run updates its release instead of creating another one.
- Debug-signed APKs are marked as such in the notes (users must uninstall the
  previous build first). Add the signing secrets below for real releases.

## Choosing what to build

- **Run workflow** (Actions → Build Vim for Android + DroidVim APK) shows all
  options.
- **Push builds** use repository variables (Settings → Secrets and variables
  → Actions → Variables): `TERMUX_TOOLS` (`auto`/`build`/`reuse`/`repo`),
  `TERMUX_REUSE_RUN`, `TERMUX_PACKAGES_REF`, `PUBLISH_RELEASE`
  (`none`/`prerelease`/`release`), and `BUILD_CMD_TOOLS`, `WITH_GIT`,
  `WITH_PYTHON`, `ENABLE_NLS`, `ENABLE_LUA` (`true`/`false`). `ANDROID_API`
  (default `21`) must match `minSdkVersion` in `build.gradle`.
- When a part isn't built or reused, the prebuilt copies already in the
  repository are used, and the run warns about any that are missing.
- Each run lists where every part came from on its summary page.

## Notes

- Results are under **Artifacts** on the run page: `DroidVim-vim<version>-<debug|release>`
  (the APK), plus `vim-android-<abi>`, `vim-runtime` and `termux-payload-<abi>`.
- The Termux-built tools need Android 7.0 (API 24) or newer. Vim, grep, diff
  and ctags are built for API 21.
- git and Python add roughly 30–50 MB to the APK. git uses `less` as its
  pager and DroidVim's `vim` as its editor.
- Without repository secrets the APK is debug-signed with a key that changes
  on every run, so uninstall the previous build first. Add the `KEYSTORE`
  (base64 of the .jks), `SIGNING_STORE_PASSWORD`, `SIGNING_KEY_ALIAS` and
  `SIGNING_KEY_PASSWORD` secrets to get a signed release APK instead.
- App resources (`term/src/main/res`, `term/src/vim/res/raw/*.zip`, ...) are
  not generated; `.github/check-payload.sh` lists anything missing.
- `patches/` holds the Android patches for Vim 9.2 (`patches/vim-9.1/` has the
  originals for 9.1).
