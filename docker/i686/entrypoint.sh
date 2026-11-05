#!/bin/sh
# Sync the mounted repo into /opt/wifit3/venv against the committed lock, then run the given command.
set -eu

if [ ! -f /src/pyproject.toml ]; then
    echo "wifit3 repo not mounted: run with -v \"\$PWD\":/src from the repo root" >&2
    exit 1
fi

echo "== $(uname -m), $(python3 -V), $(uv --version)" >&2
# shellcheck disable=SC2086  # WIFIT3_SYNC holds extra flags, e.g. "--no-dev"
uv sync --frozen $WIFIT3_SYNC
exec "$@"
