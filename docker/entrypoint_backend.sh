#!/usr/bin/env bash
set -e

python -m syncmaster.db.migrations upgrade head

if [[ "x${SYNCMASTER__ENTRYPOINT__SUPERUSERS}" != "x" ]]; then
  superusers=$(echo "${SYNCMASTER__ENTRYPOINT__SUPERUSERS}" | tr "," " ")
  python -m syncmaster.backend.scripts.manage_superusers add ${superusers}
  python -m syncmaster.backend.scripts.manage_superusers list
fi

# exec is required to forward all signals to the main process
exec python -m syncmaster.backend --host 0.0.0.0 --port 8000 "$@"
