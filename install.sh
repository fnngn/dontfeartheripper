#!/usr/bin/env bash
set -euo pipefail

echo "Installing dontfeartheripper..."

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found."
    echo "Install uv first:"
    echo "https://docs.astral.sh/uv/"
    exit 1
fi

uv tool install . --force

echo
echo "Installation complete."
echo
echo "Available commands:"
echo "  dftr scan <path>"
echo "  dftr tui <path>"
echo "  dftr doctor <path>"
echo "  dftr fix <path>"
echo

if command -v dftr >/dev/null 2>&1; then
    echo "dftr successfully installed."
    echo
    dftr --help
fi
