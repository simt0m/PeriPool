from datetime import date, timedelta

from app.extensions import db
from app.forms import MAX_ACTIVE_BORROWS_PER_USER, MAX_BORROW_DAYS
from app.models import BorrowRecord, Category, ItemModel, ItemUnit
from tests.conftest import future_due_date, login


def test_user_can_borrow_available_item(app, client, seeded_data):
    """Test that a user can borrow an available item model."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    response = client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': future_due_date()},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'You have borrowed' in response.data

    with app.app_context():
        item_unit = db.session.get(ItemUnit, seeded_data['item_unit_id'])
        borrow_record = BorrowRecord.query.filter_by(
            user_id=seeded_data['employee_id'],
            item_unit_id=seeded_data['item_unit_id'],
            status='active'
        ).first()

        assert item_unit.status == 'borrowed'
        assert borrow_record is not None
        assert borrow_record.due_at.date() == date.fromisoformat(future_due_date())


def test_borrow_rejects_past_due_date(app, client, seeded_data):
    """Test that a due date in the past is rejected."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    past_date = (date.today() - timedelta(days=1)).isoformat()

    response = client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': past_date},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Return date cannot be in the past' in response.data

    with app.app_context():
        borrow_record = BorrowRecord.query.filter_by(
            user_id=seeded_data['employee_id'],
            status='active'
        ).first()

        assert borrow_record is None


def test_borrow_rejects_due_date_too_far_ahead(app, client, seeded_data):
    """Test that a due date beyond the allowed window is rejected."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    far_future_date = (date.today() + timedelta(days=MAX_BORROW_DAYS + 1)).isoformat()

    response = client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': far_future_date},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'cannot be more than' in response.data

    with app.app_context():
        borrow_record = BorrowRecord.query.filter_by(
            user_id=seeded_data['employee_id'],
            status='active'
        ).first()

        assert borrow_record is None


def test_due_date_is_always_after_borrowed_at(app, client, seeded_data):
    """Test that the return date is always after the borrow start date.

    Guaranteed by construction (due_date can't be in the past, and due_at is
    set to the end of that day), but asserted explicitly as its own rule.
    """
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': future_due_date(days=0)},
        follow_redirects=True
    )

    with app.app_context():
        borrow_record = BorrowRecord.query.filter_by(
            user_id=seeded_data['employee_id'],
            status='active'
        ).first()

        assert borrow_record is not None
        assert borrow_record.due_at > borrow_record.borrowed_at


def test_borrow_blocked_after_reaching_active_limit(app, client, seeded_data):
    """Test that a user cannot exceed the maximum number of active borrows."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    with app.app_context():
        category = db.session.get(Category, seeded_data['category_id'])
        extra_item_model_ids = []

        for i in range(MAX_ACTIVE_BORROWS_PER_USER):
            item_model = ItemModel(
                category=category,
                manufacturer='TestBrand',
                model_name=f'Limit Test Model {i}',
                is_active=True
            )
            db.session.add(item_model)
            db.session.flush()

            db.session.add(ItemUnit(
                item_model=item_model,
                asset_tag=f'PP-LIMIT-{i}',
                status='available'
            ))
            db.session.commit()

            extra_item_model_ids.append(item_model.id)

    for item_model_id in extra_item_model_ids:
        client.post(
            f'/borrow/{item_model_id}',
            data={'due_date': future_due_date()},
            follow_redirects=True
        )

    response = client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': future_due_date()},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert f'You already have {MAX_ACTIVE_BORROWS_PER_USER} items on loan'.encode() in response.data

    with app.app_context():
        active_count = BorrowRecord.query.filter_by(
            user_id=seeded_data['employee_id'],
            status='active'
        ).count()

        assert active_count == MAX_ACTIVE_BORROWS_PER_USER


def test_duplicate_active_borrow_is_blocked(app, client, seeded_data):
    """Test that a user cannot borrow the same model twice."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': future_due_date()},
        follow_redirects=True
    )

    response = client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': future_due_date()},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'You already have this model on loan' in response.data

    with app.app_context():
        active_records = (
            BorrowRecord.query
            .join(ItemUnit)
            .filter(
                BorrowRecord.user_id == seeded_data['employee_id'],
                BorrowRecord.status == 'active',
                ItemUnit.item_model_id == seeded_data['item_model_id']
            )
            .all()
        )

        assert len(active_records) == 1


def test_user_can_return_borrowed_item(app, client, seeded_data):
    """Test that a user can return a borrowed item."""
    login(
        client,
        seeded_data['employee_email'],
        'EmployeePass123!'
    )

    client.post(
        f'/borrow/{seeded_data["item_model_id"]}',
        data={'due_date': future_due_date()},
        follow_redirects=True
    )

    with app.app_context():
        borrow_record = BorrowRecord.query.filter_by(
            user_id=seeded_data['employee_id'],
            status='active'
        ).first()

        borrow_record_id = borrow_record.id

    response = client.post(
        f'/return/{borrow_record_id}',
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Item returned successfully' in response.data

    with app.app_context():
        borrow_record = db.session.get(BorrowRecord, borrow_record_id)
        item_unit = db.session.get(ItemUnit, seeded_data['item_unit_id'])

        assert borrow_record.status == 'returned'
        assert borrow_record.returned_at is not None
        assert item_unit.status == 'available'