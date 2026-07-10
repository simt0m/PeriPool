#!/bin/sh
set -e

if ! python -c "
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    assert User.query.first() is not None
" 2>/dev/null; then
    echo "Database not ready, seeding sample data..."
    python -m scripts.reseed_database
fi

exec gunicorn --bind 0.0.0.0:5000 --workers 2 run:app
