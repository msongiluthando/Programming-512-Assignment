import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class ReportsWindow:
    def __init__(self, parent, user):
        self.user = user

        self.window = tk.Toplevel(parent)
        self.window.title("Campus Reports and Management Information")
        self.window.geometry("1050x650")
        self.window.minsize(800, 500)

        ttk.Label(
            self.window,
            text="Campus Reports and Management Information",
            font=("Arial", 16, "bold")
        ).pack(pady=12)

        self.access_label = ttk.Label(self.window)
        self.access_label.pack(pady=3)

        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=10)

        self.summary_tab = ttk.Frame(self.notebook)
        self.resources_tab = ttk.Frame(self.notebook)

        self.notebook.add(
            self.summary_tab, text="Campus Comparison"
        )
        self.notebook.add(
            self.resources_tab, text="Resource Usage"
        )

        self.summary_tree = self.make_tree(
            self.summary_tab,
            (
                "campus", "total", "active",
                "cancelled", "average"
            ),
            (
                "Campus", "Total Bookings", "Active",
                "Cancelled", "Average Duration (min)"
            )
        )

        self.resource_tree = self.make_tree(
            self.resources_tab,
            (
                "campus", "resource_id", "resource",
                "total", "average"
            ),
            (
                "Campus", "Resource ID", "Resource",
                "Active Bookings", "Average Duration (min)"
            )
        )

        ttk.Button(
            self.window,
            text="Refresh Reports",
            command=self.load_reports
        ).pack(pady=(0, 12))

        self.load_reports()

    def connect_database(self):
        connection = sqlite3.connect(DATABASE_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def make_tree(self, parent, columns, headings):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=8, pady=8)

        tree = ttk.Treeview(
            frame,
            columns=columns,
            show="headings"
        )

        for column, heading in zip(columns, headings):
            tree.heading(column, text=heading)
            tree.column(column, width=150, anchor="center")

        scrollbar = ttk.Scrollbar(
            frame, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return tree

    def load_reports(self):
        for tree in (self.summary_tree, self.resource_tree):
            for item in tree.get_children():
                tree.delete(item)

        try:
            with self.connect_database() as connection:

                # Restrict campus administrators to their own campus.
                if self.user.role == "administrator":
                    campus_filter = "WHERE c.campus_id = ?"
                    params = (self.user.campus_id,)
                    self.access_label.config(
                        text="Report access: Assigned campus only"
                    )
                elif self.user.role == "operator":
                    campus_filter = ""
                    params = ()
                    self.access_label.config(
                        text="Report access: All campuses"
                    )
                else:
                    messagebox.showerror(
                        "Access Denied",
                        "Only administrators and system operators "
                        "can access management reports.",
                        parent=self.window
                    )
                    self.window.destroy()
                    return

                summary_sql = f"""
                    SELECT
                        c.campus_name,
                        COUNT(b.booking_id),
                        COALESCE(SUM(
                            CASE WHEN b.status = 'active'
                            THEN 1 ELSE 0 END
                        ), 0),
                        COALESCE(SUM(
                            CASE WHEN b.status = 'cancelled'
                            THEN 1 ELSE 0 END
                        ), 0),
                        AVG(
                            CASE WHEN b.status = 'active'
                            THEN b.duration_minutes END
                        )
                    FROM campuses c
                    LEFT JOIN bookings b
                        ON c.campus_id = b.campus_id
                    {campus_filter}
                    GROUP BY c.campus_id, c.campus_name
                    ORDER BY c.campus_name
                """

                summary_rows = connection.execute(
                    summary_sql, params
                ).fetchall()

                resource_sql = f"""
                    SELECT
                        c.campus_name,
                        r.resource_id,
                        r.resource_name,
                        COUNT(b.booking_id),
                        AVG(b.duration_minutes)
                    FROM campuses c
                    JOIN resources r
                        ON r.campus_id = c.campus_id
                    LEFT JOIN bookings b
                        ON b.resource_id = r.resource_id
                        AND b.status = 'active'
                    {campus_filter}
                    GROUP BY
                        c.campus_id,
                        r.resource_id,
                        r.resource_name
                    ORDER BY
                        c.campus_name,
                        COUNT(b.booking_id) DESC,
                        r.resource_name
                """

                resource_rows = connection.execute(
                    resource_sql, params
                ).fetchall()

            for row in summary_rows:
                average = (
                    f"{row[4]:.1f}" if row[4] is not None
                    else "N/A"
                )

                self.summary_tree.insert(
                    "", "end",
                    values=(
                        row[0], row[1], row[2], row[3], average
                    )
                )

            for row in resource_rows:
                average = (
                    f"{row[4]:.1f}" if row[4] is not None
                    else "N/A"
                )

                self.resource_tree.insert(
                    "", "end",
                    values=(
                        row[0], row[1], row[2], row[3], average
                    )
                )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Report Error",
                f"Could not generate reports:\n{error}",
                parent=self.window
            )
