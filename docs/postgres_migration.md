# Future scalability: migrating from SQLite to PostgreSQL

This is a discussion document, not a change log — PeriPool runs on SQLite
today and that isn't changing. SQLite is a reasonable choice for a small
demo app: zero setup, the whole database is one file, and it comfortably
handles the read/write volume a handful of users generate. This document
sets out why a real multi-team deployment would eventually outgrow it, and
what the migration would actually involve, since SQLAlchemy is deliberately
used as an abstraction layer that makes this a config change rather than a
rewrite.

## Why SQLite is the current constraint

- **No concurrent writers.** SQLite locks the entire database file for a
  write, so it degrades under concurrent traffic — fine for a classroom
  demo, not for a company-wide rollout.
- **No persistent disk on Render's free tier.** The container filesystem is
  rebuilt on every deploy, so `entrypoint.sh` has to reseed the database
  from scratch each time (see `docs/architecture.md`). A managed Postgres
  instance persists independently of the app container.
- **No built-in replication or backups.** A managed Postgres add-on (Render,
  RDS, etc.) provides automated backups and point-in-time recovery for free;
  SQLite has neither.

## Why the switch is cheap

The app never talks to SQLite directly — every query goes through
SQLAlchemy's ORM (`app/models.py`), and the connection string is the single
environment-driven setting in `config.py`:

```python
app.config.setdefault(
    'SQLALCHEMY_DATABASE_URI',
    'sqlite:///' + os.path.join(app.instance_path, 'peripool.db')
)
```

Switching engines is:

1. Add a Postgres driver to `requirements.txt` (`psycopg[binary]`).
2. Set `SQLALCHEMY_DATABASE_URI` to a Postgres URL instead of a SQLite path,
   e.g. `postgresql+psycopg://user:password@host:5432/peripool` — typically
   supplied by the hosting platform as an environment variable, so no code
   change is needed, only a deployment setting.
3. Run `db.create_all()` once against the new database (or introduce
   Flask-Migrate/Alembic for versioned schema changes, which is the
   recommended next step once a project has multiple environments to keep
   in sync).

No model, route, or form code changes, because none of it references SQLite
directly — this is the practical benefit of using an ORM rather than raw
SQL: the application logic is portable across database engines by
construction, not by extra effort.

## What would need attention

- **`Numeric` precision.** `ItemModel.cost` is `db.Numeric(10, 2)` —
  SQLite stores this loosely as text/real under the hood, while Postgres
  enforces it properly. Existing data would need a one-time validation pass
  after migrating.
- **Case sensitivity.** SQLite's `LIKE`/`lower()` comparisons (used in the
  uniqueness checks in `app/forms.py`, e.g. `validate_model_name`) behave
  slightly differently from Postgres's default collation — worth a quick
  regression pass against the existing test suite after switching, since the
  tests already exercise every uniqueness rule.
- **Connection pooling.** SQLite has no concept of a connection pool since
  it's a local file; Postgres benefits from `SQLALCHEMY_ENGINE_OPTIONS`
  tuning (`pool_size`, `pool_recycle`) once traffic is non-trivial.

## Conclusion

The database is not a rewrite risk — it's a configuration decision deferred
until it's actually needed. That's the practical argument for using an ORM
from the start rather than hand-written SQL: the "future scalability" story
is a one-file config change plus a driver, not a migration project.
