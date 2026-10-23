import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta

import campus_booking_system
from booking_management import BookingService
from report_queries import (
    fetch_all_bookings, fetch_monthly_trends, fetch_weekday_usage
)
from users import hash_password

FUTURE = (date.today() + timedelta(days=30)).isoformat()


class BookingRuleTests(unittest.TestCase):

    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix=".db")
        os.close(handle)

        campus_booking_system.DATABASE_FILE = self.path
        campus_booking_system.create_tables()
        campus_booking_system.add_sample_campuses()

        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO users (full_name, username, password_hash,"
                " role, campus_id) VALUES (?, ?, ?, ?, ?)",
                ("Test Lecturer", "lect", hash_password("password1"),
                 "lecturer", 1))
            connection.execute(
                "INSERT INTO users (full_name, username, password_hash,"
                " role, campus_id) VALUES (?, ?, ?, ?, ?)",
                ("Test Admin", "adm", hash_password("password1"),
                 "administrator", 1))
            connection.executemany(
                "INSERT INTO resources VALUES (?, ?, ?, ?)",
                [("LAB1", "Lab 1", "Lab", 1),
                 ("LAB2", "Lab 2", "Lab", 3)])

        self.service = BookingService(self.path)

    def tearDown(self):
        os.remove(self.path)

    def book(self, campus, resource, day, start, minutes, user=1):
        return self.service.create_booking(
            user, campus, resource, day, start, minutes)

    def test_valid_booking_is_saved(self):
        ok, _ = self.book(1, "LAB1", FUTURE, "10:00", 60)
        self.assertTrue(ok)
        with sqlite3.connect(self.path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM bookings").fetchone()[0]
        self.assertEqual(count, 1)

    def test_overlapping_booking_rejected(self):
        self.book(1, "LAB1", FUTURE, "10:00", 60)
        ok, _ = self.book(1, "LAB1", FUTURE, "10:30", 60)
        self.assertFalse(ok)

    def test_back_to_back_booking_allowed(self):
        self.book(1, "LAB1", FUTURE, "10:00", 60)
        ok, _ = self.book(1, "LAB1", FUTURE, "11:00", 60)
        self.assertTrue(ok)

    def test_campus_max_duration_differs(self):
        # Durban allows 120 minutes, Cape Town only 60.
        self.assertTrue(self.book(1, "LAB1", FUTURE, "09:00", 120)[0])
        self.assertFalse(self.book(3, "LAB2", FUTURE, "10:00", 90)[0])

    def test_campus_hours_enforced(self):
        self.assertFalse(self.book(3, "LAB2", FUTURE, "08:00", 30)[0])
        self.assertFalse(self.book(3, "LAB2", FUTURE, "15:30", 60)[0])

    def test_past_date_rejected(self):
        self.assertFalse(self.book(1, "LAB1", "2020-01-01", "10:00", 30)[0])

    def test_resource_must_belong_to_campus(self):
        self.assertFalse(self.book(1, "LAB2", FUTURE, "10:00", 30)[0])

    def test_only_lecturers_can_book(self):
        self.assertFalse(self.book(1, "LAB1", FUTURE, "10:00", 30, 2)[0])

    def test_invalid_input_rejected(self):
        self.assertFalse(self.book(1, "LAB1", "not-a-date", "10:00", 30)[0])
        self.assertFalse(self.book(1, "LAB1", FUTURE, "25:99", 30)[0])
        self.assertFalse(self.book(1, "LAB1", FUTURE, "10:00", 0)[0])

    def test_times_are_stored_zero_padded(self):
        self.book(1, "LAB1", FUTURE, "9:15", 30)
        with sqlite3.connect(self.path) as connection:
            stored = connection.execute(
                "SELECT start_time FROM bookings").fetchone()[0]
        self.assertEqual(stored, "09:15")

    def test_cancelled_booking_frees_the_slot(self):
        self.book(1, "LAB1", FUTURE, "10:00", 60)
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE bookings SET status='cancelled'")
        self.assertTrue(self.book(1, "LAB1", FUTURE, "10:00", 60)[0])

    def test_availability_lists_booked_and_free_slots(self):
        self.book(1, "LAB1", FUTURE, "10:00", 60)
        segments, message = self.service.get_availability("LAB1", FUTURE)
        self.assertEqual(message, "")
        self.assertEqual(segments, [
            ("08:00", "10:00", "Available"),
            ("10:00", "11:00", "Booked"),
            ("11:00", "17:00", "Available"),
        ])

    def test_availability_with_bad_date_gives_message(self):
        segments, message = self.service.get_availability("LAB1", "xx")
        self.assertIsNone(segments)
        self.assertTrue(message)

    def test_policy_text_names_the_campus_rules(self):
        text = self.service.get_policy(3).describe()
        self.assertIn("Cape Town", text)
        self.assertIn("60", text)
        self.assertIn("09:00", text)


class ReportQueryTests(unittest.TestCase):

    def setUp(self):
        handle, self.path = tempfile.mkstemp(suffix=".db")
        os.close(handle)
        campus_booking_system.DATABASE_FILE = self.path
        campus_booking_system.create_tables()
        campus_booking_system.add_sample_campuses()

        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO users (full_name, username, password_hash,"
                " role, campus_id) VALUES ('L', 'l', 'x', 'lecturer', 1)")
            connection.executemany(
                "INSERT INTO resources VALUES (?, ?, ?, ?)",
                [("A1", "Room A", "Room", 1), ("C1", "Room C", "Room", 3)])

            connection.executemany(
                "INSERT INTO bookings (resource_id, lecturer_id, campus_id,"
                " booking_date, start_time, duration_minutes, status)"
                " VALUES (?, 1, ?, ?, ?, ?, ?)",
                [("A1", 1, "2026-11-02", "10:00", 60, "active"),
                 ("A1", 1, "2026-11-03", "10:00", 120, "active"),
                 ("A1", 1, "2026-11-03", "13:00", 60, "cancelled"),
                 ("C1", 3, "2026-11-02", "10:00", 30, "active"),
                 ("C1", 3, "2026-12-01", "10:00", 60, "active")])

    def tearDown(self):
        os.remove(self.path)

    def test_all_bookings_includes_every_campus(self):
        with sqlite3.connect(self.path) as connection:
            rows = fetch_all_bookings(connection)
        self.assertEqual(len(rows), 5)
        self.assertEqual({row[1] for row in rows},
                         {"Durban Campus", "Cape Town Campus"})

    def test_all_bookings_can_filter_by_campus(self):
        with sqlite3.connect(self.path) as connection:
            rows = fetch_all_bookings(connection, 3)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r[1] == "Cape Town Campus" for r in rows))

    def test_monthly_trends_counts_and_percent_of_max(self):
        with sqlite3.connect(self.path) as connection:
            rows = fetch_monthly_trends(connection)
        durban_nov = next(r for r in rows
                          if r[0] == "Durban Campus" and r[1] == "2026-11")

        self.assertEqual(durban_nov[2:4], (2, 1))
        self.assertAlmostEqual(durban_nov[4], 90)
        self.assertAlmostEqual(durban_nov[5], 75)
        ct_dec = next(r for r in rows
                      if r[0] == "Cape Town Campus" and r[1] == "2026-12")
        self.assertAlmostEqual(ct_dec[5], 100)

    def test_trends_can_be_limited_to_one_campus(self):
        with sqlite3.connect(self.path) as connection:
            rows = fetch_monthly_trends(connection, 1)
        self.assertEqual({r[0] for r in rows}, {"Durban Campus"})

    def test_weekday_usage_ignores_cancelled_bookings(self):
        with sqlite3.connect(self.path) as connection:
            rows = fetch_weekday_usage(connection, 1)

        self.assertEqual(set(rows), {("Durban Campus", "Monday", 1),
                                     ("Durban Campus", "Tuesday", 1)})

    def test_weekday_usage_sorted_busiest_first(self):
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "INSERT INTO bookings (resource_id, lecturer_id, campus_id,"
                " booking_date, start_time, duration_minutes, status)"
                " VALUES ('A1', 1, 1, '2026-11-10', '09:00', 30, 'active')")
            rows = fetch_weekday_usage(connection, 1)
        self.assertEqual(rows[0], ("Durban Campus", "Tuesday", 2))


if __name__ == "__main__":
    unittest.main()
