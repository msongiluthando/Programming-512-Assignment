import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


DATABASE_FILE = Path(__file__).resolve().parent / "campus_booking.db"


class ResourceManagerWindow:

    def __init__(self, parent, user, active_campus_id=None):
        self.user = user
        self.active_campus_id = active_campus_id
        self.window = tk.Toplevel(parent)
        self.window.title("Campus Resource Management")
        self.window.geometry("850x560")
        self.window.minsize(700, 450)

        self.can_manage = user.role == "administrator"

        self.campus_map = {}
        self.selected_resource_id = None

        self.build_interface()
        self.load_campuses()

    def connect_database(self):
        connection = sqlite3.connect(DATABASE_FILE)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def build_interface(self):
        ttk.Label(
            self.window,
            text="Campus Resource Management",
            font=("Arial", 17, "bold")
        ).pack(pady=(15, 5))

        self.active_campus_label = ttk.Label(
            self.window,
            text="Active campus: Loading..."
        )
        self.active_campus_label.pack(pady=5)

        campus_frame = ttk.Frame(self.window, padding=10)
        campus_frame.pack(fill="x")

        ttk.Label(
            campus_frame,
            text="Select campus:"
        ).pack(side="left", padx=(0, 8))

        self.campus_selector = ttk.Combobox(
            campus_frame,
            state="readonly",
            width=30
        )
        self.campus_selector.pack(side="left")
        self.campus_selector.bind(
            "<<ComboboxSelected>>",
            self.on_campus_changed
        )

        columns = ("resource_id", "resource_name", "resource_type")
        self.tree = ttk.Treeview(
            self.window,
            columns=columns,
            show="headings",
            height=12
        )

        self.tree.heading("resource_id", text="Resource ID")
        self.tree.heading("resource_name", text="Resource Name")
        self.tree.heading("resource_type", text="Resource Type")

        self.tree.column("resource_id", width=150)
        self.tree.column("resource_name", width=280)
        self.tree.column("resource_type", width=220)

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=10
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.on_resource_selected
        )

        form = ttk.LabelFrame(
            self.window,
            text="Resource Details",
            padding=10
        )
        form.pack(fill="x", padx=15, pady=5)

        ttk.Label(form, text="Resource ID:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.resource_id_entry = ttk.Entry(form, width=25)
        self.resource_id_entry.grid(
            row=0, column=1, padx=5, pady=5
        )

        ttk.Label(form, text="Resource Name:").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.resource_name_entry = ttk.Entry(form, width=25)
        self.resource_name_entry.grid(
            row=0, column=3, padx=5, pady=5
        )

        ttk.Label(form, text="Resource Type:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.resource_type_entry = ttk.Entry(form, width=25)
        self.resource_type_entry.grid(
            row=1, column=1, padx=5, pady=5
        )

        buttons = ttk.Frame(self.window, padding=10)
        buttons.pack()

        if self.can_manage:
            ttk.Button(
                buttons,
                text="Add Resource",
                command=self.add_resource
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons,
                text="Update Selected",
                command=self.update_resource
            ).pack(side="left", padx=5)

            ttk.Button(
                buttons,
                text="Remove Selected",
                command=self.remove_resource
            ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Refresh",
            command=self.load_resources
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Clear Fields",
            command=self.clear_fields
        ).pack(side="left", padx=5)

        if not self.can_manage:
            ttk.Label(
                self.window,
                text="View-only access: resource changes are disabled."
            ).pack(pady=(0, 10))

    def load_campuses(self):
        try:
            with self.connect_database() as connection:
                rows = connection.execute("""
                    SELECT campus_id, campus_name
                    FROM campuses
                    ORDER BY campus_name
                """).fetchall()

            self.campus_map = {
                name: campus_id for campus_id, name in rows
            }

            self.campus_selector["values"] = list(
                self.campus_map.keys()
            )

            if self.user.role == "administrator":
                assigned = next(
                    (
                        name for name, campus_id
                        in self.campus_map.items()
                        if campus_id == self.user.campus_id
                    ),
                    None
                )

                if assigned is None:
                    messagebox.showerror(
                        "Campus Access Error",
                        "This administrator has no valid assigned campus."
                    )
                    self.window.destroy()
                    return

                self.campus_selector.set(assigned)
                self.campus_selector.configure(state="disabled")

            elif self.campus_map:
                active_name = next(
                    (
                        name for name, campus_id
                        in self.campus_map.items()
                        if campus_id == self.active_campus_id
                    ),
                    None
                )

                if active_name:
                    self.campus_selector.set(active_name)
                    self.campus_selector.configure(state="disabled")
                else:
                    self.campus_selector.set(
                        next(iter(self.campus_map))
                    )

            self.load_resources()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load campuses: {error}"
            )

    def get_active_campus_id(self):
        campus_name = self.campus_selector.get()
        return self.campus_map.get(campus_name)

    def on_campus_changed(self, event=None):
        self.clear_fields()
        self.load_resources()

    def load_resources(self):
        campus_id = self.get_active_campus_id()

        if campus_id is None:
            self.active_campus_label.config(
                text="Active campus: None selected"
            )
            return

        campus_name = self.campus_selector.get()
        self.active_campus_label.config(
            text=f"Active campus: {campus_name}"
        )

        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            with self.connect_database() as connection:
                rows = connection.execute("""
                    SELECT resource_id, resource_name, resource_type
                    FROM resources
                    WHERE campus_id = ?
                    ORDER BY resource_name
                """, (campus_id,)).fetchall()

            for row in rows:
                self.tree.insert("", "end", values=row)

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load resources: {error}"
            )

    def on_resource_selected(self, event=None):
        selection = self.tree.selection()

        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        self.selected_resource_id = values[0]

        self.resource_id_entry.delete(0, tk.END)
        self.resource_id_entry.insert(0, values[0])

        self.resource_name_entry.delete(0, tk.END)
        self.resource_name_entry.insert(0, values[1])

        self.resource_type_entry.delete(0, tk.END)
        self.resource_type_entry.insert(0, values[2])

        if self.can_manage:
            self.resource_id_entry.configure(state="disabled")

    def clear_fields(self):
        self.selected_resource_id = None

        self.resource_id_entry.configure(state="normal")
        self.resource_id_entry.delete(0, tk.END)
        self.resource_name_entry.delete(0, tk.END)
        self.resource_type_entry.delete(0, tk.END)

        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def add_resource(self):
        if not self.can_manage:
            messagebox.showerror(
                "Access Denied",
                "Only campus administrators can manage resources."
            )
            return

        campus_id = self.get_active_campus_id()
        resource_id = self.resource_id_entry.get().strip().upper()
        resource_name = self.resource_name_entry.get().strip()
        resource_type = self.resource_type_entry.get().strip()

        if not all([campus_id, resource_id, resource_name, resource_type]):
            messagebox.showerror(
                "Missing Information",
                "Enter a resource ID, name and type."
            )
            return

        try:
            with self.connect_database() as connection:
                connection.execute("""
                    INSERT INTO resources
                    (resource_id, resource_name, resource_type, campus_id)
                    VALUES (?, ?, ?, ?)
                """, (
                    resource_id,
                    resource_name,
                    resource_type,
                    campus_id
                ))

            messagebox.showinfo(
                "Success",
                "Resource added successfully."
            )
            self.clear_fields()
            self.load_resources()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Duplicate or Invalid Resource",
                "This resource ID already exists, or the campus is invalid."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not add resource: {error}"
            )

    def update_resource(self):
        if not self.can_manage:
            messagebox.showerror(
                "Access Denied",
                "Only campus administrators can update resources."
            )
            return

        if not self.selected_resource_id:
            messagebox.showwarning(
                "Select a Resource",
                "Select a resource from the table first."
            )
            return

        campus_id = self.get_active_campus_id()
        resource_name = self.resource_name_entry.get().strip()
        resource_type = self.resource_type_entry.get().strip()

        if not resource_name or not resource_type:
            messagebox.showerror(
                "Missing Information",
                "Resource name and type are required."
            )
            return

        try:
            with self.connect_database() as connection:
                cursor = connection.execute("""
                    UPDATE resources
                    SET resource_name = ?, resource_type = ?
                    WHERE resource_id = ? AND campus_id = ?
                """, (
                    resource_name,
                    resource_type,
                    self.selected_resource_id,
                    campus_id
                ))

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Update Failed",
                    "The resource was not found in the active campus."
                )
                return

            messagebox.showinfo(
                "Success",
                "Resource updated successfully."
            )
            self.clear_fields()
            self.load_resources()

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not update resource: {error}"
            )

    def remove_resource(self):
        if not self.can_manage:
            messagebox.showerror(
                "Access Denied",
                "Only campus administrators can remove resources."
            )
            return

        if not self.selected_resource_id:
            messagebox.showwarning(
                "Select a Resource",
                "Select a resource from the table first."
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Removal",
            "Are you sure you want to remove this resource?"
        )

        if not confirmed:
            return

        try:
            with self.connect_database() as connection:
                cursor = connection.execute("""
                    DELETE FROM resources
                    WHERE resource_id = ? AND campus_id = ?
                """, (
                    self.selected_resource_id,
                    self.get_active_campus_id()
                ))

            if cursor.rowcount == 0:
                messagebox.showerror(
                    "Removal Failed",
                    "The resource was not found in the active campus."
                )
                return

            messagebox.showinfo(
                "Success",
                "Resource removed successfully."
            )
            self.clear_fields()
            self.load_resources()

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Resource In Use",
                "This resource is linked to existing bookings and "
                "cannot be deleted. Keep it in the system."
            )

        except sqlite3.Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not remove resource: {error}"
            )
