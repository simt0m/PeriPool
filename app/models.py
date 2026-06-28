from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager


def get_utc_now():
    """Return the current UTC date and time.
    
    Used as the default timestamp for database records.
    """
    return datetime.now(timezone.utc)

class User(db.Model, UserMixin):
    """User account for an employee or admin."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now
    )

    borrow_records = db.relationship("BorrowRecord", back_populates="user")
    reviews = db.relationship("ItemReview", back_populates="user")

    def set_password(self, password):
        """Hash and store the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check a submitted password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.name} ({self.email})>"


class Category(db.Model):
    """Category for grouping item models."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now
    )

    item_models = db.relationship("ItemModel", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class ItemModel(db.Model):
    """Catalogue model shown to users."""

    __tablename__ = "item_models"

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)

    manufacturer = db.Column(db.String(100), nullable=False)
    model_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    cost = db.Column(db.Numeric(10, 2))
    image_url = db.Column(db.String(500))

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now
    )

    category = db.relationship("Category", back_populates="item_models")
    item_units = db.relationship("ItemUnit", back_populates="item_model")
    reviews = db.relationship("ItemReview", back_populates="item_model")

    __table_args__ = (
        db.UniqueConstraint(
            "manufacturer",
            "model_name",
            name="uq_item_models_manufacturer_model_name"
        ),
    )

    @property
    def total_units(self):
        """Return the total number of units for this item model."""
        return len(self.item_units)
    
    @property
    def available_units(self):
        """Return the number of available units for this item model."""
        return len([unit for unit in self.item_units if unit.status == "available"])
    
    @property
    def average_rating(self):
        """Return the average review rating for this item model."""
        if not self.reviews:
            return None
        
        total = sum(review.rating for review in self.reviews)
        return round(total / len(self.reviews), 1)
    
    def __repr__(self):
        return f"<ItemModel {self.manufacturer} {self.model_name}>"


class ItemUnit(db.Model):
    """Individual physical item that can be borrowed."""

    __tablename__ = "item_units"

    id = db.Column(db.Integer, primary_key=True)

    item_model_id = db.Column(db.Integer, db.ForeignKey("item_models.id"), nullable=False)

    asset_tag = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="available")

    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now
    )

    item_model = db.relationship("ItemModel", back_populates="item_units")
    borrow_records = db.relationship("BorrowRecord", back_populates="item_unit")

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('available', 'borrowed', 'maintenance', 'inactive')",
            name="ck_item_units_status"
        ),
    )

    def __repr__(self):
        return f"<ItemUnit {self.asset_tag}>"


class BorrowRecord(db.Model):
    """Record of a user borrowing an item unit."""

    __tablename__ = "borrow_records"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_unit_id = db.Column(db.Integer, db.ForeignKey("item_units.id"), nullable=False)

    borrowed_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime)

    status = db.Column(db.String(30), nullable=False, default="active")

    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now
    )

    user = db.relationship("User", back_populates="borrow_records")
    item_unit = db.relationship("ItemUnit", back_populates="borrow_records")

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('active', 'returned', 'cancelled')",
            name="ck_borrow_records_status"
        ),
    )

    def is_overdue(self):
        """Return True when the active borrow record is overdue."""
        return (
            self.status == "active"
            and self.returned_at is None
            and self.due_at < get_utc_now()
        )
    
    def __repr__(self):
        return f"<BorrowRecord user={self.user_id} item_unit={self.item_unit_id}>"

class ItemReview(db.Model):
    """Review left by a user for an item model."""

    __tablename__ = "item_reviews"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_model_id = db.Column(db.Integer, db.ForeignKey("item_models.id"), nullable=False)

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    created_at = db.Column(db.DateTime, nullable=False, default=get_utc_now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=get_utc_now,
        onupdate=get_utc_now
    )

    user = db.relationship("User", back_populates="reviews")
    item_model = db.relationship("ItemModel", back_populates="reviews")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "item_model_id",
            name="uq_item_reviews_user_item_model"
        ),
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_item_reviews_rating_range"
        ),
    )
    
    def __repr__(self):
        return f"<ItemReview user={self.user_id} item_model={self.item_model_id}>"

@login_manager.user_loader
def load_user(user_id):
    """Load a user by ID for Flask-Login."""
    return db.session.get(User, int(user_id))