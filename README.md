# PeriPool

PeriPool is a company peripheral borrowing app that lets employees borrow shared office equipment such as mice, keyboards, headsets, webcams, and adapters.

The app helps employees who forgot essential equipment for an office day, and also lets users trial peripherals before requesting a permanent purchase through their cost center.


## Database Design

The application uses a relational SQLite database with SQLAlchemy models. The main entities are Users, Categories, Item Models, Item Units, Borrow Records, and Item Reviews.

The design separates item models from physical item units. This allows the system to represent multiple physical copies of the same model, such as 50 Dell wireless mice, while still tracking each borrowable unit individually.

Full database design documentation is available in:

[Database Design](docs/database_design.md)