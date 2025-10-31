#!/usr/bin/env bash
set -e

python -m syncmaster.server.scripts.manage_superusers add
python -m syncmaster.server.scripts.manage_superusers list

# exec is required to forward all signals to the main process
exec python -m syncmaster.server --host 0.0.0.0 --port 8000 "$@"
