#!/usr/bin/env python3
"""Turn Termux .deb packages into DroidVim's prebuilt payload layout.

DroidVim ships command-line tools the way its original build branch did:

* every executable or shared library of a bundle becomes
  jniLibs/<abi>/lib<bundle>NNNNN.so, and a raw resource
  <bundle>_symlinks_<arch> lists where the app links each one
  ("lib<bundle>00000.so|usr/bin/bash");
* everything else of the bundle (symlinks, config files, directories)
  goes into jniLibs/<abi>/lib<bundle>.tar.so, an .tar.xz archive the app
  unpacks into its files directory;
* a few programs are single libraries the app links by fixed name
  (libbusybox.so, libproot.so, libloader.so, libam.apk.so).

Output (under --out):
  bundles/<bundle>/<abi>/lib<bundle>*.so   whole set for that bundle/ABI
  libs/<src dir>/<abi>/<lib>.so            single libs (src dir = default
                                           term/src/<dir>/jniLibs to use)
  raw/<name>                               raw resources for term/src/main/res/raw
"""

import argparse
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

# Packages whose files only matter as shared libraries for other tools.
LIB_ONLY = ("pcre2", "libandroid-selinux", "libtalloc", "libandroid-shmem")

# Packages not shipped at all: static libraries, GUI parts that need X11/Tk,
# git's Perl-based svn bridge, pip wheels for ensurepip (pip itself is
# shipped as python-pip), and Tcl, which is only needed to build SQLite.
SKIP = re.compile(r"-static$|^python-tkinter$|^python-ensurepip-wheels$"
                  r"|^git-(gui|gitk|svn)$|^gitk$|^tcl$|^libsqlite-tcl$")

# Paths never shipped (docs, headers, static libs, terminfo which the app
# installs from its own terminfo_min resource, ...).
DROP = re.compile(
    r"^usr/(include|var|share/(man|doc|info|locale|terminfo|LICENSES|"
    r"bash-completion|zsh|fish|aclocal|readline|pkgconfig|examples|"
    r"gitweb|git-gui|gitk))(/|$)"
    r"|^usr/lib/(pkgconfig|cmake)(/|$)"
    # Python's own test suite and GUI modules (no Tk on DroidVim).
    r"|^usr/lib/python3[^/]*/(test|idlelib|tkinter|turtledemo|ensurepip)(/|$)"
    r"|/__pycache__(/|$)"
    r"|\.(a|la)$"
)

# DroidVim's own minimal bash.bashrc (the app copies it to ~/.bashrc).
BASHRC = "PS1='\\$ '\n"

# Android system libraries a binary may depend on.
SYSTEM_LIBS = {
    "libc.so", "libm.so", "libdl.so", "liblog.so", "libz.so",
    "libandroid.so", "libc++.so", "libstdc++.so",
}


def deb_field(deb, field):
    return subprocess.run(["dpkg-deb", "--field", deb, field], check=True,
                          capture_output=True, text=True).stdout.strip()


def is_elf(path):
    with open(path, "rb") as f:
        return f.read(4) == b"\x7fELF"


def needs_chunk(path):
    """Regular files that must be executable or loadable become .so chunks."""
    st = os.lstat(path)
    return is_elf(path) or bool(st.st_mode & 0o111)


def elf_info(path):
    """(soname, [needed]) via readelf; empty on failure."""
    try:
        out = subprocess.run(["readelf", "-d", path], check=True,
                             capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None, []
    soname = re.findall(r"\(SONAME\).*\[(.*)\]", out)
    needed = re.findall(r"\(NEEDED\).*\[(.*)\]", out)
    return (soname[0] if soname else None), needed


def route(pkg, rel):
    """Where a file of package `pkg` at `rel` (usr/...) goes.

    Returns a list of ("bundle", name) / ("lib", src_dir, lib_name) targets.
    """
    if pkg == "busybox":
        if rel == "usr/bin/busybox":
            return [("lib", "main", "libbusybox.so")]
        return [("bundle", "term-bash")] if rel.startswith("usr/lib/") else []
    if pkg == "proot":
        return {
            "usr/bin/proot": [("lib", "proot", "libproot.so")],
            "usr/libexec/proot/loader": [("lib", "proot", "libloader.so")],
            "usr/libexec/proot/loader32": [("lib", "proot", "libloader-m32.so")],
        }.get(rel, [])
    if pkg == "termux-am":
        if rel == "usr/libexec/termux-am/am.apk":
            return [("lib", "droidvim", "libam.apk.so")]
        return []
    if pkg in ("zip", "unzip"):
        return [("bundle", pkg)]
    if pkg in ("libbz2", "bzip2"):
        return [("bundle", "zip"), ("bundle", "unzip")]
    if pkg.startswith(LIB_ONLY):
        return [("bundle", "term-bash")] if rel.startswith("usr/lib/") else []
    return [("bundle", "term-bash")]


def resolve_link(rel, entries, package):
    """Follow a symlink inside a bundle to the usr/... path it ends at.

    Returns None when the chain leaves the bundle or is too long.
    """
    prefix = f"/data/data/{package}/files/"
    seen = 0
    while seen < 20:
        entry = entries.get(rel)
        if entry is None or entry[1] != "symlink":
            return rel if entry is not None else None
        link = entry[2]
        if link.startswith(prefix):
            rel = link[len(prefix):]
        elif link.startswith("/"):
            return None
        else:
            rel = os.path.normpath(os.path.join(os.path.dirname(rel), link))
        seen += 1
    return None


def add_tar_entry(tar, rel, src=None, *, kind, link=None, data=None):
    info = tarfile.TarInfo("./" + rel)
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.mtime = 0
    if kind == "dir":
        info.type, info.mode = tarfile.DIRTYPE, 0o755
        tar.addfile(info)
    elif kind == "symlink":
        info.type, info.linkname, info.mode = tarfile.SYMTYPE, link, 0o777
        tar.addfile(info)
    else:
        if data is None:
            with open(src, "rb") as f:
                data = f.read()
        info.size, info.mode = len(data), 0o644
        tar.addfile(info, io.BytesIO(data))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--debs", required=True, help="directory with .deb files")
    ap.add_argument("--abi", help="Android ABI, e.g. arm64-v8a")
    ap.add_argument("--arch",
                    help="DroidVim arch name used in raw resources (arm64, arm, x86_64, x86)")
    ap.add_argument("--package", default="com.droidvim", help="app package name")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--prune", action="store_true",
                    help="only delete the .deb files of packages DroidVim doesn't ship, then exit")
    args = ap.parse_args()

    debs = sorted(f for f in os.listdir(args.debs) if f.endswith(".deb"))
    if not debs:
        sys.exit(f"no .deb files in {args.debs}")
    if args.prune:
        for deb in debs:
            path = os.path.join(args.debs, deb)
            if SKIP.search(deb_field(path, "Package")):
                os.remove(path)
                print(f"removed {deb}")
        return
    missing = [f"--{name}" for name in ("abi", "arch", "out") if not getattr(args, name)]
    if missing:
        ap.error(f"the following arguments are required unless --prune is given: {', '.join(missing)}")

    work = tempfile.mkdtemp(prefix="droidvim-pack-")
    # bundle -> {rel: (abs_path, kind, link)}
    bundles = {}
    singles = []  # (src_dir, lib_name, abs_path)
    prefix_rel = os.path.join("data", "data", args.package, "files")

    for deb in debs:
        path = os.path.join(args.debs, deb)
        pkg = deb_field(path, "Package")
        if SKIP.search(pkg):
            print(f"{deb}: package {pkg} (skipped)")
            continue
        dest = os.path.join(work, pkg)
        subprocess.run(["dpkg-deb", "-x", path, dest], check=True)
        root = os.path.join(dest, prefix_rel)
        if not os.path.isdir(os.path.join(root, "usr")):
            print(f"warning: {deb} has no {prefix_rel}/usr (built for another package name?)",
                  file=sys.stderr)
            continue
        print(f"{deb}: package {pkg}")
        for dirpath, dirnames, filenames in os.walk(os.path.join(root, "usr")):
            for name in dirnames + filenames:
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, root)
                if DROP.search(rel):
                    continue
                if os.path.islink(full):
                    kind, link = "symlink", os.readlink(full)
                elif os.path.isdir(full):
                    continue  # directories are recreated from file paths
                else:
                    kind, link = "file", None
                for target in route(pkg, rel):
                    if target[0] == "lib":
                        if kind == "file":
                            singles.append((target[1], target[2], full))
                    else:
                        bundles.setdefault(target[1], {})[rel] = (full, kind, link)

    # proot looks for its loader under usr/libexec/proot; link the app's
    # libloader*.so there as well.
    if any(lib == "libloader.so" for _, lib, _ in singles):
        tb = bundles.setdefault("term-bash", {})
        tb["usr/libexec/proot/loader"] = (None, "alias", "libloader.so")
        if any(lib == "libloader-m32.so" for _, lib, _ in singles):
            tb["usr/libexec/proot/loader32"] = (None, "alias", "libloader-m32.so")

    if "usr/etc/bash.bashrc" in bundles.get("term-bash", {}):
        bundles["term-bash"]["usr/etc/bash.bashrc"] = (None, "data", BASHRC)

    # Termux builds git to run `pager` and `editor` (Debian alternatives);
    # point them at less and DroidVim's vim ($APPFILES/bin/vim).
    tb = bundles.get("term-bash", {})
    if "usr/bin/git" in tb:
        if "usr/bin/pager" not in tb and "usr/bin/less" in tb:
            tb["usr/bin/pager"] = (None, "symlink", "less")
        if "usr/bin/editor" not in tb:
            # $APPFILES/bin/vim is the app's libsrc.vim.default.so.
            tb["usr/bin/editor"] = (None, "alias", "libsrc.vim.default.so")

    provided = set()
    elf_files = []
    os.makedirs(args.out, exist_ok=True)

    for bundle, entries in sorted(bundles.items()):
        outdir = os.path.join(args.out, "bundles", bundle, args.abi)
        os.makedirs(outdir, exist_ok=True)
        chunks, rest = [], []
        first_by_hash = {}
        for rel in sorted(entries):
            full, kind, link = entries[rel]
            if kind == "file" and needs_chunk(full):
                # Identical copies (e.g. hard links) become symlinks to the
                # first one instead of extra copies in the APK.
                with open(full, "rb") as f:
                    digest = hashlib.sha256(f.read()).hexdigest()
                if digest in first_by_hash:
                    target = os.path.relpath(first_by_hash[digest], os.path.dirname(rel))
                    entries[rel] = (None, "symlink", target)
                    rest.append(rel)
                    continue
                first_by_hash[digest] = rel
                chunks.append(rel)
            else:
                rest.append(rel)

        lines = []
        lib_of = {}
        for i, rel in enumerate(chunks):
            lib = f"lib{bundle}{i:05d}.so"
            lib_of[rel] = lib
            shutil.copyfile(entries[rel][0], os.path.join(outdir, lib))
            lines.append(f"{lib}|{rel}")
            if is_elf(entries[rel][0]):
                elf_files.append((rel, entries[rel][0]))
                provided.add(os.path.basename(rel))

        # Links to executables and libraries (libreadline.so.8 ->
        # libreadline.so.8.3, python3 -> python3.13, git's dashed commands)
        # are listed as extra names of the same .so file instead of being
        # stored as links in the archive. The app unpacks the archive before
        # it links the .so files into place, and its built-in unpacker (used
        # whenever busybox can't run yet, e.g. on first install) skips links
        # whose target doesn't exist at that moment.
        kept = []
        for rel in rest:
            full, kind, link = entries[rel]
            if kind == "alias":  # another name for one of the app's own libs
                lines.append(f"{link}|{rel}")
                continue
            target = resolve_link(rel, entries, args.package) if kind == "symlink" else None
            if target in lib_of:
                lines.append(f"{lib_of[target]}|{rel}")
                provided.add(os.path.basename(rel))
            else:
                kept.append(rel)
        rest = kept

        dirs = set()
        for rel in chunks + rest:
            parent = os.path.dirname(rel)
            while parent:
                dirs.add(parent)
                parent = os.path.dirname(parent)
        with tarfile.open(os.path.join(outdir, f"lib{bundle}.tar.so"), "w:xz",
                          format=tarfile.GNU_FORMAT) as tar:
            for d in sorted(dirs):
                add_tar_entry(tar, d, kind="dir")
            for rel in rest:
                full, kind, link = entries[rel]
                if kind == "symlink":
                    add_tar_entry(tar, rel, kind="symlink", link=link)
                    provided.add(os.path.basename(rel))
                elif kind == "data":
                    add_tar_entry(tar, rel, kind="file", data=link.encode())
                else:
                    add_tar_entry(tar, rel, full, kind="file")

        raw = os.path.join(args.out, "raw")
        os.makedirs(raw, exist_ok=True)
        with open(os.path.join(raw, f"{bundle.replace('-', '_')}_symlinks_{args.arch}"), "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"bundle {bundle}: {len(chunks)} executables/libraries, {len(rest)} other entries")

    for src_dir, lib, full in singles:
        outdir = os.path.join(args.out, "libs", src_dir, args.abi)
        os.makedirs(outdir, exist_ok=True)
        shutil.copyfile(full, os.path.join(outdir, lib))
        if is_elf(full):
            elf_files.append((lib, full))
        print(f"single {src_dir}/{lib}")

    # Warn about libraries a binary needs that nothing provides.
    for rel, full in elf_files:
        _, needed = elf_info(full)
        missing = [n for n in needed if n not in provided and n not in SYSTEM_LIBS]
        if missing:
            print(f"warning: {rel} needs {', '.join(missing)}, which is not packaged",
                  file=sys.stderr)

    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
