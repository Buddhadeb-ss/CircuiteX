#!/usr/bin/env python3
"""Cross-platform standalone LaTeX compiler installer for CircuiteX.

Downloads and installs the portable 'tectonic' TeX engine into ~/.gemini/bin
so notes can be compiled to PDF immediately with zero external dependencies.
Works on Windows, macOS, and Linux without root/admin permissions.
"""
import io
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

TECTONIC_VERSION = "0.17.0"
INSTALL_DIR = Path.home() / ".gemini" / "bin"


def get_download_url():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return (
            f"https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40{TECTONIC_VERSION}/"
            f"tectonic-{TECTONIC_VERSION}-x86_64-pc-windows-msvc.zip",
            "zip",
            "tectonic.exe",
        )
    elif system == "darwin":  # macOS
        arch = "aarch64" if "arm" in machine or "m1" in machine or "m2" in machine else "x86_64"
        return (
            f"https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40{TECTONIC_VERSION}/"
            f"tectonic-{TECTONIC_VERSION}-{arch}-apple-darwin.tar.gz",
            "tar",
            "tectonic",
        )
    elif system == "linux":
        arch = "aarch64" if "aarch64" in machine or "arm64" in machine else "x86_64"
        return (
            f"https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40{TECTONIC_VERSION}/"
            f"tectonic-{TECTONIC_VERSION}-{arch}-unknown-linux-musl.tar.gz",
            "tar",
            "tectonic",
        )
    else:
        raise RuntimeError(f"Unsupported operating system: {system}")


def install_tectonic(target_dir=None):
    target_dir = Path(target_dir) if target_dir else INSTALL_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    exe_name = "tectonic.exe" if sys.platform == "win32" else "tectonic"
    dest_path = target_dir / exe_name

    if dest_path.exists():
        print(f"Tectonic already installed at: {dest_path}")
        return dest_path

    url, archive_type, member_name = get_download_url()
    print(f"Downloading portable Tectonic compiler from:\n  {url}")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 CircuiteX-Installer"})
    with urllib.request.urlopen(req) as response:
        content = response.read()

    print(f"Downloaded {len(content) // 1024} KB. Extracting...")
    if archive_type == "zip":
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            with zf.open(member_name) as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
    else:  # tar.gz
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tf:
            member = tf.getmember(member_name)
            with tf.extractfile(member) as src, open(dest_path, "wb") as dst:
                shutil.copyfileobj(src, dst)

    # Ensure executable permission on Unix
    dest_path.chmod(dest_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # Verify installation
    res = subprocess.run([str(dest_path), "--version"], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Successfully installed: {res.stdout.strip()} at {dest_path}")
        return dest_path
    else:
        raise RuntimeError(f"Failed to execute installed binary: {res.stderr}")


if __name__ == "__main__":
    try:
        path = install_tectonic()
        print(f"\nCompiler ready: {path}")
    except Exception as e:
        print(f"Error installing compiler: {e}", file=sys.stderr)
        sys.exit(1)

