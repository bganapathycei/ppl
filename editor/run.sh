#!/usr/bin/env bash
# Start the PPL visual editor dev server.
set -euo pipefail

EDITOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$EDITOR_DIR/.." && pwd)"
cd "$EDITOR_DIR"

HOST="127.0.0.1"
PORT="8765"
OPEN_BROWSER=1

usage() {
    cat <<'EOF'
Usage: ./run.sh [--host HOST] [--port PORT] [--no-browser]

Starts editor/serve.py with the PPL runtime on PYTHONPATH via serve.py.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            HOST="${2:?missing value for --host}"
            shift 2
            ;;
        --port)
            PORT="${2:?missing value for --port}"
            shift 2
            ;;
        --no-browser)
            OPEN_BROWSER=0
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [[ ! -f "$ROOT/src/ppl/__init__.py" ]]; then
    echo "PPL source not found at $ROOT/src/ppl. Run from a full repository checkout." >&2
    exit 1
fi

PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "Python 3.10+ is required." >&2
    exit 1
fi

URL="http://${HOST}:${PORT}/"
echo "PPL editor -> $URL"
echo "Press Ctrl+C to stop."

if [[ "$OPEN_BROWSER" -eq 1 ]]; then
    (
        sleep 1
        if command -v xdg-open >/dev/null 2>&1; then
            xdg-open "$URL" >/dev/null 2>&1 || true
        elif command -v open >/dev/null 2>&1; then
            open "$URL" >/dev/null 2>&1 || true
        fi
    ) &
fi

exec "$PYTHON" serve.py --host "$HOST" --port "$PORT" "$@"
