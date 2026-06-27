from flask import Blueprint, render_template

from .models import ItemModel

main = Blueprint('main', __name__)

@main.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@main.route('/catalogue')
def catalogue():
    """Render the item model catalogue."""
    item_models = (
        ItemModel.query
        .filter_by(is_active=True)
        .order_by(ItemModel.manufacturer, ItemModel.model_name)
        .all()
    )

    return render_template('catalogue.html', item_models=item_models)