from app.models import User
from tests.conftest import login


def test_user_can_register(app, client):
    """Test that a new user can register."""
    response = client.post(
        '/register',
        data={
            'name': 'New User',
            'email': 'new.user@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Account created successfully' in response.data

    with app.app_context():
        user = User.query.filter_by(email='new.user@example.com').first()
        assert user is not None
        assert user.password_hash != 'Password123!'


def test_user_can_login(client, seeded_data):
    """Test that an existing user can log in."""
    response = login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    assert response.status_code == 200
    assert b'You have been logged in' in response.data
    assert b'Your dashboard' in response.data


def test_invalid_login_is_rejected(client, seeded_data):
    """Test that an invalid password is rejected."""
    response = login(
        client,
        seeded_data['employee_email'],
        'WrongPassword123!'
    )

    assert response.status_code == 200
    assert b'Invalid email or password' in response.data


def test_admin_route_blocks_regular_user(client, seeded_data):
    """Test that a regular user cannot access the admin dashboard."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    response = client.get('/admin')

    assert response.status_code == 403
    assert b'Access denied' in response.data


def test_registration_rejects_name_with_digits(client):
    """Test that a name containing digits is rejected."""
    response = client.post(
        '/register',
        data={
            'name': 'User123',
            'email': 'digits@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Name cannot contain numbers or symbols' in response.data


def test_registration_rejects_name_with_symbols(client):
    """Test that a name containing symbols is rejected."""
    response = client.post(
        '/register',
        data={
            'name': 'User@Name',
            'email': 'symbols@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Name cannot contain numbers or symbols' in response.data


def test_registration_accepts_accented_name(app, client):
    """Test that an accented international name is accepted, not rejected."""
    response = client.post(
        '/register',
        data={
            'name': 'José François',
            'email': 'jose@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Account created successfully' in response.data

    with app.app_context():
        assert User.query.filter_by(email='jose@example.com').first() is not None


def test_registration_rejects_short_name(client):
    """Test that a single-character name is rejected."""
    response = client.post(
        '/register',
        data={
            'name': 'A',
            'email': 'short@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Account created successfully' not in response.data


def test_catalogue_requires_login(client):
    """Test that the catalogue is not accessible to anonymous visitors."""
    response = client.get('/catalogue')

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_catalogue_accessible_when_logged_in(client, seeded_data):
    """Test that a logged-in user can view the catalogue."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    response = client.get('/catalogue')

    assert response.status_code == 200
    assert b'Peripheral Catalogue' in response.data