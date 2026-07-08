from flask import Blueprint, current_app, flash, redirect, render_template, url_for
from flask_login import current_user

from ..decorators import admin_required
from ..extensions import db
from ..forms import CategoryForm, ItemModelForm, ItemUnitForm
from ..models import BorrowRecord, Category, ItemModel, ItemUnit, User, get_utc_now

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('')
@admin_required
def dashboard():
    """Render the administrator dashboard."""
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()

    total_categories = Category.query.count()
    total_item_models = ItemModel.query.count()
    active_item_models = ItemModel.query.filter_by(is_active=True).count()

    total_item_units = ItemUnit.query.count()
    available_item_units = ItemUnit.query.filter_by(status='available').count()
    borrowed_item_units = ItemUnit.query.filter_by(status='borrowed').count()
    maintenance_item_units = ItemUnit.query.filter_by(status='maintenance').count()

    active_borrow_records = BorrowRecord.query.filter_by(status='active').count()

    overdue_borrow_records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status == 'active',
            BorrowRecord.returned_at.is_(None),
            BorrowRecord.due_at < get_utc_now()
        )
        .count()
    )

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        active_users=active_users,
        total_categories=total_categories,
        total_item_models=total_item_models,
        active_item_models=active_item_models,
        total_item_units=total_item_units,
        available_item_units=available_item_units,
        borrowed_item_units=borrowed_item_units,
        maintenance_item_units=maintenance_item_units,
        active_borrow_records=active_borrow_records,
        overdue_borrow_records=overdue_borrow_records,
    )

@admin.route('/users')
@admin_required
def users():
    """Render a read-only list of users."""
    all_users = User.query.order_by(User.name).all()

    return render_template(
        'admin_users.html',
        users=all_users
    )

@admin.route('/inventory')
@admin_required
def inventory():
    """Render a read-only view of catalogue and item units."""
    categories = Category.query.order_by(Category.name).all()

    item_models = (
        ItemModel.query
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    item_units = (
        ItemUnit.query
        .join(ItemModel)
        .order_by(ItemModel.manufacturer, ItemModel.model_name, ItemUnit.asset_tag)
        .all()
    )

    return render_template(
        'admin_inventory.html',
        categories=categories,
        item_models=item_models,
        item_units=item_units
    )

@admin.route('/categories/new', methods=['GET', 'POST'])
@admin.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def category_form(category_id=None):
    """Create a new category, or edit an existing one."""
    category = Category.query.get_or_404(category_id) if category_id else None
    form = CategoryForm(obj=category, category_id=category_id)

    if form.validate_on_submit():
        if category is None:
            category = Category()
            db.session.add(category)

        form.populate_obj(category)
        db.session.commit()

        action = 'updated' if category_id else 'created'
        current_app.logger.info(f'{current_user.email} {action} category: {category.name}')

        flash(f'Category {action} successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template('admin_category_form.html', form=form, category=category)

@admin.route('/item-models/new', methods=['GET', 'POST'])
@admin.route('/item-models/<int:item_model_id>/edit', methods=['GET', 'POST'])
@admin_required
def item_model_form(item_model_id=None):
    """Create a new item model, or edit an existing one."""
    item_model = ItemModel.query.get_or_404(item_model_id) if item_model_id else None
    categories = Category.query.order_by(Category.name).all()

    if not categories:
        flash('Create a category before adding an item model.', 'warning')
        return redirect(url_for('admin.inventory'))

    form = ItemModelForm(obj=item_model, item_model_id=item_model_id)
    form.category_id.choices = [(category.id, category.name) for category in categories]

    if form.validate_on_submit():
        if item_model is None:
            item_model = ItemModel()
            db.session.add(item_model)

        form.populate_obj(item_model)
        db.session.commit()

        action = 'updated' if item_model_id else 'created'
        current_app.logger.info(
            f'{current_user.email} {action} item model: {item_model.manufacturer} {item_model.model_name}'
        )

        flash(f'Item model {action} successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template('admin_item_model_form.html', form=form, item_model=item_model)

@admin.route('/item-models/<int:item_model_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_item_model(item_model_id):
    """Deactivate an item model."""
    item_model = ItemModel.query.get_or_404(item_model_id)

    item_model.is_active = False

    db.session.commit()

    current_app.logger.info(
        f'{current_user.email} deactivated item model: {item_model.manufacturer} {item_model.model_name}'
    )

    flash('Item model deactivated successfully.', 'success')
    return redirect(url_for('admin.inventory'))

@admin.route('/item-units/new', methods=['GET', 'POST'])
@admin.route('/item-units/<int:item_unit_id>/edit', methods=['GET', 'POST'])
@admin_required
def item_unit_form(item_unit_id=None):
    """Create a new item unit, or edit an existing one."""
    item_unit = ItemUnit.query.get_or_404(item_unit_id) if item_unit_id else None

    if item_unit and item_unit.status == 'borrowed':
        flash('Borrowed item units must be returned before they can be edited.', 'warning')
        return redirect(url_for('admin.inventory'))

    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    if not item_models:
        flash('Create an active item model before adding an item unit.', 'warning')
        return redirect(url_for('admin.inventory'))

    form = ItemUnitForm(obj=item_unit, item_unit_id=item_unit_id)
    form.item_model_id.choices = [
        (model.id, f'{model.manufacturer} {model.model_name}') for model in item_models
    ]

    if form.validate_on_submit():
        if item_unit is None:
            item_unit = ItemUnit()
            db.session.add(item_unit)

        form.populate_obj(item_unit)
        db.session.commit()

        action = 'updated' if item_unit_id else 'created'
        current_app.logger.info(f'{current_user.email} {action} item unit: {item_unit.asset_tag}')

        flash(f'Item unit {action} successfully.', 'success')
        return redirect(url_for('admin.inventory'))

    return render_template('admin_item_unit_form.html', form=form, item_unit=item_unit)

@admin.route('/item-units/<int:item_unit_id>/delete', methods=['POST'])
@admin_required
def delete_item_unit(item_unit_id):
    """Delete an item unit if it has no borrowing history."""
    item_unit = ItemUnit.query.get_or_404(item_unit_id)

    if item_unit.borrow_records:
        flash('This item unit has borrowing history and cannot be deleted. Set it to inactive instead.', 'warning')
        return redirect(url_for('admin.inventory'))

    asset_tag = item_unit.asset_tag

    db.session.delete(item_unit)
    db.session.commit()

    current_app.logger.info(f'{current_user.email} deleted item unit: {asset_tag}')

    flash('Item unit deleted successfully.', 'success')
    return redirect(url_for('admin.inventory'))

@admin.route('/borrow-records')
@admin_required
def borrow_records():
    """Render a read-only list of borrow records."""
    all_borrow_records = (
        BorrowRecord.query
        .order_by(BorrowRecord.borrowed_at.desc())
        .all()
    )

    return render_template(
        'admin_borrow_records.html',
        borrow_records=all_borrow_records
    )
