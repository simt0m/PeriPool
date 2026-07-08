from decimal import Decimal

from app.extensions import db
from app.models import ItemModel
from tests.conftest import login


def _login_admin(client, seeded_data):
    return login(client, seeded_data['admin_email'], 'AdminPass123!')


def test_admin_can_create_item_model(app, client, seeded_data):
    """Test that an admin can create a new item model."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-models/new',
        data={
            'category_id': seeded_data['category_id'],
            'manufacturer': 'Logitech',
            'model_name': 'MX Keys',
            'description': 'Wireless keyboard.',
            'cost': '99.99',
            'image_url': '',
            'is_active': 'y',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item model created successfully' in response.data

    with app.app_context():
        item_model = ItemModel.query.filter_by(manufacturer='Logitech', model_name='MX Keys').first()
        assert item_model is not None
        assert item_model.cost == Decimal('99.99')


def test_admin_can_edit_item_model(app, client, seeded_data):
    """Test that an admin can edit an existing item model."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/item-models/{seeded_data["item_model_id"]}/edit',
        data={
            'category_id': seeded_data['category_id'],
            'manufacturer': 'Jabra',
            'model_name': 'Evolve2 75',
            'description': 'Updated.',
            'cost': '159.99',
            'image_url': '',
            'is_active': 'y',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item model updated successfully' in response.data

    with app.app_context():
        item_model = db.session.get(ItemModel, seeded_data['item_model_id'])
        assert item_model.model_name == 'Evolve2 75'


def test_admin_can_deactivate_item_model(app, client, seeded_data):
    """Test that an admin can deactivate an item model."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/item-models/{seeded_data["item_model_id"]}/deactivate',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item model deactivated successfully' in response.data

    with app.app_context():
        item_model = db.session.get(ItemModel, seeded_data['item_model_id'])
        assert item_model.is_active is False


def test_duplicate_manufacturer_model_pair_is_rejected(client, seeded_data):
    """Test that a duplicate manufacturer and model name pair shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-models/new',
        data={
            'category_id': seeded_data['category_id'],
            'manufacturer': 'Jabra',
            'model_name': 'Evolve2 65',
            'description': '',
            'cost': '',
            'image_url': '',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'That manufacturer and model name already exists' in response.data


def test_negative_cost_is_rejected(client, seeded_data):
    """Test that a negative cost shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-models/new',
        data={
            'category_id': seeded_data['category_id'],
            'manufacturer': 'Acme',
            'model_name': 'Widget',
            'description': '',
            'cost': '-5',
            'image_url': '',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Cost cannot be negative' in response.data


def test_missing_required_fields_are_rejected(client, seeded_data):
    """Test that a missing manufacturer or model name shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/item-models/new',
        data={
            'category_id': seeded_data['category_id'],
            'manufacturer': '',
            'model_name': '',
            'description': '',
            'cost': '',
            'image_url': '',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Manufacturer and model name are required' in response.data
