# DroidVim-revived
 
This project is a fork of [DroidVim (dead link as repo was deleted)](https://github.com/shiftrot/droidvim) by shiftrot, which is itself based on [Terminal Emulator for Android](https://github.com/jackpal/Android-Terminal-Emulator) by Jack Palevich.
 
# Licensing
 
- This project is licensed under the GNU General Public License, version 3 (GPL-3.0). See [LICENSE](LICENSE) for the full license text.  
- Code inherited from DroidVim and [Terminal Emulator for Android](https://github.com/jackpal/Android-Terminal-Emulator) was released under the Apache License, Version 2.0, and remains available under that license; its original copyright and license notices are kept.

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
- Reuse works for as long as the run's artifacts are kept (90 days by
  default; Settings → Actions → General). Once they expire, `auto` simply
  builds again. Each reusable run stores roughly 100–250 MB of artifacts;
  on private repositories this counts towards your Actions storage quota.
- For something permanent, download the `termux-payload-*` artifacts of a
  good run, commit their contents into `term/src/...`, and use `repo` mode.
- In `auto` mode, giving a termux-packages version other than `master` builds
  (cached per termux-packages commit, so repeating it is fast).
- Pushes wait for a running build to finish instead of cancelling it.

## Choosing what to build

- **Run workflow** (Actions → Build Vim for Android + DroidVim APK) shows all
  options.
- **Push builds** use repository variables (Settings → Secrets and variables
  → Actions → Variables): `TERMUX_TOOLS` (`auto`/`build`/`reuse`/`repo`),
  `TERMUX_REUSE_RUN`, `TERMUX_PACKAGES_REF`, and `BUILD_CMD_TOOLS`, `WITH_GIT`,
  `WITH_PYTHON` (`true`/`false`). `ANDROID_API` (default `21`) must match
  `minSdkVersion` in `build.gradle`.
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
