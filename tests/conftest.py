import re
from datetime import date, timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import Category, ItemModel, ItemUnit, User


@pytest.fixture()
def app(tmp_path):
    """Create a test version of the Flask app.

    Uses a temporary SQLite database for each test run.
    """
    db_path = tmp_path / 'test_peripool.db'

    test_app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test_secret_key',
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path.as_posix()}',
        'WTF_CSRF_ENABLED': False,
    })

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    """Create a test client for making requests."""
    return app.test_client()


@pytest.fixture()
def csrf_app(tmp_path):
    """Create a test app with CSRF protection left enabled.

    Kept separate from the main app fixture, which disables CSRF for
    convenience everywhere else.
    """
    db_path = tmp_path / 'test_peripool_csrf.db'

    test_app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test_secret_key',
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path.as_posix()}',
    })

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def csrf_client(csrf_app):
    """Create a test client for the CSRF-enabled app."""
    return csrf_app.test_client()


def _create_seed_data():
    """Create test users and inventory records.

    Must be called inside an app context. Shared by the seeded_data and
    csrf_seeded_data fixtures so both app variants seed identically.
    """
    admin = User(
        name='Admin User',
        email='admin@example.com',
        is_admin=True,
        is_active=True
    )
    admin.set_password('AdminPass123!')

    employee = User(
        name='Employee User',
        email='employee@example.com',
        is_admin=False,
        is_active=True
    )
    employee.set_password('EmployeePass123!')

    category = Category(
        name='Headsets',
        description='Headsets for calls and meetings.'
    )

    item_model = ItemModel(
        category=category,
        manufacturer='Jabra',
        model_name='Evolve2 65',
        description='Wireless headset for office calls.',
        cost='149.99',
        is_active=True
    )

    item_unit = ItemUnit(
        item_model=item_model,
        asset_tag='PP-HS-TEST-001',
        status='available'
    )

    db.session.add_all([
        admin,
        employee,
        category,
        item_model,
        item_unit,
    ])
    db.session.commit()

    return {
        'admin_id': admin.id,
        'admin_email': admin.email,
        'employee_id': employee.id,
        'employee_email': employee.email,
        'category_id': category.id,
        'category_name': category.name,
        'item_model_id': item_model.id,
        'item_unit_id': item_unit.id,
        'item_unit_asset_tag': item_unit.asset_tag,
    }


@pytest.fixture()
def seeded_data(app):
    """Create test users and inventory records for the main app fixture."""
    with app.app_context():
        return _create_seed_data()


@pytest.fixture()
def csrf_seeded_data(csrf_app):
    """Create test users and inventory records for the CSRF-enabled app fixture."""
    with csrf_app.app_context():
        return _create_seed_data()


def get_csrf_token(client, url):
    """Extract the CSRF token from a GET response for the given URL.

    Returns an empty string if no token is present (e.g. when CSRF is
    disabled for the client's app), which login() below relies on.
    """
    response = client.get(url)
    match = re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', response.data)
    return match.group(1).decode() if match else ''


def future_due_date(days=3):
    """Return an ISO date string a few days from now, for borrow form data."""
    return (date.today() + timedelta(days=days)).isoformat()


def login(client, email, password):
    """Log a user in during a test."""
    return client.post(
        '/login',
        data={
            'email': email,
            'password': password,
            'csrf_token': get_csrf_token(client, '/login'),
        },
        follow_redirects=True
    )
