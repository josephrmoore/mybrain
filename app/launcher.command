#!/bin/bash
# Core Shell launcher. Double-click this file to start the app.
# Leaves this terminal window open showing server logs (by design).

set -e

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "First run — setting up environment (this only happens once)..."
    python3 -m venv venv
fi

source venv/bin/activate

DEPS="flask pyyaml keyring anthropic requests watchdog"
DEPS_HASH=$(echo "$DEPS" | shasum | cut -d' ' -f1)
DEPS_MARKER="venv/.deps_installed"

NEED_INSTALL=true
if [ -f "$DEPS_MARKER" ] && [ "$(cat "$DEPS_MARKER")" = "$DEPS_HASH" ]; then
    if python3 -c "import flask, yaml, keyring, anthropic, requests, watchdog" 2>/dev/null; then
        NEED_INSTALL=false
    else
        echo "Dependency marker looked current, but a package isn't actually importable — reinstalling."
    fi
fi

if [ "$NEED_INSTALL" = true ]; then
    echo "Checking dependencies..."
    if ! pip install --quiet $DEPS; then
        echo ""
        echo "ERROR: dependency install failed. Check your internet connection and try again."
        echo "Press any key to close this window."
        read -n 1
        exit 1
    fi
    echo "$DEPS_HASH" > "$DEPS_MARKER"
else
    echo "Dependencies already verified — skipping check."
fi

echo "Starting Core Shell..."

EXISTING_PID=$(lsof -ti:5151 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
    echo "A previous instance is still running on port 5151 — stopping it first."
    kill $EXISTING_PID
    sleep 1
fi

python3 app.py &
SERVER_PID=$!

sleep 1
open http://127.0.0.1:5151

echo ""
echo "Core Shell is running. Logs will appear below."
echo "Close this window to stop the server."
echo ""

wait $SERVER_PID
