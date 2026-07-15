from app.extensions import db
from app.models import User
from tests.conftest import login


def _login_admin(client, seeded_data):
    return login(client, seeded_data['admin_email'], 'AdminPass123!')


def test_admin_can_suspend_and_reactivate_user(app, client, seeded_data):
    """Test that an admin can suspend a user, then reactivate them."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/users/{seeded_data["employee_id"]}/toggle-active',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'User account suspended successfully' in response.data

    with app.app_context():
        assert db.session.get(User, seeded_data['employee_id']).is_active is False

    response = client.post(
        f'/admin/users/{seeded_data["employee_id"]}/toggle-active',
        follow_redirects=True
    )

    assert b'User account reactivated successfully' in response.data

    with app.app_context():
        assert db.session.get(User, seeded_data['employee_id']).is_active is True


def test_admin_cannot_suspend_self(app, client, seeded_data):
    """Test that an admin cannot change their own active status."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/users/{seeded_data["admin_id"]}/toggle-active',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'You cannot change your own active status' in response.data

    with app.app_context():
        assert db.session.get(User, seeded_data['admin_id']).is_active is True


def test_admin_can_grant_admin_status_to_user(app, client, seeded_data):
    """Test that an admin can promote a regular user to admin."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/users/{seeded_data["employee_id"]}/toggle-admin',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Granted admin access' in response.data

    with app.app_context():
        assert db.session.get(User, seeded_data['employee_id']).is_admin is True


def test_admin_can_revoke_admin_status_from_another_admin(app, client, seeded_data):
    """Test that an admin can revoke admin status from a different admin."""
    with app.app_context():
        other_admin = User(name='Second Admin', email='second.admin@example.com', is_admin=True)
        other_admin.set_password('AdminPass123!')
        db.session.add(other_admin)
        db.session.commit()
        other_admin_id = other_admin.id

    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/users/{other_admin_id}/toggle-admin',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Revoked admin access' in response.data

    with app.app_context():
        assert db.session.get(User, other_admin_id).is_admin is False


def test_admin_cannot_suspend_another_active_admin(app, client, seeded_data):
    """Test that an active admin cannot be suspended without first removing admin access."""
    with app.app_context():
        other_admin = User(name='Second Admin', email='second.admin@example.com', is_admin=True)
        other_admin.set_password('AdminPass123!')
        db.session.add(other_admin)
        db.session.commit()
        other_admin_id = other_admin.id

    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/users/{other_admin_id}/toggle-active',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Remove admin access before suspending this user' in response.data

    with app.app_context():
        assert db.session.get(User, other_admin_id).is_active is True


def test_admin_can_suspend_after_removing_admin_access(app, client, seeded_data):
    """Test that suspension becomes possible once admin access is removed first."""
    with app.app_context():
        other_admin = User(name='Second Admin', email='second.admin@example.com', is_admin=True)
        other_admin.set_password('AdminPass123!')
        db.session.add(other_admin)
        db.session.commit()
        other_admin_id = other_admin.id

    _login_admin(client, seeded_data)

    client.post(f'/admin/users/{other_admin_id}/toggle-admin', follow_redirects=True)

    response = client.post(
        f'/admin/users/{other_admin_id}/toggle-active',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'User account suspended successfully' in response.data

    with app.app_context():
        user = db.session.get(User, other_admin_id)
        assert user.is_admin is False
        assert user.is_active is False


def test_admin_cannot_change_own_admin_status(app, client, seeded_data):
    """Test that an admin cannot revoke their own admin status."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/users/{seeded_data["admin_id"]}/toggle-admin',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'You cannot change your own admin status' in response.data

    with app.app_context():
        assert db.session.get(User, seeded_data['admin_id']).is_admin is True
