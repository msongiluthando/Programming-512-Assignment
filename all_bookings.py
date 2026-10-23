import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from report_queries import fetch_all_bookings

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"

ALL_CAMPUSES = "All campuses"


class AllBookingsWindow:

    def __init__(self, parent, user, initial_campus_id=None):
        if getattr(user, "role", None) != "operator":
            messagebox.showerror(
                "Access Denied",
                "Only system operators can view bookings "
                "across all campuses.",
                parent=parent,
            )
            return

        self.user = user
        self.initial_campus_id = initial_campus_id
        self.campus_map = {}

        self.window = tk.Toplevel(parent)
        self.window.title("All Campus Bookings")
        self.window.geometry("1150x560")
        self.window.minsize(900, 420)

        ttk.Label(
            self.window,
            text="Bookings Across All Campuses",
            font=("Arial", 16, "bold"),
        ).pack(pady=(12, 4))

        self.summary_label = ttk.Label(self.window, text="")
        self.summary_label.pack(pady=(0, 6))

        filter_frame = ttk.Frame(self.window, padding=(10, 0))
        filter_frame.pack(fill="x")
        ttk.Label(filter_frame, text="Show campus:").pack(
            side="left", padx=(0, 8)
        )
        self.campus_filter = ttk.Combobox(
            filter_frame, state="readonly", width=30
        )
        self.campus_filter.pack(side="left")
        self.campus_filter.bind(
            "<<ComboboxSelected>>", self.load_bookings
        )

        columns = (
            "booking_id", "campus", "lecturer", "resource",
            "date", "time", "duration", "status",
        )
        headings = {
            "booking_id": "Booking ID", "campus": "Campus",
            "lecturer": "Lecturer", "resource": "Resource",
            "date": "Date", "time": "Start Time",
            "duration": "Duration (min)", "status": "Status",
        }
        widths = {
            "booking_id": 80, "campus": 160, "lecturer": 160,
            "resource": 180, "date": 100, "time": 90,
            "duration": 110, "status": 90,
        }

        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(column, width=widths[column], anchor="center")
        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(
            self.window, text="Refresh Bookings",
            command=self.load_campuses
        ).pack(pady=(0, 12))

        self.load_campuses()

    def load_campuses(self):
        try:
            with sqlite3.connect(DATABASE_FILE) as connection:
                rows = connection.execute("""
                    SELECT campus_id, campus_name
                    FROM campuses ORDER BY campus_name
                """).fetchall()
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not load campuses: {error}",
                parent=self.window,
            )
            return

        self.campus_map = {name: campus_id for campus_id, name in rows}
        self.campus_filter["values"] = [ALL_CAMPUSES] + list(
            self.campus_map.keys()
        )
        if self.campus_filter.get() not in self.campus_filter["values"]:
            # Start on the campus chosen at login, or on all campuses.
            initial_name = next(
                (
                    name for name, campus_id in self.campus_map.items()
                    if campus_id == self.initial_campus_id
                ),
                ALL_CAMPUSES
            )
            self.campus_filter.set(initial_name)

        self.load_bookings()

    def load_bookings(self, event=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        selected = self.campus_filter.get()
        campus_id = self.campus_map.get(selected)

        try:
            with sqlite3.connect(DATABASE_FILE) as connection:
                rows = fetch_all_bookings(connection, campus_id)
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not load bookings: {error}",
                parent=self.window,
            )
            return

        for row in rows:
            self.tree.insert("", "end", values=row)

        active = sum(1 for row in rows if row[7] == "active")
        self.summary_label.config(
            text=(
                f"Showing: {selected or ALL_CAMPUSES}  |  "
                f"{len(rows)} bookings ({active} active, "
                f"{len(rows) - active} cancelled)"
            )
        )
