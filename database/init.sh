#!/bin/bash
# database/init.sh
# Ensures migrations run in the correct order

set -e

# Run SQL files in numerical order
for file in /docker-entrypoint-initdb.d/*.sql; do
    echo "Running migration: $file"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$file"
done