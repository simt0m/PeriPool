from datetime import datetime, time, timedelta, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..forms import MAX_ACTIVE_BORROWS_PER_USER, MAX_BORROW_DAYS, BorrowForm, ReviewForm
from ..models import BorrowRecord, ItemModel, ItemReview, ItemUnit, get_utc_now

catalogue = Blueprint('catalogue', __name__)

@catalogue.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@catalogue.route('/catalogue')
@login_required
def catalogue_view():
    """Render the item model catalogue."""
    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    today = get_utc_now().date()

    return render_template(
        'catalogue.html',
        item_models=item_models,
        min_due_date=today.isoformat(),
        max_due_date=(today + timedelta(days=MAX_BORROW_DAYS)).isoformat()
    )

@catalogue.route('/borrow/<int:item_model_id>', methods=['POST'])
@login_required
def borrow_item(item_model_id):
    """Borrow one available unit for the selected item model."""
    item_model = ItemModel.query.filter_by(
        id=item_model_id,
        is_active=True
    ).first_or_404()

    form = BorrowForm()

    if not form.validate_on_submit():
        for error in form.due_date.errors:
            flash(error, 'danger')
        return redirect(url_for('catalogue.catalogue_view'))

    active_borrow_count = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).count()

    if active_borrow_count >= MAX_ACTIVE_BORROWS_PER_USER:
        flash(
            f'You already have {MAX_ACTIVE_BORROWS_PER_USER} items on loan. '
            'Return one before borrowing another.',
            'warning'
        )
        return redirect(url_for('catalogue.catalogue_view'))

    existing_borrow = (
        BorrowRecord.query
        .join(ItemUnit)
        .filter(
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.status == 'active',
            ItemUnit.item_model_id == item_model.id
        )
        .first()
    )

    if existing_borrow:
        flash('You already have this model on loan.', 'warning')
        return redirect(url_for('catalogue.catalogue_view'))

    available_unit = (
        ItemUnit.query
        .filter_by(item_model_id=item_model.id, status='available')
        .order_by(ItemUnit.asset_tag)
        .first()
    )

    if available_unit is None:
        flash('No units are currently available for this model.', 'warning')
        return redirect(url_for('catalogue.catalogue_view'))

    available_unit.status = 'borrowed'

    due_at = datetime.combine(form.due_date.data, time(23, 59, 59), tzinfo=timezone.utc)

    borrow_record = BorrowRecord(
        user_id=current_user.id,
        item_unit_id=available_unit.id,
        due_at=due_at,
        status='active'
    )

    db.session.add(borrow_record)
    db.session.commit()

    current_app.logger.info(
        f'{current_user.email} borrowed unit {available_unit.asset_tag} '
        f'({item_model.manufacturer} {item_model.model_name})'
    )

    flash(
        f'You have borrowed {item_model.manufacturer} {item_model.model_name}.',
        'success'
    )

    return redirect(url_for('catalogue.dashboard'))

@catalogue.route('/return/<int:borrow_record_id>', methods=['POST'])
@login_required
def return_item(borrow_record_id):
    """Return an active borrowed item."""
    borrow_record = BorrowRecord.query.filter_by(
        id=borrow_record_id,
        user_id=current_user.id,
        status='active'
    ).first_or_404()

    borrow_record.status = 'returned'
    borrow_record.returned_at = get_utc_now()
    borrow_record.item_unit.status = 'available'

    db.session.commit()

    current_app.logger.info(f'{current_user.email} returned unit {borrow_record.item_unit.asset_tag}')

    flash('Item returned successfully.', 'success')
    return redirect(url_for('catalogue.dashboard'))

@catalogue.route('/dashboard')
@login_required
def dashboard():
    """Render the user dashboard."""
    active_borrow_records = (
        BorrowRecord.query
        .filter_by(user_id=current_user.id, status='active')
        .order_by(BorrowRecord.due_at)
        .all()
    )

    previous_borrow_records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.status != 'active'
        )
        .order_by(BorrowRecord.borrowed_at.desc())
        .all()
    )

    return render_template(
        'dashboard.html',
        active_borrow_records=active_borrow_records,
        previous_borrow_records=previous_borrow_records
    )

@catalogue.route('/catalogue/<int:item_model_id>/review', methods=['GET', 'POST'])
@login_required
def review_item(item_model_id):
    """Leave or update a review for a previously borrowed item model."""
    item_model = db.get_or_404(ItemModel, item_model_id)

    has_borrowed = (
        BorrowRecord.query
        .join(ItemUnit)
        .filter(
            BorrowRecord.user_id == current_user.id,
            ItemUnit.item_model_id == item_model.id
        )
        .first()
    )

    if not has_borrowed:
        flash('You can only review items you have borrowed.', 'warning')
        return redirect(url_for('catalogue.dashboard'))

    review = ItemReview.query.filter_by(user_id=current_user.id, item_model_id=item_model.id).first()
    form = ReviewForm(obj=review)

    if form.validate_on_submit():
        if review is None:
            review = ItemReview(user_id=current_user.id, item_model_id=item_model.id)
            db.session.add(review)

        form.populate_obj(review)
        db.session.commit()

        current_app.logger.info(
            f'{current_user.email} reviewed item model: '
            f'{item_model.manufacturer} {item_model.model_name} ({review.rating}/5)'
        )

        flash('Thank you for your review!', 'success')
        return redirect(url_for('catalogue.dashboard'))

    return render_template('review_form.html', form=form, item_model=item_model)
