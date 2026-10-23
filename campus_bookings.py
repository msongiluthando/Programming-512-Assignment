import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class CampusBookingsWindow:

    def __init__(self, parent, user):
        if getattr(user, "role", None) != "administrator":
            messagebox.showerror(
                "Access Denied",
                "Only campus administrators can view this screen.",
                parent=parent,
            )
            return

        self.user = user
        self.window = tk.Toplevel(parent)
        self.window.title("Bookings for My Campus")
        self.window.geometry("1050x540")
        self.window.minsize(800, 400)

        ttk.Label(
            self.window,
            text="Bookings for My Campus",
            font=("Arial", 16, "bold"),
        ).pack(pady=(12, 4))
        self.campus_label = ttk.Label(self.window, text="")
        self.campus_label.pack(pady=(0, 8))

        columns = (
            "booking_id", "lecturer", "resource", "date", "time",
            "duration", "status",
        )
        frame = ttk.Frame(self.window, padding=10)
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        headings = {
            "booking_id": "Booking ID", "lecturer": "Lecturer",
            "resource": "Resource", "date": "Date", "time": "Start Time",
            "duration": "Duration (min)", "status": "Status",
        }
        widths = {
            "booking_id": 85, "lecturer": 190, "resource": 190,
            "date": 115, "time": 100, "duration": 120, "status": 100,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Button(
            self.window, text="Refresh Bookings", command=self.load_bookings
        ).pack(pady=(0, 12))
        self.load_bookings()

    def load_bookings(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            with sqlite3.connect(DATABASE_FILE) as connection:
                campus = connection.execute(
                    "SELECT campus_name FROM campuses WHERE campus_id = ?",
                    (self.user.campus_id,),
                ).fetchone()
                if campus is None:
                    messagebox.showerror(
                        "Campus Error", "Your assigned campus was not found.",
                        parent=self.window,
                    )
                    self.window.destroy()
                    return
                self.campus_label.config(text=f"Active campus: {campus[0]}")
                rows = connection.execute(
                    """SELECT b.booking_id, u.full_name, r.resource_name,
                              b.booking_date, b.start_time,
                              b.duration_minutes, b.status
                       FROM bookings b
                       JOIN users u ON u.user_id = b.lecturer_id
                       JOIN resources r ON r.resource_id = b.resource_id
                       WHERE b.campus_id = ?
                       ORDER BY b.booking_date DESC, b.start_time DESC""",
                    (self.user.campus_id,),
                ).fetchall()
            for row in rows:
                self.tree.insert("", "end", values=row)
        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error", f"Could not load campus bookings: {error}",
                parent=self.window,
            )
