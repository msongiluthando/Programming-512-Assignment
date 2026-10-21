
import sqlite3
from pathlib import Path
from getpass import getpass

from users import hash_password

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


def create_staff_account():
    print("CREATE A PRIVILEGED TEST ACCOUNT")
    print("1. Campus administrator")
    print("2. System operator")

    choice = input("Choose a role (1 or 2): ").strip()

    if choice not in ("1", "2"):
        print("Invalid role selection.")
        return

    role = "administrator" if choice == "1" else "operator"

    full_name = input("Full name: ").strip()
    username = input("Username: ").strip().lower()
    password = input("Password (minimum 8 characters): ")
    confirmation = input("Confirm password: ")

    if not full_name or len(username) < 3 or " " in username:
        print("Enter a name and a username of at least 3 characters, without spaces.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirmation:
        print("Passwords do not match.")
        return

    campus_id = None

    try:
        with sqlite3.connect(DATABASE_FILE) as connection:
            connection.execute("PRAGMA foreign_keys = ON")

            if role == "administrator":
                campuses = connection.execute("""
                    SELECT campus_id, campus_name
                    FROM campuses
                    ORDER BY campus_id
                """).fetchall()

                if not campuses:
                    print("No campuses found. Run the main application first.")
                    return

                print("\nAvailable campuses:")
                for campus_id_option, campus_name in campuses:
                    print(f"{campus_id_option}. {campus_name}")

                try:
                    campus_id = int(input("Enter the campus ID: "))
                except ValueError:
                    print("Campus ID must be a number.")
                    return

                valid_ids = [campus[0] for campus in campuses]
                if campus_id not in valid_ids:
                    print("That campus ID does not exist.")
                    return

            connection.execute("""
                INSERT INTO users
                (full_name, username, password_hash, role, campus_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                full_name,
                username,
                hash_password(password),
                role,
                campus_id
            ))

        print(f"\nCreated {role} account successfully.")

    except sqlite3.IntegrityError:
        print("That username already exists, or the account data is invalid.")
    except sqlite3.Error as error:
        print(f"Database error: {error}")


if __name__ == "__main__":
    create_staff_account()
