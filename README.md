# PeriPool

PeriPool is a company peripheral borrowing app that lets employees borrow shared office equipment such as mice, keyboards, headsets, webcams, and adapters.

The app helps employees who forgot essential equipment for an office day, and also lets users trial peripherals before requesting a permanent purchase through their cost center.

## Database Design

The application uses a relational SQLite database with SQLAlchemy models. The main entities are Users, Categories, Item Models, Item Units, Borrow Records, and Item Reviews.

The design separates item models from physical item units. This allows the system to represent multiple physical copies of the same model, such as 50 Dell wireless mice, while still tracking each borrowable unit individually.

Full database design documentation is available in:

[Database Design](docs/database_design.md)

## Running It Locally

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux

pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env` and set `SECRET_KEY`. A development fallback is used if you skip this, but don't rely on it outside local dev.

Seed the database with some sample data (creates an admin login, admin@peripool.com / AdminPass123!, and an employee login, alex.carter@peripool.com / EmployeePass123!):

```bash
python -m scripts.reseed_database
```

Then start the app:

```bash
python run.py
```

The site is served at http://127.0.0.1:5000.

## Running The Tests

```bash
pytest --cov=app --cov-report=term-missing
ruff check .
```
