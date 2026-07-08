from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, EmailField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError

from .extensions import db
from .models import Category, ItemModel, ItemUnit, User

ITEM_UNIT_ADMIN_STATUSES = ['available', 'maintenance', 'inactive']


def _strip(value):
    return value.strip() if value else value


def _strip_lower(value):
    return value.strip().lower() if value else value


def _strip_upper(value):
    return value.strip().upper() if value else value


class RegisterForm(FlaskForm):
    """Validates new account details on the registration page."""

    name = StringField(
        'Name',
        filters=[_strip],
        validators=[DataRequired(), Length(max=100)],
        render_kw={'required': True}
    )
    email = EmailField(
        'Email',
        filters=[_strip_lower],
        validators=[DataRequired(), Email(), Length(max=150)],
        render_kw={'required': True}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(), Length(min=8, max=128, message='Password must be at least 8 characters long.')],
        render_kw={'required': True}
    )
    confirm_password = PasswordField(
        'Confirm password',
        validators=[DataRequired(), EqualTo('password', message='Passwords do not match.')],
        render_kw={'required': True}
    )

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('An account already exists for that email address.')


class LoginForm(FlaskForm):
    """Validates the login page's email and password fields."""

    email = EmailField('Email', filters=[_strip_lower], validators=[DataRequired()], render_kw={'required': True})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'required': True})


class CategoryForm(FlaskForm):
    """Validates the add/edit category form.

    Excludes its own id from the uniqueness check when editing.
    """

    name = StringField(
        'Name',
        filters=[_strip],
        validators=[DataRequired(message='Category name is required.'), Length(max=100)],
        render_kw={'required': True}
    )
    description = TextAreaField('Description', filters=[_strip])

    def __init__(self, *args, category_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.category_id = category_id

    def validate_name(self, field):
        query = Category.query.filter(db.func.lower(Category.name) == field.data.lower())

        if self.category_id:
            query = query.filter(Category.id != self.category_id)

        if query.first():
            raise ValidationError('A category with that name already exists.')


class ItemModelForm(FlaskForm):
    """Validates the add/edit item model form."""

    category_id = SelectField('Category', coerce=int, validators=[DataRequired()], render_kw={'required': True})
    manufacturer = StringField(
        'Manufacturer',
        filters=[_strip],
        validators=[DataRequired(message='Manufacturer and model name are required.'), Length(max=100)],
        render_kw={'required': True}
    )
    model_name = StringField(
        'Model name',
        filters=[_strip],
        validators=[DataRequired(message='Manufacturer and model name are required.'), Length(max=150)],
        render_kw={'required': True}
    )
    description = TextAreaField('Description', filters=[_strip])
    cost = DecimalField(
        'Estimated cost',
        validators=[Optional(), NumberRange(min=0, message='Cost cannot be negative.')]
    )
    image_url = StringField('Image URL', filters=[_strip], validators=[Optional(), Length(max=500)])
    is_active = BooleanField('Active in catalogue', default=True)

    def __init__(self, *args, item_model_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_model_id = item_model_id

    def validate_model_name(self, field):
        query = ItemModel.query.filter(
            db.func.lower(ItemModel.manufacturer) == self.manufacturer.data.lower(),
            db.func.lower(ItemModel.model_name) == field.data.lower()
        )

        if self.item_model_id:
            query = query.filter(ItemModel.id != self.item_model_id)

        if query.first():
            raise ValidationError('That manufacturer and model name already exists.')


class ItemUnitForm(FlaskForm):
    """Validates the add/edit item unit form."""

    item_model_id = SelectField('Item model', coerce=int, validators=[DataRequired()], render_kw={'required': True})
    asset_tag = StringField(
        'Asset tag',
        filters=[_strip_upper],
        validators=[DataRequired(message='Asset tag is required.'), Length(max=100)],
        render_kw={'required': True}
    )
    status = SelectField(
        'Status',
        choices=[(status, status.title()) for status in ITEM_UNIT_ADMIN_STATUSES],
        validators=[DataRequired()],
        render_kw={'required': True}
    )

    def __init__(self, *args, item_unit_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_unit_id = item_unit_id

    def validate_asset_tag(self, field):
        query = ItemUnit.query.filter(db.func.lower(ItemUnit.asset_tag) == field.data.lower())

        if self.item_unit_id:
            query = query.filter(ItemUnit.id != self.item_unit_id)

        if query.first():
            raise ValidationError('An item unit with that asset tag already exists.')
