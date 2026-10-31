#!/usr/bin/env bash
set -euo pipefail

echo "Installing dontfeartheripper..."

uv sync

echo
echo "Installation successful."
echo
echo "Run:"
echo "  uv run dftr scan <library>"
echo "  uv run dftr doctor <library>"
echo "  uv run dftr fix <library>"
