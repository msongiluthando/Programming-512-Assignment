
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class BookingHistoryWindow:
    def __init__(self, parent, user):
        self.user = user

        self.window = tk.Toplevel(parent)
        self.window.title("My Booking History")
        self.window.geometry("950x500")
        self.window.minsize(750, 400)

        ttk.Label(
            self.window,
            text="My Bookings and History",
            font=("Arial", 16, "bold")
        ).pack(pady=12)

        columns = (
            "booking_id", "resource", "campus",
            "date", "time", "duration", "status"
        )

        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings",
            height=14
        )

        headings = {
            "booking_id": "Booking ID",
            "resource": "Resource",
            "campus": "Campus",
            "date": "Date",
            "time": "Start Time",
            "duration": "Duration (min)",
            "status": "Status"
        }

        for column, heading in headings.items():
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=115, anchor="center")

        self.tree.column("booking_id", width=80)
        self.tree.pack(fill="both", expand=True, padx=12, pady=8)

        buttons = ttk.Frame(self.window)
        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Refresh Bookings",
            command=self.load_bookings
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Cancel Selected Future Booking",
            command=self.cancel_booking
        ).pack(side="left", padx=5)

        self.load_bookings()

    def connect_database(self):
        connection = sqlite3.connect(DATABASE_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def load_bookings(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with self.connect_database() as connection:
                rows = connection.execute("""
                    SELECT
                        b.booking_id,
                        r.resource_name,
                        c.campus_name,
                        b.booking_date,
                        b.start_time,
                        b.duration_minutes,
                        b.status
                    FROM bookings b
                    JOIN resources r
                        ON b.resource_id = r.resource_id
                    JOIN campuses c
                        ON b.campus_id = c.campus_id
                    WHERE b.lecturer_id = ?
                    ORDER BY b.booking_date DESC, b.start_time DESC
                """, (self.user.user_id,)).fetchall()

            for row in rows:
                self.tree.insert("", "end", values=row)

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load bookings: {error}",
                parent=self.window
            )

    def cancel_booking(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Booking",
                "Select a booking from the table first.",
                parent=self.window
            )
            return

        values = self.tree.item(selected[0], "values")

        booking_id = int(values[0])
        booking_date = values[3]
        start_time = values[4]
        status = values[6]

        if status != "active":
            messagebox.showwarning(
                "Cannot Cancel",
                "Only active bookings can be cancelled.",
                parent=self.window
            )
            return

        try:
            booking_start = datetime.strptime(
                f"{booking_date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:
            messagebox.showerror(
                "Invalid Booking",
                "The saved booking date or time is invalid.",
                parent=self.window
            )
            return

        if booking_start <= datetime.now():
            messagebox.showwarning(
                "Cannot Cancel",
                "Only future bookings can be cancelled.",
                parent=self.window
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Cancellation",
            "Are you sure you want to cancel this future booking?",
            parent=self.window
        )

        if not confirmed:
            return

        try:
            with self.connect_database() as connection:
                cursor = connection.execute("""
                    UPDATE bookings
                    SET status = 'cancelled'
                    WHERE booking_id = ?
                      AND lecturer_id = ?
                      AND status = 'active'
                      AND (booking_date || ' ' || start_time) > ?
                """, (
                    booking_id,
                    self.user.user_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ))

            if cursor.rowcount == 1:
                messagebox.showinfo(
                    "Success",
                    "Booking cancelled successfully.",
                    parent=self.window
                )
                self.load_bookings()
            else:
                messagebox.showwarning(
                    "Cancellation Failed",
                    "The booking may have started, been cancelled, "
                    "or changed. Refresh and check its status.",
                    parent=self.window
                )
                self.load_bookings()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not cancel booking: {error}",
                parent=self.window
            )
