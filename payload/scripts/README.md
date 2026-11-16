# DroidVim helper scripts

These are DroidVim's own shell scripts. Android only lets apps run files
from their native library directory, so they are shipped as `lib*.so` files
and linked into `$APPFILES/bin` by the app (see `JniLibsToBin.java`).

`build-vim-apk.yml` copies each `<dir>/<name>` here to
`term/src/<dir>/jniLibs/<abi>/<name>` for every ABI.

Restored from DroidVim 2.5.0, with three changes for the tools that
the workflow builds with today's termux-packages:

- `main/libam.so`: starts `com.termux.termuxam.Am` (current termux-am)
  and keeps `am.apk` read-only, as Android 14+ requires.
- `main/libusr.bin.busybox-setup.so`: sets `LD_LIBRARY_PATH` to
  `$APPFILES/usr/lib`, because Termux builds busybox as a small program
  plus `libbusybox.so`.
- `proot/libsuproot.so`: points `PROOT_LOADER` at `$APPFILES/bin/loader`
  and `loader-m32`, the names the app actually links them under.
