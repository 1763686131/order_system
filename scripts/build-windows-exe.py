"""Build the Windows x64 demonstration executable from the current source."""

import hashlib
import os
import platform
import shutil
import struct
import subprocess
import sys
from ctypes import WinDLL, c_long, c_uint, c_wchar_p
from pathlib import Path


def build_icon(root, cache):
    try:
        from PIL import Image, ImageOps
    except ImportError as error:
        raise SystemExit("Install the dependencies in scripts/windows-exe-requirements.txt before building.") from error

    source = root / "scripts" / "icon" / "appicon.png"
    if not source.is_file():
        raise SystemExit(f"Missing build icon: {source}")

    # PyInstaller compares icon paths when deciding whether to reuse an EXE.
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    icon = cache / f"appicon-{digest}.ico"
    cache.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        square = ImageOps.pad(image.convert("RGBA"), (256, 256), method=Image.Resampling.LANCZOS, color=(0, 0, 0, 0))
        square.save(icon)
    return icon


def notify_explorer(executable):
    notify = WinDLL("shell32").SHChangeNotify
    notify.argtypes = (c_long, c_uint, c_wchar_p, c_wchar_p)
    notify.restype = None
    # SHCNE_UPDATEITEM with a Unicode path; don't wait for Explorer to refresh.
    notify(0x00002000, 0x2005, str(executable), None)


def main():
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64") or struct.calcsize("P") != 8:
        raise SystemExit("Use a 64-bit Python installation on Windows x64.")

    root = Path(__file__).resolve().parents[1]
    cache = root / ".exe-build.local"
    output = root / "release" / "windows"
    npm = shutil.which("npm.cmd")
    if not npm:
        raise SystemExit("Install Node.js and run npm ci before building.")
    icon = build_icon(root, cache)
    subprocess.run([npm, "run", "build"], cwd=root, check=True)

    os.environ["PYINSTALLER_CONFIG_DIR"] = str(cache / "cache")
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onefile", "--windowed", "--noupx",
            "--name", "OrderSystem-Demo",
            "--icon", str(icon),
            "--add-data", f"{root / 'dist'}:frontend",
            "--distpath", str(output),
            "--workpath", str(cache / "work"),
            "--specpath", str(cache),
            "backend/desktop.py",
        ],
        cwd=root,
        check=True,
    )

    executable = output / "OrderSystem-Demo.exe"
    with executable.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    notify_explorer(executable)
    print(f"{executable}\nSHA-256 {digest}")


if __name__ == "__main__":
    main()
