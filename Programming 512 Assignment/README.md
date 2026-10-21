# Programming 512 — Smart Campus Resource Booking System

## 1. Project overview

The Smart Campus Resource Booking System is a Python desktop application for managing shared academic resources across multiple campuses. It uses Tkinter for the graphical user interface and SQLite for persistent storage.

The application supports three user roles:

- **Lecturer:** can view resources, make bookings, and view/cancel eligible bookings.
- **Campus administrator:** manages resources and views information for the administrator's assigned campus.
- **System operator:** has system-wide access to booking and resource information and reports.

## 2. Technologies

- Python 3
- Tkinter / ttk for the desktop interface
- SQLite (`sqlite3`) for the database
- Python standard-library modules for password hashing, validation, and file paths

The project does not require third-party Python packages for the functionality documented here.

## 3. Source files

### `auth_app.py`
The main entry point. It provides authentication, registration/dashboard flow, role-aware navigation, and opens the booking, resource-management, booking-history, and reports windows. Run this file to start the application.

### `users.py`
Defines the user classes and role-specific permissions. It includes password hashing and password verification.

### `campus_booking_system.py`
Contains database setup/helper logic for campuses, resources, users, and bookings. Do not run setup routines casually against the submitted database; inspect the code and back up the database first if changing stored data.

### `booking_window.py`
Provides the Tkinter interface for selecting a campus/resource and entering booking details.

### `booking_management.py`
Contains booking-service logic, including booking creation and checks intended to prevent overlapping bookings.

### `booking_history_window.py`
Displays booking history and supports cancellation of eligible future bookings while retaining cancelled records in the database.

### `reports_window.py`
Displays booking totals, active/cancelled counts, average booking duration, and resource-use information, with access restricted by role/campus.

### `resource_management.py`
Provides the resource-management interface for adding, updating, and removing resources according to role permissions.

### `create_staff_account.py`
A command-line helper for creating staff accounts such as campus administrators and system operators. Use it only when you intentionally need to create an account.

### `campus_booking.db`
The SQLite database containing the current campus, user, resource, and booking records. It is included with the project so the existing data is preserved.

## 4. How the application works

1. Start the program from `auth_app.py`.
2. Register or sign in with an account.
3. The application uses the account's role and campus assignment to determine available actions.
4. Users open the booking, resource-management, history, or reports windows that their role permits.
5. Booking and resource information is saved in `campus_booking.db` so it remains available after the application closes.

## 5. Run the application

1. Install Python 3 on your computer. Tkinter is included with most standard Windows Python installations.
2. Extract the project folder from the ZIP file.
3. Open the extracted folder in PyCharm or another Python IDE.
4. Select a compatible Python 3 interpreter.
5. Open `auth_app.py` and run it.
6. Sign in using an existing account and check the actions available to that role.

The application uses Python's standard library and SQLite, so a separate `pip install` step should not normally be required.

## 6. Database preservation and safety

- Keep `campus_booking.db` in the same folder as the Python source files.
- The source files resolve the database path relative to the project folder.
- Do not delete, reset, or replace the database if the existing accounts, resources, and bookings must be preserved.
- Before making any manual database changes, make a backup copy of the database.
- Do not run database setup or staff-account helper scripts unless you intend to perform those operations.

## 7. Development test results

The following functional tests were reported as passing during development:

- Booking creation, rejection of overlapping bookings, and persistence after restart.
- Booking-history display, cancellation of eligible future bookings, retention of cancelled records, and persistence after restart.
- Campus administrator and system operator report access, booking counts, average duration, resource ranking, and refresh behaviour.
- Integration checks covering startup, role permissions, campus policies, booking conflict prevention, cancellation, persistence, reports, and basic error handling.

These are development test results reported by the project developer. A final live GUI run should still be performed on the target Windows computer before submission.

