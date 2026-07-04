from app.models import User
from tests.conftest import login


def test_user_can_register(app, client):
    """Test that a new user can register."""
    response = client.post(
        '/register',
        data={
            'name': 'New User',
            'email': 'new.user@test.local',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Account created successfully' in response.data

    with app.app_context():
        user = User.query.filter_by(email='new.user@test.local').first()
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