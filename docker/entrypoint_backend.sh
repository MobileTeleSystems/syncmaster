#!/usr/bin/env bash
set -e

python -m syncmaster.db.migrations upgrade head

# exec is required to forward all signals to the main process
exec python -m syncmaster.backend --host 0.0.0.0 --port 8000 "$@"
