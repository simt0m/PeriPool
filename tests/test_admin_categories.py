from app.extensions import db
from app.models import Category
from tests.conftest import login


def _login_admin(client, seeded_data):
    return login(client, seeded_data['admin_email'], 'AdminPass123!')


def test_admin_can_create_category(app, client, seeded_data):
    """Test that an admin can create a new category."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/categories/new',
        data={'name': 'Cables', 'description': 'Various cables.'},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Category created successfully' in response.data

    with app.app_context():
        assert Category.query.filter_by(name='Cables').first() is not None


def test_admin_can_edit_category(app, client, seeded_data):
    """Test that an admin can edit an existing category."""
    _login_admin(client, seeded_data)

    response = client.post(
        f'/admin/categories/{seeded_data["category_id"]}/edit',
        data={'name': 'Updated Headsets', 'description': 'Updated description.'},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Category updated successfully' in response.data

    with app.app_context():
        category = db.session.get(Category, seeded_data['category_id'])
        assert category.name == 'Updated Headsets'


def test_duplicate_category_name_is_rejected(client, seeded_data):
    """Test that creating a category with a duplicate name shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/categories/new',
        data={'name': seeded_data['category_name'], 'description': ''},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'A category with that name already exists' in response.data


def test_blank_category_name_is_rejected(client, seeded_data):
    """Test that a blank category name shows a validation error."""
    _login_admin(client, seeded_data)

    response = client.post(
        '/admin/categories/new',
        data={'name': '', 'description': 'x'},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Category name is required' in response.data
