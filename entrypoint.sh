#!/bin/sh
set -e

if [ ! -f "instance/peripool.db" ]; then
    echo "No database found, seeding sample data..."
    python -m scripts.reseed_database
fi

exec gunicorn --bind 0.0.0.0:5000 --workers 2 run:app
