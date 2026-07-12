#!/bin/sh
set -eu

DB_PATH="${BACKEND_DB_PATH:-/app/backend/kip.db}"

if [ ! -s "$DB_PATH" ]; then
  echo "Bootstrapping demo database at $DB_PATH"
  python /app/scripts/reset_demo_db.py
fi

exec "$@"
