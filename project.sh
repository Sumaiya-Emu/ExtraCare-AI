#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
exec python3 scripts/project.py "${1:-run}"
