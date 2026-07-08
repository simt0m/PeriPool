from app.extensions import db
from app.models import ItemUnit
from tests.conftest import login


def _login_admin(client, seeded_data):
    return login(client, seeded_data['admin_email'], 'AdminPass123!')


def test_admin_can_create_item_unit(app, client, seeded_data):
    """Test that an admin can create a new item unit."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-units/new',
        data={
            'item_model_id': seeded_data['item_model_id'],
            'asset_tag': 'PP-HS-NEW-001',
            'status': 'available',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item unit created successfully' in response.data

    with app.app_context():
        assert ItemUnit.query.filter_by(asset_tag='PP-HS-NEW-001').first() is not None


def test_admin_can_edit_item_unit(app, client, seeded_data):
    """Test that an admin can edit an existing item unit."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/item-units/{seeded_data["item_unit_id"]}/edit',
        data={
            'item_model_id': seeded_data['item_model_id'],
            'asset_tag': 'PP-HS-TEST-001-B',
            'status': 'maintenance',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item unit updated successfully' in response.data

    with app.app_context():
        item_unit = db.session.get(ItemUnit, seeded_data['item_unit_id'])
        assert item_unit.status == 'maintenance'


def test_admin_can_delete_item_unit_without_history(app, client, seeded_data):
    """Test that an admin can delete an item unit with no borrowing history."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/item-units/{seeded_data["item_unit_id"]}/delete',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item unit deleted successfully' in response.data

    with app.app_context():
        assert db.session.get(ItemUnit, seeded_data['item_unit_id']) is None


def test_duplicate_asset_tag_is_rejected(client, seeded_data):
    """Test that a duplicate asset tag shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-units/new',
        data={
            'item_model_id': seeded_data['item_model_id'],
            'asset_tag': seeded_data['item_unit_asset_tag'],
            'status': 'available',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'An item unit with that asset tag already exists' in response.data


def test_blank_asset_tag_is_rejected(client, seeded_data):
    """Test that a blank asset tag shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-units/new',
        data={
            'item_model_id': seeded_data['item_model_id'],
            'asset_tag': '',
            'status': 'available',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Asset tag is required' in response.data


def test_invalid_status_is_rejected(app, client, seeded_data):
    """Test that a status outside the allowed choices is rejected."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-units/new',
        data={
            'item_model_id': seeded_data['item_model_id'],
            'asset_tag': 'PP-HS-BOGUS-001',
            'status': 'bogus-status',
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    with app.app_context():
        assert ItemUnit.query.filter_by(asset_tag='PP-HS-BOGUS-001').first() is None
