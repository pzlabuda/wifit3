# 32-bit (i686) Debian with Python, uv and libusb, for checking that wifit3 syncs and runs on i686.
#
# The image holds only the toolchain. The repo is bind-mounted at /src, so you always test your
# working tree; the venv + uv cache live in /opt/wifit3 (a named volume), never in your host's .venv.
#
# Use docker/i686/run.sh (builds, then runs; see its --help). By hand, from the repo root:
#
#   docker build -t wifit3-i686 docker/i686
#   docker run --rm -it -v "$PWD":/src -v wifit3-i686:/opt/wifit3 wifit3-i686 [command]
#
# Every start runs `uv sync --frozen` first; -e WIFIT3_SYNC="--no-dev" skips the dev group.
#
# The entrypoint runs under `linux32`: on an x86_64 kernel `uname -m` (and so uv's
# platform_machine marker) would otherwise say x86_64 and select the 64-bit dependencies.

ARG DEBIAN=bookworm
FROM --platform=linux/386 i386/debian:${DEBIAN}

ARG UV_VERSION=0.12.6

# python3: uv publishes no managed i686 Linux Python, the interpreter must come from the distro.
# build-essential + headers: markupsafe, msgpack and pillow ship no i686 wheels (dev group only).
# libusb-1.0-0 / usbutils: system libusb as a fallback, lsusb to see what the container can reach.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        ca-certificates curl python3 python3-dev \
        build-essential pkg-config libjpeg-dev zlib1g-dev \
        libusb-1.0-0 usbutils tshark \
 && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-i686-unknown-linux-gnu.tar.gz" \
    | tar xz -C /usr/local/bin --strip-components=1

ENV UV_PROJECT_ENVIRONMENT=/opt/wifit3/venv \
    UV_PYTHON=/usr/bin/python3 \
    UV_PYTHON_DOWNLOADS=never \
    UV_CACHE_DIR=/opt/wifit3/uv-cache \
    UV_LINK_MODE=copy \
    PYTHONPYCACHEPREFIX=/opt/wifit3/pycache \
    WIFIT3_SYNC=""

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

WORKDIR /src
ENTRYPOINT ["linux32", "/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
