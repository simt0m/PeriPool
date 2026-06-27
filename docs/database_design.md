# PeriPool Database Design

## 1. Design overview


## 2. State transition model

```mermaid
stateDiagram-v2
    [*] --> Available : Create item unit

    Available --> Borrowed : Borrow item
    Available --> Maintenance : Mark as broken / under maintenance
    Available --> Inactive : Remove from circulation

    Borrowed --> Available : Return item
    Borrowed --> Overdue : Due date passes

    Overdue --> Available : Return overdue item

    Maintenance --> Available : Repair complete
    Maintenance --> Inactive : Retire item

    Inactive --> [*]

    note right of Borrowed
      Borrowed items cannot be moved directly
      to Maintenance. The borrow record must be
      closed first by returning the item.
    end note

    note right of Overdue
      Overdue is calculated from the active
      borrow record's due_at date.
    end note
```


## 3. Conceptual data model

The system is based on six main business entities:

- User: a person who can log in and borrow items.
- Category: a grouping such as Headsets, Mice, Keyboards, or Webcams.
- Item Model: a type of item, such as "Dell Wireless Mouse".
- Item Unit: an individual physical item that can be borrowed.
- Borrow Record: a record of a user borrowing a specific item unit.
- Item Review: feedback left by a user for an item model.

Main relationships:

- One user can have many borrow records.
- One category can contain many item models.
- One item model can have many physical item units.
- One item unit can appear in many borrow records over its lifetime.
- One user can write many reviews.
- One item model can receive many reviews.


## 4. Logical data model

### User
- id: Primary Key
- name
- email: Unique
- password_hash
- is_admin
- is_active
- created_at
- updated_at

### Category
- id: Primary Key
- name: Unique
- description
- created_at
- updated_at

### ItemModel
- id: Primary Key
- category_id: Foreign Key to Category
- manufacturer
- model_name
- description
- cost
- image_url
- is_active
- created_at
- updated_at

Constraint:
- manufacturer and model_name must be unique together.

### ItemUnit
- id: Primary Key
- item_model_id: Foreign Key to ItemModel
- asset_tag: Unique
- status
- created_at
- updated_at

### BorrowRecord
- id: Primary Key
- user_id: Foreign Key to User
- item_unit_id: Foreign Key to ItemUnit
- borrowed_at
- due_at
- returned_at
- status
- created_at
- updated_at

### ItemReview
- id: Primary Key
- user_id: Foreign Key to User
- item_model_id: Foreign Key to ItemModel
- rating
- comment
- created_at
- updated_at

Constraint:
- A user can only review each item model once.


## 5. Physical data model / database schema

### Table: users

| Column | Type | Constraint |
|---|---|---|
| id | Integer | Primary Key |
| name | String(100) | Not Null |
| email | String(150) | Unique, Not Null, Indexed |
| password_hash | String(255) | Not Null |
| is_admin | Boolean | Default False, Not Null |
| is_active | Boolean | Default True, Not Null |
| created_at | DateTime | Default Current Timestamp, Not Null |
| updated_at | DateTime | Default Current Timestamp, Not Null |

### Table: categories

| Column | Type | Constraint |
|---|---|---|
| id | Integer | Primary Key |
| name | String(100) | Unique, Not Null |
| description | Text | Nullable |
| created_at | DateTime | Default Current Timestamp, Not Null |
| updated_at | DateTime | Default Current Timestamp, Not Null |

### Table: item_models

| Column | Type | Constraint |
|---|---|---|
| id | Integer | Primary Key |
| category_id | Integer | Foreign Key to categories.id, Not Null |
| manufacturer | String(100) | Not Null |
| model_name | String(150) | Not Null |
| description | Text | Nullable |
| cost | Numeric(10,2) | Nullable |
| image_url | String(500) | Nullable |
| is_active | Boolean | Default True, Not Null |
| created_at | DateTime | Default Current Timestamp, Not Null |
| updated_at | DateTime | Default Current Timestamp, Not Null |

Unique constraint:
- manufacturer + model_name

### Table: item_units

| Column | Type | Constraint |
|---|---|---|
| id | Integer | Primary Key |
| item_model_id | Integer | Foreign Key to item_models.id, Not Null |
| asset_tag | String(100) | Unique, Not Null |
| status | String(30) | Default 'available', Not Null |
| created_at | DateTime | Default Current Timestamp, Not Null |
| updated_at | DateTime | Default Current Timestamp, Not Null |

Allowed status values:
- available
- borrowed
- maintenance
- inactive

### Table: borrow_records

| Column | Type | Constraint |
|---|---|---|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key to users.id, Not Null |
| item_unit_id | Integer | Foreign Key to item_units.id, Not Null |
| borrowed_at | DateTime | Default Current Timestamp, Not Null |
| due_at | DateTime | Not Null |
| returned_at | DateTime | Nullable |
| status | String(30) | Default 'active', Not Null |
| created_at | DateTime | Default Current Timestamp, Not Null |
| updated_at | DateTime | Default Current Timestamp, Not Null |

Allowed status values:
- active
- returned
- cancelled

Overdue records are identified where:
- status = active
- returned_at is null
- due_at is before the current date/time

### Table: item_reviews

| Column | Type | Constraint |
|---|---|---|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key to users.id, Not Null |
| item_model_id | Integer | Foreign Key to item_models.id, Not Null |
| rating | Integer | Not Null |
| comment | Text | Nullable |
| created_at | DateTime | Default Current Timestamp, Not Null |
| updated_at | DateTime | Default Current Timestamp, Not Null |

Constraints:
- user_id + item_model_id must be unique.
- rating should be between 1 and 5.


## 6. UML class diagram

```mermaid
classDiagram
    class User {
        +int id
        +string name
        +string email
        +string password_hash
        +bool is_admin
        +bool is_active
        +datetime created_at
        +datetime updated_at
    }

    class Category {
        +int id
        +string name
        +text description
        +datetime created_at
        +datetime updated_at
    }

    class ItemModel {
        +int id
        +int category_id
        +string manufacturer
        +string model_name
        +text description
        +decimal cost
        +string image_url
        +bool is_active
        +datetime created_at
        +datetime updated_at
        +average_rating()
    }

    class ItemUnit {
        +int id
        +int item_model_id
        +string asset_tag
        +string status
        +datetime created_at
        +datetime updated_at
    }

    class BorrowRecord {
        +int id
        +int user_id
        +int item_unit_id
        +datetime borrowed_at
        +datetime due_at
        +datetime returned_at
        +string status
        +datetime created_at
        +datetime updated_at
        +is_overdue()
    }

    class ItemReview {
        +int id
        +int user_id
        +int item_model_id
        +int rating
        +text comment
        +datetime created_at
        +datetime updated_at
    }

    User "1" --> "many" BorrowRecord
    User "1" --> "many" ItemReview

    Category "1" --> "many" ItemModel

    ItemModel "1" --> "many" ItemUnit
    ItemModel "1" --> "many" ItemReview

    ItemUnit "1" --> "many" BorrowRecord
```


## 7. Entity-relationship diagram

```mermaid
erDiagram
    USERS ||--o{ BORROW_RECORDS : makes
    USERS ||--o{ ITEM_REVIEWS : writes

    CATEGORIES ||--o{ ITEM_MODELS : contains

    ITEM_MODELS ||--o{ ITEM_UNITS : has
    ITEM_MODELS ||--o{ ITEM_REVIEWS : receives

    ITEM_UNITS ||--o{ BORROW_RECORDS : appears_in

    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        boolean is_admin
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    CATEGORIES {
        int id PK
        string name UK
        text description
        datetime created_at
        datetime updated_at
    }

    ITEM_MODELS {
        int id PK
        int category_id FK
        string manufacturer
        string model_name
        text description
        decimal cost
        string image_url
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    ITEM_UNITS {
        int id PK
        int item_model_id FK
        string asset_tag UK
        string status
        datetime created_at
        datetime updated_at
    }

    BORROW_RECORDS {
        int id PK
        int user_id FK
        int item_unit_id FK
        datetime borrowed_at
        datetime due_at
        datetime returned_at
        string status
        datetime created_at
        datetime updated_at
    }

    ITEM_REVIEWS {
        int id PK
        int user_id FK
        int item_model_id FK
        int rating
        text comment
        datetime created_at
        datetime updated_at
    }
```


## 8. Design rules and constraints

### User deletion
Users should not normally be deleted because this could damage historical borrowing records. Instead, a user can be marked as inactive by setting `is_active` to false.

### Item availability
Available stock is not stored directly on `item_models`. It is calculated by counting related `item_units` where `status = 'available'`.

### Borrowing rule
An item unit can only be borrowed if its status is `available`.

When an item is borrowed:
- `item_units.status` changes to `borrowed`
- a new `borrow_records` row is created
- `borrow_records.status` is set to `active`
- `borrow_records.returned_at` remains null

When an item is returned:
- `borrow_records.status` changes to `returned`
- `borrow_records.returned_at` is set to the current timestamp
- `item_units.status` changes back to `available`

### Overdue rule
Overdue status is calculated rather than permanently stored on the item unit.

A borrow record is overdue when:
- `borrow_records.status = 'active'`
- `borrow_records.returned_at is null`
- `borrow_records.due_at` is before the current datetime

### Review rule
A user can only review each item model once. This is enforced using a unique constraint on:
- `user_id`
- `item_model_id`

### Rating rule
Review ratings must be between 1 and 5. Average item ratings are calculated from related item review records.