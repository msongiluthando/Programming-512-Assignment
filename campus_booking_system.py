import sqlite3
from pathlib import Path

# Create a database file inside the project folder
PROJECT_FOLDER = Path(__file__).resolve().parent
DATABASE_FILE = PROJECT_FOLDER / "campus_booking.db"


def connect_database():
    """Connect to the SQLite database."""
    connection = sqlite3.connect(DATABASE_FILE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables():
    """Create the tables needed by the booking system."""

    with connect_database() as connection:

        # Store users and their roles
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN (
                        'lecturer',
                        'administrator',
                        'operator'
                    )
                ),
                campus_id INTEGER,
                FOREIGN KEY (campus_id)
                    REFERENCES campuses(campus_id)
            )
        """)

        # Store campuses and their booking policies
        connection.execute("""
            CREATE TABLE IF NOT EXISTS campuses (
                campus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                campus_name TEXT NOT NULL UNIQUE,
                max_duration INTEGER NOT NULL,
                opening_time TEXT NOT NULL,
                closing_time TEXT NOT NULL
            )
        """)

        # Store resources belonging to campuses
        connection.execute("""
            CREATE TABLE IF NOT EXISTS resources (
                resource_id TEXT PRIMARY KEY,
                resource_name TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                campus_id INTEGER NOT NULL,
                FOREIGN KEY (campus_id)
                    REFERENCES campuses(campus_id)
            )
        """)

        # Store bookings made by lecturers
        connection.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id TEXT NOT NULL,
                lecturer_id INTEGER NOT NULL,
                campus_id INTEGER NOT NULL,
                booking_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'cancelled')),
                FOREIGN KEY (resource_id)
                    REFERENCES resources(resource_id),
                FOREIGN KEY (lecturer_id)
                    REFERENCES users(user_id),
                FOREIGN KEY (campus_id)
                    REFERENCES campuses(campus_id),
                CHECK (duration_minutes > 0)
            )
        """)

        # Add indexes to speed up common booking searches
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_booking_resource_date
            ON bookings(resource_id, booking_date, status)
        """)

    print("Database tables created successfully.")


def add_sample_campuses():
    """Add three campuses with different booking policies."""

    campuses = [
        ("Durban Campus", 120, "08:00", "17:00"),
        ("Johannesburg Campus", 180, "07:00", "18:00"),
        ("Cape Town Campus", 60, "09:00", "16:00")
    ]

    with connect_database() as connection:
        connection.executemany("""
            INSERT OR IGNORE INTO campuses
            (campus_name, max_duration, opening_time, closing_time)
            VALUES (?, ?, ?, ?)
        """, campuses)

    print("Sample campuses added successfully.")


def show_campuses():
    """Display all campuses and their booking policies."""

    with connect_database() as connection:
        rows = connection.execute("""
            SELECT campus_id, campus_name, max_duration,
                   opening_time, closing_time
            FROM campuses
            ORDER BY campus_name
        """).fetchall()

    print("\nREGISTERED CAMPUSES")
    print("-" * 65)

    for campus in rows:
        print(
            f"ID: {campus[0]} | "
            f"Campus: {campus[1]} | "
            f"Maximum duration: {campus[2]} minutes | "
            f"Hours: {campus[3]}–{campus[4]}"
        )


if __name__ == "__main__":
    create_tables()
    add_sample_campuses()
    show_campuses()
