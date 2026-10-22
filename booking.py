import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import date

from booking_management import BookingService

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class BookingWindow:
    def __init__(self, parent, user):
        self.user = user
        self.booking_service = BookingService()

        self.window = tk.Toplevel(parent)
        self.window.title("Smart Campus - Resource Booking")
        self.window.geometry("760x570")
        self.window.minsize(650, 500)

        self.campus_map = {}
        self.resource_map = {}

        self.build_interface()
        self.load_campuses()

    def connect_database(self):
        connection = sqlite3.connect(DATABASE_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def build_interface(self):
        main = ttk.Frame(self.window, padding=15)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Create a Resource Booking",
            font=("Arial", 16, "bold")
        ).pack(pady=(0, 12))

        form = ttk.Frame(main)
        form.pack(fill="x")

        ttk.Label(form, text="Campus:").grid(
            row=0, column=0, sticky="w", pady=6
        )
        self.campus_combo = ttk.Combobox(
            form, state="readonly", width=35
        )
        self.campus_combo.grid(
            row=0, column=1, sticky="ew", pady=6
        )
        self.campus_combo.bind(
            "<<ComboboxSelected>>", self.on_campus_changed
        )

        ttk.Label(form, text="Resource:").grid(
            row=1, column=0, sticky="w", pady=6
        )
        self.resource_combo = ttk.Combobox(
            form, state="readonly", width=35
        )
        self.resource_combo.grid(
            row=1, column=1, sticky="ew", pady=6
        )

        ttk.Label(form, text="Booking date (YYYY-MM-DD):").grid(
            row=2, column=0, sticky="w", pady=6
        )
        self.date_entry = ttk.Entry(form, width=38)
        self.date_entry.grid(
            row=2, column=1, sticky="ew", pady=6
        )
        self.date_entry.insert(0, date.today().isoformat())

        ttk.Label(form, text="Start time (HH:MM):").grid(
            row=3, column=0, sticky="w", pady=6
        )
        self.time_entry = ttk.Entry(form, width=38)
        self.time_entry.grid(
            row=3, column=1, sticky="ew", pady=6
        )
        self.time_entry.insert(0, "10:00")

        ttk.Label(form, text="Duration (minutes):").grid(
            row=4, column=0, sticky="w", pady=6
        )
        self.duration_entry = ttk.Entry(form, width=38)
        self.duration_entry.grid(
            row=4, column=1, sticky="ew", pady=6
        )
        self.duration_entry.insert(0, "60")

        form.columnconfigure(1, weight=1)

        ttk.Label(
            main,
            text=(
                "Campus opening hours and maximum duration "
                "are checked automatically."
            ),
            wraplength=650
        ).pack(anchor="w", pady=12)

        ttk.Button(
            main,
            text="Create Booking",
            command=self.create_booking
        ).pack(pady=6)

        ttk.Button(
            main,
            text="Refresh Campuses and Resources",
            command=self.load_campuses
        ).pack(pady=4)

    def load_campuses(self):
        try:
            with self.connect_database() as connection:
                rows = connection.execute("""
                    SELECT campus_id, campus_name
                    FROM campuses
                    ORDER BY campus_id
                """).fetchall()

            self.campus_map = {
                name: campus_id for campus_id, name in rows
            }
            names = [name for _, name in rows]
            self.campus_combo["values"] = names

            if names:
                current = self.campus_combo.get()
                if current not in names:
                    self.campus_combo.set(names[0])
                self.load_resources()
            else:
                self.campus_combo.set("")
                self.resource_combo["values"] = []
                self.resource_combo.set("")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", str(error), parent=self.window
            )

    def on_campus_changed(self, event=None):
        self.load_resources()

    def load_resources(self):
        campus_name = self.campus_combo.get()
        campus_id = self.campus_map.get(campus_name)

        self.resource_map = {}

        if campus_id is None:
            self.resource_combo["values"] = []
            self.resource_combo.set("")
            return

        try:
            with self.connect_database() as connection:
                rows = connection.execute("""
                    SELECT resource_id, resource_name
                    FROM resources
                    WHERE campus_id = ?
                    ORDER BY resource_name
                """, (campus_id,)).fetchall()

            self.resource_map = {
                f"{resource_id} - {name}": resource_id
                for resource_id, name in rows
            }
            names = list(self.resource_map.keys())
            self.resource_combo["values"] = names

            if names:
                self.resource_combo.current(0)
            else:
                self.resource_combo.set("")

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", str(error), parent=self.window
            )

    def create_booking(self):
        campus_name = self.campus_combo.get()
        campus_id = self.campus_map.get(campus_name)
        resource_id = self.resource_map.get(
            self.resource_combo.get()
        )

        if campus_id is None:
            messagebox.showwarning(
                "Select Campus", "Please select a campus.",
                parent=self.window
            )
            return

        if resource_id is None:
            messagebox.showwarning(
                "Select Resource",
                "Please select a resource for this campus.",
                parent=self.window
            )
            return

        try:
            duration = int(self.duration_entry.get().strip())
        except ValueError:
            messagebox.showwarning(
                "Invalid Duration",
                "Enter duration as a whole number of minutes.",
                parent=self.window
            )
            return

        success, message = self.booking_service.create_booking(
            lecturer_id=self.user.user_id,
            campus_id=campus_id,
            resource_id=resource_id,
            booking_date=self.date_entry.get().strip(),
            start_time=self.time_entry.get().strip(),
            duration_minutes=duration
        )

        if success:
            messagebox.showinfo(
                "Booking Successful", message, parent=self.window
            )
        else:
            messagebox.showerror(
                "Booking Rejected", message, parent=self.window
            )
