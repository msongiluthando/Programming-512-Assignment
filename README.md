# Programming 512 — Smart Campus Resource Booking System

## 1. Project overview

The Smart Campus Resource Booking System is a Python desktop application for managing shared academic resources across multiple campuses. It uses Tkinter for the graphical user interface and SQLite for persistent storage.

The application supports three user roles:

- **Lecturer:** can view resources, make bookings, and view/cancel eligible bookings.
- **Campus administrator:** manages resources and views information for the administrator's assigned campus.
- **System operator:** has system-wide access to booking and resource information, an all-campus bookings list, and comparative reports with monthly trends.

## 2. Technologies

- Python 3
- Tkinter / ttk for the desktop interface
- SQLite (`sqlite3`) for the database
- Python standard-library modules for password hashing, validation, and file paths

The project does not require third-party Python packages for the functionality documented here.

## 3. Source files

### `app.py`
The main entry point. It provides authentication, registration/dashboard flow, role-aware navigation, and opens the booking, resource-management, booking-history, and reports windows. Run this file to start the application.

### `users.py`
Defines the user classes (`User`, `Lecturer`, `CampusAdministrator`, `SystemOperator`) using inheritance, with private attributes exposed through read-only properties (encapsulation). Each role defines its own permissions and which campuses it may work on. Also includes salted PBKDF2 password hashing and verification.

### `campus_booking_system.py`
Contains database setup/helper logic for campuses, resources, users, and bookings. Do not run setup routines casually against the submitted database; inspect the code and back up the database first if changing stored data.

### `booking.py`
Provides the Tkinter interface for selecting a campus/resource and entering booking details. Campus opening hours and maximum duration are checked automatically when the booking is created.

### `booking_policy.py`
Defines the `CampusPolicy` class, which holds each campus's booking rules and is applied by `BookingService` (maximum duration and booking hours). Rules are kept separate from the core booking logic. A new campus only needs a new row in the `campuses` table, and a new rule only needs a new method added to `CampusPolicy._rules`.

### `test_booking_rules.py`
Automated tests (Python `unittest`) for booking rules, overlap prevention, availability and time storage. They run against a temporary database, so `campus_booking.db` is never changed.

### `booking_management.py`
Contains booking-service logic: booking creation, overlap prevention, and availability calculation. Campus-specific rules are applied through `CampusPolicy`.

### `booking_history.py`
Displays booking history and supports cancellation of eligible future bookings while retaining cancelled records in the database.

### `reports.py`
Displays campus reports in four tabs: **Campus Comparison** (total, active and cancelled bookings, average duration, and each campus's booking policy), **Resource Usage** (most frequently used resources), **Monthly Trends** (bookings per month and how much of each campus's maximum booking length is used, which shows the effect of campus-specific rules) and **Busiest Days** (active bookings by day of the week). Campus administrators see only their own campus; system operators see all campuses.

### `report_queries.py`
The SQL behind the all-bookings list and the trend reports, kept separate from the GUI so it can be tested.

### `all_bookings.py`
System-operator screen listing bookings from every campus, with a campus filter and a summary of active and cancelled counts.

### `resource_management.py`
Provides the resource-management interface for adding, updating, and removing resources according to role permissions.

### `create_staff_account.py`
A command-line helper for creating staff accounts such as campus administrators and system operators. Use it only when you intentionally need to create an account.

### `campus_booking.db`
The SQLite database containing the current campus, user, resource, and booking records. It is included with the project so the existing data is preserved.


## 4. How the application works

1. Start the program from `app.py`.
2. Register as a lecturer or sign in with an existing account.
3. **Select a campus.** After login every user chooses the campus to work with. Lecturers can choose any campus, campus administrators are locked to their assigned campus, and system operators can choose one campus or "All campuses". The booking policy of the highlighted campus is shown on this screen.
4. The dashboard clearly shows the **active campus** and the **booking policy in effect**. Use **Change Campus** to switch.
5. Open the booking, resource-management, booking-history, all-bookings or reports windows that your role permits. The resource-management and all-bookings windows start on the active campus.
6. Everything is saved in `campus_booking.db`, so it remains available after the application closes.

## 5. Run the application

1. Install Python 3 on your computer. Tkinter is included with most standard Windows Python installations.
2. Extract the project folder from the ZIP file.
3. Open the extracted folder in PyCharm or another Python IDE.
4. Select a compatible Python 3 interpreter.
5. Open `app.py` and run it.
6. Sign in using an existing account and check the actions available to that role.

The application uses Python's standard library and SQLite, so a separate `pip install` step should not normally be required.

## 6. Database preservation and safety

- Keep `campus_booking.db` in the same folder as the Python source files.
- The source files resolve the database path relative to the project folder.
- Do not delete, reset, or replace the database if the existing accounts, resources, and bookings must be preserved.
- Before making any manual database changes, make a backup copy of the database.
- Do not run database setup or staff-account helper scripts unless you intend to perform those operations.


## GitHub Repository
`Repository Link: https://github.com/msongiluthando/Programming-512-Assignment`