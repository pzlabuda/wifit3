#!/usr/bin/env python3
"""Build libusb-package's i686 Linux wheel from source into vendor/wheels/ and re-lock.

For releases with no i686 Linux wheel, like 1.0.26.4 to 1.0.30.0 (pyocd/libusb-package#40).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PYPROJECT = REPO / "pyproject.toml"
VENDOR_DIR = REPO / "vendor" / "wheels"
UPSTREAM = "https://github.com/pyocd/libusb-package.git"
CIBUILDWHEEL = "cibuildwheel@4.1.0"
SOURCE_LINE = re.compile(r'^(libusb-package = \{ path = ")([^"]+)(".*)$', re.M)
FLOOR_LINE = re.compile(r'^(\s*"libusb-package>=)[^"]+(",)$', re.M)
SOURCES_ENTRY = """[tool.uv.sources]
# Vendored by scripts/vendor_libusb_package.py, which also rewrites this path and the floor.
libusb-package = {{ path = "{path}", marker = "platform_machine == 'i686'" }}

"""


def run(*cmd: str, cwd: Path | None = None, env: dict | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def fetch_sources(version: str, dest: Path) -> None:
    run("git", "clone", "--quiet", "--depth", "1", "--branch", f"v{version}", UPSTREAM, str(dest))
    # The libusb submodule URL is SSH; fetch it over HTTPS so no GitHub keys are needed.
    run("git", "-c", "url.https://github.com/.insteadOf=git@github.com:", "submodule", "update",
        "--quiet", "--init", "--depth", "1", cwd=dest)


def build_wheel(version: str, src: Path, out: Path) -> Path:
    env = os.environ | {
        "CIBW_BUILD": "cp3*-manylinux_i686",
        "CIBW_SKIP": "*t-*",
        "CIBW_MANYLINUX_I686_IMAGE": "manylinux2014",
        "CIBW_ENVIRONMENT": f"SETUPTOOLS_SCM_PRETEND_VERSION={version}",
    }
    run("uvx", CIBUILDWHEEL, "--platform", "linux", "--archs", "i686", "--output-dir", str(out),
        ".", cwd=src, env=env)
    wheels = list(out.glob(f"libusb_package-{version}-*.whl"))
    if len(wheels) != 1:
        sys.exit(f"expected one libusb_package-{version} wheel in {out}, got {wheels}")
    return wheels[0]


def vendor(wheel: Path) -> Path:
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    for old in VENDOR_DIR.glob("libusb_package-*.whl"):
        old.unlink()
    return Path(shutil.copy2(wheel, VENDOR_DIR))


def point_pyproject_at(wheel: Path, version: str) -> None:
    text = PYPROJECT.read_text()
    if not FLOOR_LINE.search(text):
        sys.exit('pyproject.toml lacks the "libusb-package>=..." dependency')
    rel = wheel.relative_to(REPO).as_posix()
    if SOURCE_LINE.search(text):
        text = SOURCE_LINE.sub(lambda m: f"{m[1]}{rel}{m[3]}", text)
    elif "[tool.uv.sources]" in text:
        sys.exit("[tool.uv.sources] exists without a libusb-package entry: add it by hand")
    elif "\n[dependency-groups]" in text:
        entry = SOURCES_ENTRY.format(path=rel)
        text = text.replace("\n[dependency-groups]", f"\n{entry}[dependency-groups]", 1)
    else:
        text = f"{text.rstrip()}\n\n{SOURCES_ENTRY.format(path=rel).rstrip()}\n"
    text = FLOOR_LINE.sub(lambda m: f"{m[1]}{version}{m[2]}", text)
    PYPROJECT.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True, help="libusb-package release tag, no 'v'")
    args = parser.parse_args()

    for tool in ("git", "docker", "uvx", "uv"):
        if shutil.which(tool) is None:
            sys.exit(f"{tool} not found: needs git, docker and uv on an x86_64 Linux host")

    with tempfile.TemporaryDirectory(prefix="libusb-package-") as tmp:
        src, out = Path(tmp, "src"), Path(tmp, "wheelhouse")
        fetch_sources(args.version, src)
        wheel = vendor(build_wheel(args.version, src, out))
    point_pyproject_at(wheel, args.version)
    run("uv", "lock", cwd=REPO)
    print(f"\nVendored {wheel.relative_to(REPO)}; commit it with pyproject.toml and uv.lock.")


if __name__ == "__main__":
    main()
