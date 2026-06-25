#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed or not in PATH." >&2
  exit 1
fi

if [ ! -f requirements.txt ]; then
  echo "Error: requirements.txt not found in $PROJECT_DIR" >&2
  exit 1
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Starting Stream Deck controller..."
python3 main.py
