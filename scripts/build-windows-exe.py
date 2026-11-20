"""Build the Windows x64 demonstration executable from the current source."""

import hashlib
import os
import platform
import shutil
import struct
import subprocess
import sys
from pathlib import Path


def main():
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64") or struct.calcsize("P") != 8:
        raise SystemExit("Use a 64-bit Python installation on Windows x64.")

    root = Path(__file__).resolve().parents[1]
    cache = root / ".exe-build.local"
    output = root / "release" / "windows"
    npm = shutil.which("npm.cmd")
    if not npm:
        raise SystemExit("Install Node.js and run npm ci before building.")
    subprocess.run([npm, "run", "build"], cwd=root, check=True)

    os.environ["PYINSTALLER_CONFIG_DIR"] = str(cache / "cache")
    subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onefile", "--windowed", "--noupx",
            "--name", "OrderSystem-Demo",
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
    print(f"{executable}\nSHA-256 {digest}")


if __name__ == "__main__":
    main()
