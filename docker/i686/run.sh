#!/bin/sh
# Build the i686 test image and run a command in it against this working tree (default: a shell).
#
#   docker/i686/run.sh                    # shell, after `uv sync --frozen`
#   docker/i686/run.sh uv run pytest      # any command
#   docker/i686/run.sh --usb uv run wifit3
#
# Options (before the command):
#   --usb      pass the host USB bus through (--privileged), to drive real cards
#   --no-dev   sync runtime dependencies only
#   --reset    delete the venv volume first, for a sync from scratch
#   --rebuild  rebuild the image without Docker's layer cache
set -eu

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
image=wifit3-i686
volume=wifit3-i686

usb=""
sync=""
build_flags=""
while [ $# -gt 0 ]; do
    case "$1" in
        --usb) usb=1 ;;
        --no-dev) sync="--no-dev" ;;
        --reset) docker volume rm -f "$volume" >/dev/null ;;
        --rebuild) build_flags="--no-cache" ;;
        -h|--help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        --) shift; break ;;
        -*) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
        *) break ;;
    esac
    shift
done
[ $# -gt 0 ] || set -- bash

# shellcheck disable=SC2086  # build_flags is empty or one flag
docker build -q $build_flags -t "$image" "$here" >/dev/null

set -- -v "$repo":/src -v "$volume":/opt/wifit3 -e WIFIT3_SYNC="$sync" -e TERM="${TERM:-xterm}" \
    "$image" "$@"
[ -z "$usb" ] || set -- --privileged -v /dev/bus/usb:/dev/bus/usb "$@"
if [ -t 0 ] && [ -t 1 ]; then set -- -it "$@"; fi
exec docker run --rm "$@"
