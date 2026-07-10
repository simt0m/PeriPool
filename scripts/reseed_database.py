import itertools
from collections import defaultdict
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

_asset_tag_counters = defaultdict(lambda: itertools.count(1))


def make_units(item_model, code, statuses):
    """Create item units for a model, numbering asset tags per-category."""
    counter = _asset_tag_counters[code]
    return [
        ItemUnit(item_model=item_model, asset_tag=f"PP-{code}-{next(counter):03d}", status=status)
        for status in statuses
    ]


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

    employee_two = User(
        name="Priya Shah",
        email="priya.shah@peripool.com",
        is_admin=False,
    )
    employee_two.set_password("EmployeePass123!")

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

    # --- Headsets ---

    jabra_65 = ItemModel(
        category=headset_category,
        manufacturer="Jabra",
        model_name="Evolve2 65",
        description="Wireless headset suitable for Teams calls and hybrid meetings.",
        cost=149.99,
        image_url=None,
    )
    jabra_65_units = make_units(jabra_65, "HS", ["available", "available", "borrowed"])

    jabra_55 = ItemModel(
        category=headset_category,
        manufacturer="Jabra",
        model_name="Evolve2 55",
        description="Lightweight headset for office calls and general use.",
        cost=119.99,
        image_url=None,
    )
    jabra_55_units = make_units(jabra_55, "HS", ["available", "maintenance"])

    poly_focus = ItemModel(
        category=headset_category,
        manufacturer="Poly",
        model_name="Voyager Focus 2",
        description="Active noise-cancelling headset for open-plan offices.",
        cost=229.99,
        image_url=None,
    )
    poly_focus_units = make_units(poly_focus, "HS", ["available", "available", "borrowed"])

    logitech_zone = ItemModel(
        category=headset_category,
        manufacturer="Logitech",
        model_name="Zone Wireless",
        description="Wireless headset with a boom mic for busy environments.",
        cost=179.99,
        image_url=None,
    )
    logitech_zone_units = make_units(logitech_zone, "HS", ["available", "borrowed"])

    sennheiser_sc165 = ItemModel(
        category=headset_category,
        manufacturer="Sennheiser",
        model_name="SC 165",
        description="Wired stereo headset for desk-based calls.",
        cost=99.99,
        image_url=None,
    )
    sennheiser_sc165_units = make_units(sennheiser_sc165, "HS", ["available", "available"])

    # --- Webcams ---

    logitech_brio = ItemModel(
        category=webcam_category,
        manufacturer="Logitech",
        model_name="Brio",
        description="High-quality 4K webcam for video meetings.",
        cost=139.99,
        image_url=None,
    )
    logitech_brio_units = make_units(logitech_brio, "WC", ["available", "borrowed"])

    logitech_c920s = ItemModel(
        category=webcam_category,
        manufacturer="Logitech",
        model_name="C920s",
        description="Full HD webcam with a built-in privacy shutter.",
        cost=79.99,
        image_url=None,
    )
    logitech_c920s_units = make_units(logitech_c920s, "WC", ["available", "available", "borrowed"])

    dell_wb7022 = ItemModel(
        category=webcam_category,
        manufacturer="Dell",
        model_name="WB7022",
        description="4K webcam with auto-framing for meeting rooms.",
        cost=129.99,
        image_url=None,
    )
    dell_wb7022_units = make_units(dell_wb7022, "WC", ["available", "maintenance"])

    anker_c200 = ItemModel(
        category=webcam_category,
        manufacturer="Anker",
        model_name="PowerConf C200",
        description="Compact 2K webcam for hybrid working setups.",
        cost=69.99,
        image_url=None,
    )
    anker_c200_units = make_units(anker_c200, "WC", ["available", "available"])

    # --- Mice ---

    mx_master = ItemModel(
        category=mouse_category,
        manufacturer="Logitech",
        model_name="MX Master 3",
        description="Ergonomic wireless mouse for productivity work.",
        cost=89.99,
        image_url=None,
    )
    mx_master_units = make_units(mx_master, "MS", ["borrowed", "available"])

    mx_anywhere = ItemModel(
        category=mouse_category,
        manufacturer="Logitech",
        model_name="MX Anywhere 3",
        description="Compact wireless mouse suited to travel and hot-desking.",
        cost=69.99,
        image_url=None,
    )
    mx_anywhere_units = make_units(mx_anywhere, "MS", ["available", "available"])

    surface_precision = ItemModel(
        category=mouse_category,
        manufacturer="Microsoft",
        model_name="Surface Precision Mouse",
        description="Precision mouse with customisable buttons for multitasking.",
        cost=99.99,
        image_url=None,
    )
    surface_precision_units = make_units(surface_precision, "MS", ["available", "borrowed"])

    m720_triathlon = ItemModel(
        category=mouse_category,
        manufacturer="Logitech",
        model_name="M720 Triathlon",
        description="Multi-device wireless mouse for switching between machines.",
        cost=49.99,
        image_url=None,
    )
    m720_triathlon_units = make_units(m720_triathlon, "MS", ["available", "available", "maintenance"])

    # --- Keyboards ---

    mx_keys = ItemModel(
        category=keyboard_category,
        manufacturer="Logitech",
        model_name="MX Keys",
        description="Backlit wireless keyboard for office and hybrid use.",
        cost=109.99,
        image_url=None,
    )
    mx_keys_units = make_units(mx_keys, "KB", ["available", "available", "borrowed"])

    surface_keyboard = ItemModel(
        category=keyboard_category,
        manufacturer="Microsoft",
        model_name="Surface Keyboard",
        description="Slim wireless keyboard for desk setups.",
        cost=89.99,
        image_url=None,
    )
    surface_keyboard_units = make_units(surface_keyboard, "KB", ["available", "available"])

    keychron_k8 = ItemModel(
        category=keyboard_category,
        manufacturer="Keychron",
        model_name="K8",
        description="Mechanical keyboard for staff who prefer tactile typing.",
        cost=79.99,
        image_url=None,
    )
    keychron_k8_units = make_units(keychron_k8, "KB", ["available", "maintenance"])

    dell_kb216 = ItemModel(
        category=keyboard_category,
        manufacturer="Dell",
        model_name="KB216",
        description="Standard wired keyboard for general office use.",
        cost=19.99,
        image_url=None,
    )
    dell_kb216_units = make_units(dell_kb216, "KB", ["available", "available", "available"])

    # --- Docking Stations ---

    dell_dock = ItemModel(
        category=dock_category,
        manufacturer="Dell",
        model_name="WD19",
        description="USB-C docking station for desk setups.",
        cost=169.99,
        image_url=None,
    )
    dell_dock_units = make_units(dell_dock, "DS", ["available", "available"])

    dell_wd22tb4 = ItemModel(
        category=dock_category,
        manufacturer="Dell",
        model_name="WD22TB4",
        description="Thunderbolt 4 docking station for higher-spec laptops.",
        cost=249.99,
        image_url=None,
    )
    dell_wd22tb4_units = make_units(dell_wd22tb4, "DS", ["available", "borrowed"])

    caldigit_ts4 = ItemModel(
        category=dock_category,
        manufacturer="CalDigit",
        model_name="TS4",
        description="High-throughput dock for demanding multi-monitor setups.",
        cost=329.99,
        image_url=None,
    )
    caldigit_ts4_units = make_units(caldigit_ts4, "DS", ["available", "maintenance"])

    anker_powerexpand = ItemModel(
        category=dock_category,
        manufacturer="Anker",
        model_name="PowerExpand Elite",
        description="13-in-1 docking station for expanding a single laptop port.",
        cost=199.99,
        image_url=None,
    )
    anker_powerexpand_units = make_units(anker_powerexpand, "DS", ["available", "available"])

    all_item_models = [
        jabra_65, jabra_55, poly_focus, logitech_zone, sennheiser_sc165,
        logitech_brio, logitech_c920s, dell_wb7022, anker_c200,
        mx_master, mx_anywhere, surface_precision, m720_triathlon,
        mx_keys, surface_keyboard, keychron_k8, dell_kb216,
        dell_dock, dell_wd22tb4, caldigit_ts4, anker_powerexpand,
    ]

    all_item_units = (
        jabra_65_units + jabra_55_units + poly_focus_units + logitech_zone_units + sennheiser_sc165_units
        + logitech_brio_units + logitech_c920s_units + dell_wb7022_units + anker_c200_units
        + mx_master_units + mx_anywhere_units + surface_precision_units + m720_triathlon_units
        + mx_keys_units + surface_keyboard_units + keychron_k8_units + dell_kb216_units
        + dell_dock_units + dell_wd22tb4_units + caldigit_ts4_units + anker_powerexpand_units
    )

    active_borrow = BorrowRecord(
        user=employee,
        item_unit=jabra_65_units[2],
        borrowed_at=get_utc_now(),
        due_at=get_utc_now() + timedelta(days=7),
        status="active",
    )

    overdue_borrow = BorrowRecord(
        user=employee,
        item_unit=mx_master_units[0],
        borrowed_at=get_utc_now() - timedelta(days=10),
        due_at=get_utc_now() - timedelta(days=3),
        status="active",
    )

    returned_borrow = BorrowRecord(
        user=employee,
        item_unit=logitech_c920s_units[2],
        borrowed_at=get_utc_now() - timedelta(days=14),
        due_at=get_utc_now() - timedelta(days=7),
        returned_at=get_utc_now() - timedelta(days=8),
        status="returned",
    )

    priya_active_borrow = BorrowRecord(
        user=employee_two,
        item_unit=poly_focus_units[2],
        borrowed_at=get_utc_now(),
        due_at=get_utc_now() + timedelta(days=5),
        status="active",
    )

    priya_second_active_borrow = BorrowRecord(
        user=employee_two,
        item_unit=mx_keys_units[2],
        borrowed_at=get_utc_now(),
        due_at=get_utc_now() + timedelta(days=10),
        status="active",
    )

    priya_returned_borrow = BorrowRecord(
        user=employee_two,
        item_unit=logitech_zone_units[1],
        borrowed_at=get_utc_now() - timedelta(days=20),
        due_at=get_utc_now() - timedelta(days=13),
        returned_at=get_utc_now() - timedelta(days=15),
        status="returned",
    )

    reviews = [
        ItemReview(
            user=employee,
            item_model=jabra_65,
            rating=5,
            comment="Comfortable headset with strong microphone quality.",
        ),
        ItemReview(
            user=employee,
            item_model=logitech_c920s,
            rating=4,
            comment="Sharp picture in video calls, but a bit bulky to carry between desks.",
        ),
        ItemReview(
            user=employee,
            item_model=mx_master,
            rating=4,
            comment="Very comfortable for long sessions, though the battery drains faster than expected.",
        ),
        ItemReview(
            user=employee_two,
            item_model=poly_focus,
            rating=5,
            comment="Excellent noise cancelling for our open-plan office.",
        ),
        ItemReview(
            user=employee_two,
            item_model=logitech_zone,
            rating=3,
            comment="Solid audio, but the headband is a little tight after a few hours.",
        ),
        ItemReview(
            user=employee_two,
            item_model=mx_keys,
            rating=5,
            comment="Great typing feel and the backlight is handy in low light.",
        ),
    ]

    db.session.add_all([
        admin,
        employee,
        employee_two,
        headset_category,
        webcam_category,
        mouse_category,
        keyboard_category,
        dock_category,
        *all_item_models,
        *all_item_units,
        active_borrow,
        overdue_borrow,
        returned_borrow,
        priya_active_borrow,
        priya_second_active_borrow,
        priya_returned_borrow,
        *reviews,
    ])

    db.session.commit()

    print("Database reseeded successfully.")
    print(f"Seeded {len(all_item_models)} item models across 5 categories with {len(all_item_units)} units.")
    print("Admin login: admin@peripool.com / AdminPass123!")
    print("Employee login: alex.carter@peripool.com / EmployeePass123!")
    print("Employee login: priya.shah@peripool.com / EmployeePass123!")
