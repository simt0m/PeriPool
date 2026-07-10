import re
from datetime import timedelta

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, EmailField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, ValidationError

from .extensions import db
from .models import Category, ItemModel, ItemUnit, User, get_utc_now

REVIEW_RATING_CHOICES = [(rating, str(rating)) for rating in range(1, 6)]

ITEM_UNIT_ADMIN_STATUSES = ['available', 'maintenance', 'inactive']

# How far ahead a borrower may choose a return date. Long enough to cover a
# typical loan, short enough that inventory doesn't disappear for months.
MAX_BORROW_DAYS = 30

# Maximum number of items a single user may have on loan at once, so one
# person can't tie up the entire shared pool of a scarce item.
MAX_ACTIVE_BORROWS_PER_USER = 3

# Blocks digits and obviously-wrong symbols, rather than only allowing a fixed
# set of characters — an allow-list here would reject legitimate accented
# names (e.g. "José", "François").
_NAME_INVALID_CHARACTERS = re.compile(r"[0-9@#$%^&*_+=\[\]{}|\\/<>~`\"]")

_PASSWORD_HAS_UPPERCASE = re.compile(r"[A-Z]")
_PASSWORD_HAS_DIGIT = re.compile(r"[0-9]")
_PASSWORD_HAS_SYMBOL = re.compile(r"[^A-Za-z0-9]")


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
        validators=[DataRequired(), Length(min=2, max=100)],
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

    def validate_name(self, field):
        if _NAME_INVALID_CHARACTERS.search(field.data):
            raise ValidationError('Name cannot contain numbers or symbols.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('An account already exists for that email address.')

    def validate_password(self, field):
        if not _PASSWORD_HAS_UPPERCASE.search(field.data):
            raise ValidationError('Password must include an uppercase letter.')

        if not _PASSWORD_HAS_DIGIT.search(field.data):
            raise ValidationError('Password must include a number.')

        if not _PASSWORD_HAS_SYMBOL.search(field.data):
            raise ValidationError('Password must include a symbol.')


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


class BorrowForm(FlaskForm):
    """Validates the return-by date chosen when borrowing an item."""

    due_date = DateField(
        'Return by',
        validators=[DataRequired(message='Please choose a return date.')],
        render_kw={'required': True}
    )

    def validate_due_date(self, field):
        today = get_utc_now().date()
        latest = today + timedelta(days=MAX_BORROW_DAYS)

        if field.data < today:
            raise ValidationError('Return date cannot be in the past.')

        if field.data > latest:
            raise ValidationError(f'Return date cannot be more than {MAX_BORROW_DAYS} days away.')


class ReviewForm(FlaskForm):
    """Validates a rating and comment left for a previously borrowed item model."""

    rating = SelectField(
        'Rating',
        choices=REVIEW_RATING_CHOICES,
        coerce=int,
        validators=[DataRequired()],
        render_kw={'required': True}
    )
    comment = TextAreaField('Comment', filters=[_strip], validators=[Optional(), Length(max=2000)])
