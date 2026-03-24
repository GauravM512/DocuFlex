#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SOFFICE_BIN="${SOFFICE_BIN:-soffice}"
LO_ACCEPT="socket,host=localhost,port=8100;urp;"

if ! command -v "$SOFFICE_BIN" >/dev/null 2>&1; then
    echo "[ERROR] LibreOffice executable not found in PATH: $SOFFICE_BIN"
    echo "Set SOFFICE_BIN to the soffice binary if needed."
    exit 1
fi

echo "Starting LibreOffice headless server..."
"$SOFFICE_BIN" --headless --accept="$LO_ACCEPT" >/tmp/docuflex-lo.log 2>&1 &
LO_PID=$!

cleanup() {
    echo
    echo "Stopping LibreOffice (PID $LO_PID)..."
    kill "$LO_PID" 2>/dev/null || true
    wait "$LO_PID" 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT

if ! kill -0 "$LO_PID" 2>/dev/null; then
    echo "[ERROR] Failed to start LibreOffice server."
    exit 1
fi

echo "LibreOffice started with PID $LO_PID"
echo

echo "Starting DocuFlex..."
if [ -x ".venv/bin/python" ]; then
    ./.venv/bin/python -m uvicorn main:app --port 8000 --workers 2
else
    echo "Set Up Virtual Environment"
fi
