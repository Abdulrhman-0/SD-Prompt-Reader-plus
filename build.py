#!/usr/bin/env python3
"""Easy build entry point for SD Prompt Reader+.

Usage
-----
    python build.py              build the GUI executable (default)
    python build.py --no-clean   keep the previous PyInstaller cache
    python build.py --check      only report whether the build can run

On Windows this is the same build the project has always used - it just wires up
the pieces that used to be done by ``setup.py`` plus a couple of extra packages:

    1. sync ``sd_prompt_reader/__version__.py`` with ``pyproject.toml``
    2. refresh the Windows version resource (``file_version_info.txt``)
    3. run PyInstaller with ``win.spec``

Nothing is installed automatically: if PyInstaller is missing the script tells
you the exact command to run.
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import NoReturn

ROOT = Path(__file__).resolve().parent
PYPROJECT = ROOT / "pyproject.toml"
VERSION_FILE = ROOT / "sd_prompt_reader" / "__version__.py"
WINDOWS_VERSION_FILE = ROOT / "file_version_info.txt"
SPEC_FILE = ROOT / "win.spec"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build"

REQUIRED = {"PyInstaller": "pyinstaller"}


def fail(message: str) -> NoReturn:
    print(f"\n[build] ERROR: {message}")
    raise SystemExit(1)


def read_version() -> str:
    """Read the project version without depending on ``toml``."""
    if PYPROJECT.is_file():
        match = re.search(
            r'^\s*version\s*=\s*"([^"]+)"', PYPROJECT.read_text(encoding="utf-8"), re.M
        )
        if match:
            return match.group(1)
    if VERSION_FILE.is_file():
        match = re.search(
            r'VERSION\s*=\s*"([^"]+)"', VERSION_FILE.read_text(encoding="utf-8")
        )
        if match:
            return match.group(1)
    fail("could not determine the project version")


def numeric_version(version: str) -> tuple:
    """``1.0.0`` -> ``(1, 0, 0, 0)``; non numeric parts are ignored."""
    parts = [int(part) for part in re.findall(r"\d+", version)][:4]
    return tuple(parts + [0] * (4 - len(parts)))


def sync_version_module(version: str) -> None:
    wanted = f'VERSION = "{version}"\n'
    if VERSION_FILE.is_file() and VERSION_FILE.read_text(encoding="utf-8") == wanted:
        print(f"[build] version already up to date ({version})")
        return
    VERSION_FILE.write_text(wanted, encoding="utf-8")
    print(f"[build] wrote {VERSION_FILE.name} -> {version}")


def sync_windows_version(version: str) -> None:
    """(Re)generate the Windows version resource from the PyInstaller classes.

    The checked-in ``file_version_info.txt`` could not be deserialized by
    PyInstaller 6.6 (its ``eval()`` raised a ``SyntaxError``), which made every
    Windows build fail. Generating the file from ``VSVersionInfo`` itself is
    the round-trip safe way to do it, and it needs no extra package - unlike
    the optional ``pyinstaller-versionfile`` used by ``setup.py``.
    """
    if sys.platform != "win32":
        return

    try:
        from PyInstaller.utils.win32.versioninfo import (
            FixedFileInfo,
            StringFileInfo,
            StringStruct,
            StringTable,
            VarFileInfo,
            VarStruct,
            VSVersionInfo,
            load_version_info_from_text_file,
        )
    except ImportError:
        print("[build] PyInstaller versioninfo helpers unavailable, skipping")
        return

    numbers = numeric_version(version)
    dotted = ".".join(str(part) for part in numbers)
    # The StringTable key must be the hex form of (language << 16 | codepage),
    # i.e. "040904B0" for en-US (0x0409) + Unicode (0x04B0). Passing the integer
    # 0x040904B0 makes PyInstaller stringify it as decimal "67699888", which
    # Windows cannot match against the VarFileInfo translation, so every string
    # field (ProductName, FileDescription, ...) would read back empty.
    language = "040904B0"

    info = VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=numbers,
            prodvers=numbers,
            mask=0x3F,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo(
                [
                    StringTable(
                        language,
                        [
                            StringStruct("CompanyName", ""),
                            StringStruct("FileDescription", "SD Prompt Reader+"),
                            StringStruct("FileVersion", dotted),
                            StringStruct("InternalName", "SD Prompt Reader+"),
                            StringStruct(
                                "LegalCopyright",
                                "Copyright (C) 2026 Abdulrhman-0. MIT License.",
                            ),
                            StringStruct("OriginalFilename", "SD Prompt Reader+.exe"),
                            StringStruct("ProductName", "SD Prompt Reader+"),
                            StringStruct("ProductVersion", dotted),
                        ],
                    )
                ]
            ),
            VarFileInfo([VarStruct("Translation", [1033, 1200])]),
        ],
    )

    # newline="" keeps the file LF-only on Windows; the loader is sensitive to
    # getting a file it cannot eval().
    with open(WINDOWS_VERSION_FILE, "w", encoding="utf-8", newline="\n") as file:
        file.write(str(info))

    try:
        load_version_info_from_text_file(str(WINDOWS_VERSION_FILE))
    except Exception as error:  # noqa: BLE001 - surface it before PyInstaller does
        fail(f"generated version resource is not loadable: {error}")
    print(f"[build] wrote file_version_info.txt -> {dotted}")


def check_environment() -> None:
    missing = []
    for module, package in REQUIRED.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        fail(
            "missing build dependencies: "
            + ", ".join(missing)
            + f"\n        install them with:\n            {Path(sys.executable).name} -m pip install "
            + " ".join(missing)
        )
    if not SPEC_FILE.is_file():
        fail(f"{SPEC_FILE.name} not found next to build.py")
    print(f"[build] python  : {sys.executable}")
    print(f"[build] platform: {sys.platform}")


def run_pyinstaller(clean: bool) -> None:
    args = [str(SPEC_FILE)]
    if clean:
        args.append("--clean")
    args.append("--noconfirm")

    try:
        import PyInstaller.__main__

        PyInstaller.__main__.run(args)
    except SystemExit as error:
        if error.code not in (0, None):
            fail(f"PyInstaller exited with code {error.code}")


def report_artifacts() -> None:
    print("\n[build] artifacts:")
    if not DIST_DIR.is_dir():
        print("    (dist/ is empty - did the build fail?)")
        return
    for item in sorted(DIST_DIR.iterdir()):
        if item.is_dir():
            size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
            print(f"    {item.name}/  ({size / 1_048_576:.1f} MB)")
        else:
            print(f"    {item.name}  ({item.stat().st_size / 1_048_576:.1f} MB)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build SD Prompt Reader executables.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--no-clean", action="store_true", help="reuse the PyInstaller cache")
    parser.add_argument("--check", action="store_true", help="only check the environment")
    parser.add_argument(
        "--keep-work", action="store_true", help="keep the build/ work directory"
    )
    options = parser.parse_args()

    # The spec file uses paths relative to the project root, so always build
    # from there no matter where the script was started from.
    os.chdir(ROOT)

    print("[build] SD Prompt Reader")
    check_environment()

    version = read_version()
    print(f"[build] version : {version}")
    if options.check:
        print("[build] environment looks good (nothing was built)")
        return

    sync_version_module(version)
    if sys.platform == "win32":
        sync_windows_version(version)

    run_pyinstaller(clean=not options.no_clean)
    report_artifacts()

    if not options.keep_work and BUILD_DIR.is_dir():
        shutil.rmtree(BUILD_DIR, ignore_errors=True)

    print("\n[build] done")


if __name__ == "__main__":
    main()
