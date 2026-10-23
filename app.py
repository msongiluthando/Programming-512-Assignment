import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from resource_management import ResourceManagerWindow
from booking import BookingWindow
from booking_history import BookingHistoryWindow
from reports import ReportsWindow
from campus_bookings import CampusBookingsWindow

from campus_booking_system import (
    create_tables,
    add_sample_campuses
)

from users import (
    Lecturer,
    CampusAdministrator,
    SystemOperator,
    hash_password
)



DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class CampusBookingApp:


    def open_resource_manager(self):
        ResourceManagerWindow(self.root, self.current_user)

    def open_reports_window(self):
        if self.current_user.role not in ("administrator", "operator"):
            messagebox.showerror(
                "Access Denied",
                "Only administrators and system operators "
                "can access reports."
            )
            return

        ReportsWindow(self.root, self.current_user)

    def open_booking_history(self):
        """Open the signed-in lecturer's booking history."""
        if self.current_user.role != "lecturer":
            messagebox.showinfo(
                "Lecturer Access Only",
                "Booking history is available to lecturers."
            )
            return

        BookingHistoryWindow(self.root, self.current_user)

    def open_campus_bookings(self):
        """Open the administrator's campus-scoped booking list."""
        if self.current_user.role != "administrator":
            messagebox.showerror(
                "Access Denied",
                "Only campus administrators can view campus bookings."
            )
            return
        CampusBookingsWindow(self.root, self.current_user)

    def open_booking_window(self):
        """Open the booking window for the signed-in user."""
        if self.current_user.role != "lecturer":
            messagebox.showinfo(
                "Lecturer Access Only",
                "Only lecturers can create resource bookings."
            )
            return
        BookingWindow(self.root, self.current_user)

    def __init__(self, root):
        self.root = root
        self.root.title("Smart Campus Resource Booking System")
        self.root.geometry("650x500")
        self.root.minsize(550, 420)

        self.current_user = None
        self.campus_map = {}

        self.setup_database()
        self.show_login()

    def connect_database(self):
        """Open a database connection with foreign keys enabled."""
        connection = sqlite3.connect(DATABASE_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def setup_database(self):
        """Prepare the tables and initial campus records."""
        create_tables()
        add_sample_campuses()

    def clear_window(self):
        """Remove the current screen's widgets."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def get_campuses(self):
        """Return campus IDs and names from the database."""
        with self.connect_database() as connection:
            return connection.execute("""
                SELECT campus_id, campus_name
                FROM campuses
                ORDER BY campus_name
            """).fetchall()

    def make_heading(self, heading, subtitle):
        """Display a consistent heading on each screen."""
        ttk.Label(
            self.root,
            text=heading,
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 5))

        ttk.Label(
            self.root,
            text=subtitle,
            font=("Arial", 10)
        ).pack(pady=(0, 15))

    def show_login(self):
        """Display the login screen."""
        self.clear_window()
        self.make_heading(
            "Smart Campus Resource Booking System",
            "Log in using your registered account"
        )

        form = ttk.Frame(self.root, padding=20)
        form.pack()

        ttk.Label(form, text="Username:").grid(
            row=0, column=0, sticky="w", pady=8
        )
        self.login_username = ttk.Entry(form, width=32)
        self.login_username.grid(row=0, column=1, pady=8)

        ttk.Label(form, text="Password:").grid(
            row=1, column=0, sticky="w", pady=8
        )
        self.login_password = ttk.Entry(
            form, width=32, show="*"
        )
        self.login_password.grid(row=1, column=1, pady=8)

        ttk.Button(
            form,
            text="Log In",
            command=self.login
        ).grid(row=2, column=0, columnspan=2, pady=15)

        ttk.Button(
            form,
            text="Register as a Lecturer",
            command=self.show_registration
        ).grid(row=3, column=0, columnspan=2, pady=5)

        self.login_username.focus_set()

    def show_registration(self):
        """Display the lecturer registration form."""
        self.clear_window()
        self.make_heading(
            "Create a Lecturer Account",
            "Complete all fields to register"
        )

        campuses = self.get_campuses()
        self.campus_map = {
            name: campus_id for campus_id, name in campuses
        }

        form = ttk.Frame(self.root, padding=20)
        form.pack()

        ttk.Label(form, text="Full name:").grid(
            row=0, column=0, sticky="w", pady=7
        )
        self.reg_name = ttk.Entry(form, width=32)
        self.reg_name.grid(row=0, column=1, pady=7)

        ttk.Label(form, text="Username:").grid(
            row=1, column=0, sticky="w", pady=7
        )
        self.reg_username = ttk.Entry(form, width=32)
        self.reg_username.grid(row=1, column=1, pady=7)

        ttk.Label(form, text="Password:").grid(
            row=2, column=0, sticky="w", pady=7
        )
        self.reg_password = ttk.Entry(
            form, width=32, show="*"
        )
        self.reg_password.grid(row=2, column=1, pady=7)

        ttk.Label(form, text="Confirm password:").grid(
            row=3, column=0, sticky="w", pady=7
        )
        self.reg_confirm = ttk.Entry(
            form, width=32, show="*"
        )
        self.reg_confirm.grid(row=3, column=1, pady=7)

        ttk.Label(form, text="Home campus:").grid(
            row=4, column=0, sticky="w", pady=7
        )

        self.reg_campus = ttk.Combobox(
            form,
            values=list(self.campus_map.keys()),
            state="readonly",
            width=29
        )
        self.reg_campus.grid(row=4, column=1, pady=7)

        if self.campus_map:
            self.reg_campus.current(0)

        ttk.Button(
            form,
            text="Create Account",
            command=self.register
        ).grid(row=5, column=0, columnspan=2, pady=15)

        ttk.Button(
            form,
            text="Back to Login",
            command=self.show_login
        ).grid(row=6, column=0, columnspan=2)

    def register(self):
        """Validate and save a new lecturer account."""
        full_name = self.reg_name.get().strip()
        username = self.reg_username.get().strip().lower()
        password = self.reg_password.get()
        confirmation = self.reg_confirm.get()
        campus_name = self.reg_campus.get()

        if not all([
            full_name, username, password,
            confirmation, campus_name
        ]):
            messagebox.showerror(
                "Missing Information",
                "Please complete every field."
            )
            return

        if len(username) < 3 or " " in username:
            messagebox.showerror(
                "Invalid Username",
                "Use at least 3 characters with no spaces."
            )
            return

        if len(password) < 8:
            messagebox.showerror(
                "Weak Password",
                "Your password must contain at least 8 characters."
            )
            return

        if password != confirmation:
            messagebox.showerror(
                "Password Mismatch",
                "The two passwords do not match."
            )
            return

        campus_id = self.campus_map.get(campus_name)
        if campus_id is None:
            messagebox.showerror(
                "Invalid Campus",
                "Please select a valid campus."
            )
            return

        password_hash = hash_password(password)

        try:
            with self.connect_database() as connection:
                connection.execute("""
                    INSERT INTO users
                    (full_name, username, password_hash,
                     role, campus_id)
                    VALUES (?, ?, ?, 'lecturer', ?)
                """, (
                    full_name,
                    username,
                    password_hash,
                    campus_id
                ))

            messagebox.showinfo(
                "Registration Successful",
                "Your lecturer account has been created. "
                "You can now log in."
            )
            self.show_login()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Registration Failed",
                "That username is already registered, "
                "or the supplied information is invalid."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not save the account: {error}"
            )

    def login(self):
        """Authenticate a user and open their role-specific screen."""
        username = self.login_username.get().strip().lower()
        password = self.login_password.get()

        if not username or not password:
            messagebox.showerror(
                "Missing Information",
                "Enter your username and password."
            )
            return

        try:
            with self.connect_database() as connection:
                row = connection.execute("""
                    SELECT user_id, full_name, username,
                           password_hash, role, campus_id
                    FROM users
                    WHERE username = ?
                """, (username,)).fetchone()

        except sqlite3.Error:
            messagebox.showerror(
                "Database Error",
                "Could not access the user database."
            )
            return

        from users import verify_password

        if row is None or not verify_password(password, row[3]):
            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )
            return

        user_id, full_name, saved_username, saved_hash, role, campus_id = row

        user_classes = {
            "lecturer": Lecturer,
            "administrator": CampusAdministrator,
            "operator": SystemOperator
        }

        user_class = user_classes.get(role)

        if user_class is None:
            messagebox.showerror(
                "Access Denied",
                "This account has an unrecognised role."
            )
            return

        self.current_user = user_class(
            full_name,
            saved_username,
            saved_hash,
            campus_id,
            user_id
        )

        self.current_user_id = user_id

        self.show_dashboard()

    def show_dashboard(self):
        """Display a dashboard based on the authenticated role."""
        self.clear_window()

        user = self.current_user
        role_titles = {
            "lecturer": "Lecturer Dashboard",
            "administrator": "Campus Administrator Dashboard",
            "operator": "System Operator Dashboard"
        }


        self.make_heading(
            role_titles[user.role],
            f"Welcome, {user.full_name}"
        )

        campus_name = "All campuses"

        if user.campus_id is not None:
            with self.connect_database() as connection:
                row = connection.execute("""
                    SELECT campus_name
                    FROM campuses
                    WHERE campus_id = ?
                """, (user.campus_id,)).fetchone()

            if row:
                campus_name = row[0]

        ttk.Label(
            self.root,
            text=f"Home campus: {campus_name}"
        ).pack(pady=5)

        ttk.Label(
            self.root,
            text=f"Signed-in role: {user.role.title()}"
        ).pack(pady=5)

        ttk.Label(
            self.root,
            text="Your permissions:"
        ).pack(pady=(15, 5))

        for permission in user.get_permissions():
            ttk.Label(
                self.root,
                text=f"• {permission.replace('_', ' ').title()}"
            ).pack(anchor="center", pady=2)

        ttk.Label(
            self.root,
            text=(
                "Use the options below to manage resources, make bookings, "
                "review booking records, and view reports allowed for your role."
            ),
            wraplength=520
        ).pack(pady=14)

        ttk.Button(
            self.root,
            text="View Campus Resources",
            command=self.open_resource_manager
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="Create Resource Booking",
            command=self.open_booking_window
        ).pack(pady=5)

        if user.role == "administrator":
            ttk.Button(
                self.root,
                text="View All Bookings for My Campus",
                command=self.open_campus_bookings
            ).pack(pady=5)

        ttk.Button(
            self.root,
            text="View My Bookings and History",
            command=self.open_booking_history
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="Campus Reports",
            command=self.open_reports_window
        ).pack(pady=5)

        ttk.Button(
            self.root,
            text="Log Out",
            command=self.logout
        ).pack(pady=10)


    def logout(self):
        self.current_user = None
        self.show_login()


if __name__ == "__main__":
    root = tk.Tk()
    app = CampusBookingApp(root)
    root.mainloop()
