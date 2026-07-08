from datetime import timedelta

import pytest

from app import create_app
from app.extensions import db
from app.models import (
    BorrowRecord,
    Category,
    ItemModel,
    ItemUnit,
    User,
    get_utc_now,
)


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


@pytest.fixture()
def client(app):
    """Create a test client for making requests."""
    return app.test_client()


@pytest.fixture()
def seeded_data(app):
    """Create test users and inventory records."""
    with app.app_context():
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
            'item_model_id': item_model.id,
            'item_unit_id': item_unit.id,
        }


def login(client, email, password):
    """Log a user in during a test."""
    return client.post(
        '/login',
        data={
            'email': email,
            'password': password,
        },
        follow_redirects=True
    )