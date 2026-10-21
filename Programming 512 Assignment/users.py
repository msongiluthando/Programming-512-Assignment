import hashlib
import hmac
import secrets


def hash_password(password):
    """Convert a password into a salted hash for storage."""
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return salt.hex() + "$" + password_hash.hex()


def verify_password(password, stored_hash):
    """Check a password against its stored salted hash."""
    try:
        salt_hex, hash_hex = stored_hash.split("$")
        salt = bytes.fromhex(salt_hex)

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            600_000
        )

        return hmac.compare_digest(new_hash.hex(), hash_hex)

    except (ValueError, TypeError):
        return False



class User:
    def __init__(
            self, full_name, username, password_hash,
            campus_id=None, user_id=None
    ):
        self.user_id = user_id
        self.full_name = full_name
        self.username = username
        self._User__password_hash = password_hash
        self.campus_id = campus_id


    @property
    def role(self):
        return "user"

    def verify_login(self, password):
        return verify_password(password, self.__password_hash)

    def get_permissions(self):
        return ["view_profile"]


class Lecturer(User):
    """A lecturer can manage their own resource bookings."""

    @property
    def role(self):
        return "lecturer"

    def get_permissions(self):
        return [
            "view_resources",
            "create_booking",
            "view_own_bookings",
            "cancel_own_future_booking"
        ]


class CampusAdministrator(User):
    """An administrator manages resources at their campus."""

    @property
    def role(self):
        return "administrator"

    def get_permissions(self):
        return [
            "manage_campus_resources",
            "view_campus_bookings",
            "view_campus_usage"
        ]


class SystemOperator(User):
    """An operator can access system-wide information."""

    @property
    def role(self):
        return "operator"

    def get_permissions(self):
        return [
            "view_all_campuses",
            "view_all_resources",
            "view_all_bookings",
            "compare_campus_reports"
        ]


if __name__ == "__main__":
    # Test password hashing and verification
    saved_hash = hash_password("ExamplePass123!")

    print("Correct password:", verify_password(
        "ExamplePass123!", saved_hash
    ))
    print("Incorrect password:", verify_password(
        "WrongPassword", saved_hash
    ))

    # Test inheritance and role-specific permissions
    lecturer = Lecturer(
        "Test Lecturer", "lecturer1", saved_hash, campus_id=1
    )

    administrator = CampusAdministrator(
        "Test Administrator", "admin1", saved_hash, campus_id=1
    )

    operator = SystemOperator(
        "Test Operator", "operator1", saved_hash
    )

    for user in [lecturer, administrator, operator]:
        print("\nName:", user.full_name)
        print("Role:", user.role)
        print("Permissions:", user.get_permissions())
