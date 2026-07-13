#!/bin/sh
set -eu

alembic upgrade head

if [ "${KIP_SEED_DEMO:-0}" = "1" ]; then
  python /app/scripts/seed_phase2_data.py
fi

exec "$@"
