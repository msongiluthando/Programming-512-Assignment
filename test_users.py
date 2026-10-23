import unittest

from users import (
    Lecturer, CampusAdministrator, SystemOperator,
    hash_password, verify_password
)

HASH = hash_password("Password123")


class UserTests(unittest.TestCase):

    def setUp(self):
        self.lecturer = Lecturer("Lee", "lee", HASH, campus_id=1, user_id=1)
        self.admin = CampusAdministrator(
            "Ada", "ada", HASH, campus_id=3, user_id=2)
        self.operator = SystemOperator("Oz", "oz", HASH, user_id=3)

    def test_password_hash_is_salted_and_verifies(self):
        self.assertNotEqual(HASH, hash_password("Password123"))
        self.assertTrue(verify_password("Password123", HASH))
        self.assertFalse(verify_password("wrong", HASH))
        self.assertFalse(verify_password("x", "not-a-valid-hash"))

    def test_verify_login(self):
        self.assertTrue(self.lecturer.verify_login("Password123"))
        self.assertFalse(self.lecturer.verify_login("nope"))

    def test_roles(self):
        self.assertEqual(self.lecturer.role, "lecturer")
        self.assertEqual(self.admin.role, "administrator")
        self.assertEqual(self.operator.role, "operator")

    def test_each_role_has_different_permissions(self):
        self.assertIn("create_booking", self.lecturer.get_permissions())
        self.assertNotIn("create_booking", self.admin.get_permissions())
        self.assertIn("compare_campus_reports",
                      self.operator.get_permissions())

    def test_details_are_read_only(self):
        for name in ("user_id", "full_name", "username", "campus_id"):
            with self.assertRaises(AttributeError):
                setattr(self.lecturer, name, "changed")

    def test_password_hash_is_not_exposed(self):
        self.assertFalse(hasattr(self.lecturer, "password_hash"))
        self.assertNotIn(HASH, repr(self.lecturer))

    def test_lecturer_may_choose_any_campus(self):
        self.assertTrue(self.lecturer.can_select_campus(1))
        self.assertTrue(self.lecturer.can_select_campus(2))
        self.assertFalse(self.lecturer.can_view_all_campuses())

    def test_administrator_is_limited_to_own_campus(self):
        self.assertTrue(self.admin.can_select_campus(3))
        self.assertFalse(self.admin.can_select_campus(1))
        self.assertFalse(self.admin.can_view_all_campuses())

    def test_operator_can_work_across_all_campuses(self):
        self.assertTrue(self.operator.can_select_campus(2))
        self.assertTrue(self.operator.can_view_all_campuses())

    def test_no_campus_is_never_allowed(self):
        for user in (self.lecturer, self.admin, self.operator):
            self.assertFalse(user.can_select_campus(None))


if __name__ == "__main__":
    unittest.main()
