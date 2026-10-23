import hashlib
import hmac
import secrets


def hash_password(password):
    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        600_000
    )

    return salt.hex() + "$" + password_hash.hex()


def verify_password(password, stored_hash):

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

    except (ValueError, TypeError, AttributeError):
        return False


class User:

    def __init__(
            self, full_name, username, password_hash,
            campus_id=None, user_id=None
    ):
        self.__user_id = user_id
        self.__full_name = full_name
        self.__username = username
        self.__password_hash = password_hash
        self.__campus_id = campus_id

    @property
    def user_id(self):
        return self.__user_id

    @property
    def full_name(self):
        return self.__full_name

    @property
    def username(self):
        return self.__username

    @property
    def campus_id(self):
        return self.__campus_id

    @property
    def role(self):
        return "user"

    def verify_login(self, password):
        return verify_password(password, self.__password_hash)

    def get_permissions(self):
        return ["view_profile"]

    def can_select_campus(self, campus_id):
        return campus_id is not None and campus_id == self.__campus_id

    def can_view_all_campuses(self):
        return False

    def __repr__(self):
        return f"{type(self).__name__}(username={self.__username!r})"


class Lecturer(User):

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

    def can_select_campus(self, campus_id):
        return campus_id is not None


class CampusAdministrator(User):

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

    def can_select_campus(self, campus_id):
        return campus_id is not None

    def can_view_all_campuses(self):
        return True


if __name__ == "__main__":
    saved_hash = hash_password("ExamplePass123!")

    print("Correct password:", verify_password(
        "ExamplePass123!", saved_hash
    ))
    print("Incorrect password:", verify_password(
        "WrongPassword", saved_hash
    ))

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
