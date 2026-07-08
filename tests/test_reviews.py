from app.models import ItemReview
from tests.conftest import login


def test_user_can_review_borrowed_item(app, client, seeded_data):
    """Test that a user can leave a review for an item they have borrowed."""
    login(client, seeded_data['employee_email'], 'EmployeePass123!')
    client.post(f'/borrow/{seeded_data["item_model_id"]}', follow_redirects=True)

    response = client.post(
        f'/catalogue/{seeded_data["item_model_id"]}/review',
        data={'rating': '5', 'comment': 'Great item.'},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'Thank you for your review' in response.data

    with app.app_context():
        review = ItemReview.query.filter_by(
            user_id=seeded_data['employee_id'],
            item_model_id=seeded_data['item_model_id']
        ).first()

        assert review is not None
        assert review.rating == 5


def test_resubmitting_a_review_updates_it(app, client, seeded_data):
    """Test that submitting a second review for the same item updates it, not duplicates it."""
    login(client, seeded_data['employee_email'], 'EmployeePass123!')
    client.post(f'/borrow/{seeded_data["item_model_id"]}', follow_redirects=True)

    client.post(
        f'/catalogue/{seeded_data["item_model_id"]}/review',
        data={'rating': '3', 'comment': 'It was OK.'},
        follow_redirects=True
    )

    client.post(
        f'/catalogue/{seeded_data["item_model_id"]}/review',
        data={'rating': '5', 'comment': 'Actually great.'},
        follow_redirects=True
    )

    with app.app_context():
        reviews = ItemReview.query.filter_by(
            user_id=seeded_data['employee_id'],
            item_model_id=seeded_data['item_model_id']
        ).all()

        assert len(reviews) == 1
        assert reviews[0].rating == 5


def test_review_blocked_without_prior_borrow(client, seeded_data):
    """Test that a user cannot review an item they have never borrowed."""
    login(client, seeded_data['employee_email'], 'EmployeePass123!')

    response = client.post(
        f'/catalogue/{seeded_data["item_model_id"]}/review',
        data={'rating': '5', 'comment': 'Never had this.'},
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b'You can only review items you have borrowed' in response.data


def test_out_of_range_rating_is_rejected(app, client, seeded_data):
    """Test that a rating outside 1-5 is rejected by the form."""
    login(client, seeded_data['employee_email'], 'EmployeePass123!')
    client.post(f'/borrow/{seeded_data["item_model_id"]}', follow_redirects=True)

    client.post(
        f'/catalogue/{seeded_data["item_model_id"]}/review',
        data={'rating': '9', 'comment': 'Out of range.'},
        follow_redirects=True
    )

    with app.app_context():
        review = ItemReview.query.filter_by(
            user_id=seeded_data['employee_id'],
            item_model_id=seeded_data['item_model_id']
        ).first()

        assert review is None
