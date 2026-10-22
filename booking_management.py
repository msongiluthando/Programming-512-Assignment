import sqlite3
from pathlib import Path
from datetime import datetime, date

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class BookingService:
    """Handles booking rules and saves valid bookings."""

    def connect_database(self):
        connection = sqlite3.connect(DATABASE_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def time_to_minutes(time_text):
        """Convert a time such as 09:30 into minutes after midnight."""
        parsed_time = datetime.strptime(time_text, "%H:%M")
        return parsed_time.hour * 60 + parsed_time.minute

    def create_booking(
        self, lecturer_id, campus_id, resource_id,
        booking_date, start_time, duration_minutes
    ):
        """Validate and save a booking. Return success and a message."""

        try:
            selected_date = datetime.strptime(
                booking_date, "%Y-%m-%d"
            ).date()

            if selected_date < date.today():
                return False, "You cannot book a date in the past."

            start_minutes = self.time_to_minutes(start_time)

            if not isinstance(duration_minutes, int) or duration_minutes <= 0:
                return False, "Duration must be a positive whole number."

        except (ValueError, TypeError):
            return False, (
                "Check the date (YYYY-MM-DD), time (HH:MM), "
                "and duration."
            )

        connection = self.connect_database()

        try:
            connection.execute("BEGIN IMMEDIATE")

            campus = connection.execute("""
                SELECT max_duration, opening_time, closing_time
                FROM campuses
                WHERE campus_id = ?
            """, (campus_id,)).fetchone()

            if campus is None:
                connection.rollback()
                return False, "The selected campus does not exist."

            max_duration, opening_time, closing_time = campus

            resource = connection.execute("""
                SELECT campus_id, resource_name
                FROM resources
                WHERE resource_id = ?
            """, (resource_id,)).fetchone()

            if resource is None:
                connection.rollback()
                return False, "The selected resource does not exist."

            if resource[0] != campus_id:
                connection.rollback()
                return False, (
                    "This resource does not belong to the selected campus."
                )

            lecturer = connection.execute("""
                SELECT role FROM users WHERE user_id = ?
            """, (lecturer_id,)).fetchone()

            if lecturer is None or lecturer[0] != "lecturer":
                connection.rollback()
                return False, "Only a registered lecturer can book resources."

            if duration_minutes > max_duration:
                connection.rollback()
                return False, (
                    f"This campus allows bookings up to "
                    f"{max_duration} minutes."
                )

            opening_minutes = self.time_to_minutes(opening_time)
            closing_minutes = self.time_to_minutes(closing_time)
            end_minutes = start_minutes + duration_minutes

            if (
                start_minutes < opening_minutes
                or end_minutes > closing_minutes
            ):
                connection.rollback()
                return False, (
                    f"Bookings must fall within campus hours: "
                    f"{opening_time}–{closing_time}."
                )

            # Check all active bookings for this resource and date.
            existing_bookings = connection.execute("""
                SELECT start_time, duration_minutes
                FROM bookings
                WHERE resource_id = ?
                  AND booking_date = ?
                  AND status = 'active'
            """, (resource_id, booking_date)).fetchall()

            for existing_start, existing_duration in existing_bookings:
                existing_start_minutes = self.time_to_minutes(
                    existing_start
                )
                existing_end_minutes = (
                    existing_start_minutes + existing_duration
                )

                if (
                    start_minutes < existing_end_minutes
                    and end_minutes > existing_start_minutes
                ):
                    connection.rollback()
                    return False, (
                        "This resource is already booked during "
                        "part or all of that time. Choose another time."
                    )

            connection.execute("""
                INSERT INTO bookings (
                    resource_id, lecturer_id, campus_id,
                    booking_date, start_time, duration_minutes, status
                )
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (
                resource_id, lecturer_id, campus_id,
                booking_date, start_time, duration_minutes
            ))

            connection.commit()
            return True, "Booking created successfully."

        except sqlite3.Error as error:
            connection.rollback()
            return False, f"Database error: {error}"

        finally:
            connection.close()


if __name__ == "__main__":
    print("Booking engine loaded successfully.")
    print("Campus-specific policy checks are ready.")
