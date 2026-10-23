import sqlite3
from pathlib import Path
from datetime import datetime, date

from booking_policy import CampusPolicy, to_minutes, to_text

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class BookingService:

    def __init__(self, database_file=None):
        self.database_file = database_file or DATABASE_FILE

    def connect_database(self):
        connection = sqlite3.connect(self.database_file)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def time_to_minutes(time_text):
        parsed_time = datetime.strptime(time_text, "%H:%M")
        return parsed_time.hour * 60 + parsed_time.minute

    def get_policy(self, campus_id, connection=None):
        own_connection = connection is None
        connection = connection or self.connect_database()
        try:
            row = connection.execute("""
                SELECT campus_name, max_duration, opening_time, closing_time
                FROM campuses
                WHERE campus_id = ?
            """, (campus_id,)).fetchone()
        finally:
            if own_connection:
                connection.close()
        return CampusPolicy(*row) if row else None

    def get_availability(self, resource_id, booking_date):
        try:
            selected_date = datetime.strptime(
                booking_date, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return None, "Enter the date as YYYY-MM-DD to see availability."

        try:
            with self.connect_database() as connection:
                row = connection.execute("""
                    SELECT campus_id FROM resources WHERE resource_id = ?
                """, (resource_id,)).fetchone()

                if row is None:
                    return None, "Select a resource to see availability."

                policy = self.get_policy(row[0], connection)

                booked = connection.execute("""
                    SELECT start_time, duration_minutes
                    FROM bookings
                    WHERE resource_id = ?
                      AND booking_date = ?
                      AND status = 'active'
                """, (resource_id, selected_date.isoformat())).fetchall()
        except sqlite3.Error as error:
            return None, f"Could not load availability: {error}"

        intervals = sorted(
            (to_minutes(start), to_minutes(start) + duration)
            for start, duration in booked
        )

        segments = []
        cursor = policy.opening_minutes

        for start, end in intervals:
            start = max(start, policy.opening_minutes)
            end = min(end, policy.closing_minutes)
            if end <= start:
                continue
            if start > cursor:
                segments.append(
                    (to_text(cursor), to_text(start), "Available")
                )
            segments.append((to_text(start), to_text(end), "Booked"))
            cursor = max(cursor, end)

        if cursor < policy.closing_minutes:
            segments.append(
                (to_text(cursor), to_text(policy.closing_minutes),
                 "Available")
            )

        return segments, ""

    def create_booking(
        self, lecturer_id, campus_id, resource_id,
        booking_date, start_time, duration_minutes
    ):
        try:
            selected_date = datetime.strptime(
                booking_date, "%Y-%m-%d"
            ).date()

            if selected_date < date.today():
                return False, "You cannot book a date in the past."

            start_minutes = self.time_to_minutes(start_time)

            if (
                not isinstance(duration_minutes, int)
                or duration_minutes <= 0
            ):
                return False, "Duration must be a positive whole number."

        except (ValueError, TypeError):
            return False, (
                "Check the date (YYYY-MM-DD), time (HH:MM), "
                "and duration."
            )

        booking_date = selected_date.isoformat()
        start_time = to_text(start_minutes)

        connection = self.connect_database()

        try:
            connection.execute("BEGIN IMMEDIATE")

            policy = self.get_policy(campus_id, connection)

            if policy is None:
                connection.rollback()
                return False, "The selected campus does not exist."

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

            problem = policy.validate(start_minutes, duration_minutes)
            if problem:
                connection.rollback()
                return False, problem

            end_minutes = start_minutes + duration_minutes

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
