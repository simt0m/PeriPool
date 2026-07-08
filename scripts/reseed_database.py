from datetime import timedelta

from app import create_app
from app.extensions import db
from app.models import (
    User,
    Category,
    ItemModel,
    ItemUnit,
    BorrowRecord,
    ItemReview,
    get_utc_now
)


app = create_app()


with app.app_context():
    db.drop_all()
    db.create_all()

    admin = User(
        name="Admin User",
        email="admin@peripool.com",
        is_admin=True,
    )
    admin.set_password("AdminPass123!")

    employee = User(
        name="Alex Carter",
        email="alex.carter@peripool.com",
        is_admin=False,
    )
    employee.set_password("EmployeePass123!")

    headset_category = Category(
        name="Headsets",
        description="Audio devices for calls, meetings, and hybrid working."
    )

    webcam_category = Category(
        name="Webcams",
        description="Video devices for meetings and remote collaboration."
    )

    mouse_category = Category(
        name="Mice",
        description="Pointing devices for office and ergonomic use."
    )

    keyboard_category = Category(
        name="Keyboards",
        description="Keyboards for standard and ergonomic working."
    )

    dock_category = Category(
        name="Docking Stations",
        description="Docking equipment for connecting laptops to desk setups."
    )

    jabra_65 = ItemModel(
        category=headset_category,
        manufacturer="Jabra",
        model_name="Evolve2 65",
        description="Wireless headset suitable for Teams calls and hybrid meetings.",
        cost=149.99,
        image_url=None,
    )

    jabra_55 = ItemModel(
        category=headset_category,
        manufacturer="Jabra",
        model_name="Evolve2 55",
        description="Lightweight headset for office calls and general use.",
        cost=119.99,
        image_url=None,
    )

    logitech_brio = ItemModel(
        category=webcam_category,
        manufacturer="Logitech",
        model_name="Brio",
        description="High-quality webcam for video meetings.",
        cost=139.99,
        image_url=None,
    )

    mx_master = ItemModel(
        category=mouse_category,
        manufacturer="Logitech",
        model_name="MX Master 3",
        description="Ergonomic wireless mouse for productivity work.",
        cost=89.99,
        image_url=None,
    )

    dell_dock = ItemModel(
        category=dock_category,
        manufacturer="Dell",
        model_name="WD19",
        description="USB-C docking station for desk setups.",
        cost=169.99,
        image_url=None,
    )

    item_units = [
        ItemUnit(item_model=jabra_65, asset_tag="PP-HS-001", status="available"),
        ItemUnit(item_model=jabra_65, asset_tag="PP-HS-002", status="available"),
        ItemUnit(item_model=jabra_65, asset_tag="PP-HS-003", status="borrowed"),
        ItemUnit(item_model=jabra_55, asset_tag="PP-HS-004", status="available"),
        ItemUnit(item_model=jabra_55, asset_tag="PP-HS-005", status="maintenance"),
        ItemUnit(item_model=logitech_brio, asset_tag="PP-WC-001", status="available"),
        ItemUnit(item_model=mx_master, asset_tag="PP-MS-001", status="available"),
        ItemUnit(item_model=mx_master, asset_tag="PP-MS-002", status="available"),
        ItemUnit(item_model=dell_dock, asset_tag="PP-DS-001", status="available"),
    ]

    active_borrow = BorrowRecord(
        user=employee,
        item_unit=item_units[2],
        borrowed_at=get_utc_now(),
        due_at=get_utc_now() + timedelta(days=7),
        status="active",
    )

    review = ItemReview(
        user=employee,
        item_model=jabra_65,
        rating=5,
        comment="Comfortable headset with strong microphone quality.",
    )

    db.session.add_all([
        admin,
        employee,
        headset_category,
        webcam_category,
        mouse_category,
        keyboard_category,
        dock_category,
        jabra_65,
        jabra_55,
        logitech_brio,
        mx_master,
        dell_dock,
        *item_units,
        active_borrow,
        review,
    ])

    db.session.commit()

    print("Database reseeded successfully.")
    print("Admin login: admin@peripool.com / AdminPass123!")
    print("Employee login: alex.carter@peripool.com / EmployeePass123!")