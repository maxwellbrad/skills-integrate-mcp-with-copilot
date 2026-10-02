import os
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app import activities, app
from src.auth import hash_password, load_users, save_users, verify_password


class RoleBasedAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.student_hash = hash_password("student-password")
        cls.staff_hash = hash_password("staff-password")

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.users_path = os.path.join(self.temporary_directory.name, "users.json")
        self.environment = patch.dict(
            os.environ,
            {
                "AUTH_USERS_FILE": self.users_path,
                "AUTH_SESSION_SECRET": "test-only-session-secret",
                "AUTH_COOKIE_SECURE": "false",
            },
        )
        self.environment.start()
        save_users(
            {
                "student@mergington.edu": {
                    "role": "student",
                    "password_hash": self.student_hash,
                },
                "staff@mergington.edu": {
                    "role": "staff",
                    "password_hash": self.staff_hash,
                },
            }
        )
        self.original_activities = deepcopy(activities)
        self.client = TestClient(app)

    def tearDown(self):
        activities.clear()
        activities.update(self.original_activities)
        self.environment.stop()
        self.temporary_directory.cleanup()

    def sign_in(self, email, password):
        return self.client.post("/auth/login", json={"email": email, "password": password})

    def test_passwords_are_hashed_and_bad_credentials_are_rejected(self):
        self.assertNotEqual(self.student_hash, "student-password")
        self.assertTrue(verify_password("student-password", self.student_hash))
        self.assertFalse(verify_password("wrong-password", self.student_hash))
        self.assertEqual(load_users()["student@mergington.edu"]["password_hash"], self.student_hash)
        self.assertEqual(self.sign_in("student@mergington.edu", "wrong-password").status_code, 401)

    def test_registration_mutations_require_authentication(self):
        signup = self.client.post("/activities/Chess%20Club/signup")
        unregister = self.client.delete(
            "/activities/Chess%20Club/unregister?email=michael%40mergington.edu"
        )
        self.assertEqual(signup.status_code, 401)
        self.assertEqual(unregister.status_code, 401)

    def test_student_can_manage_only_their_own_registration(self):
        response = self.sign_in("student@mergington.edu", "student-password")
        self.assertEqual(response.status_code, 200)
        self.assertIn("httponly", response.headers["set-cookie"].lower())

        signup = self.client.post("/activities/Chess%20Club/signup")
        self.assertEqual(signup.status_code, 200)
        self.assertIn("student@mergington.edu", activities["Chess Club"]["participants"])

        forbidden_signup = self.client.post(
            "/activities/Chess%20Club/signup?email=someone%40mergington.edu"
        )
        forbidden_unregister = self.client.delete(
            "/activities/Chess%20Club/unregister?email=michael%40mergington.edu"
        )
        self.assertEqual(forbidden_signup.status_code, 403)
        self.assertEqual(forbidden_unregister.status_code, 403)

        unregister = self.client.delete("/activities/Chess%20Club/unregister")
        self.assertEqual(unregister.status_code, 200)
        self.assertNotIn("student@mergington.edu", activities["Chess Club"]["participants"])

    def test_staff_can_manage_another_students_registration(self):
        response = self.sign_in("staff@mergington.edu", "staff-password")
        self.assertEqual(response.json()["role"], "staff")

        signup = self.client.post(
            "/activities/Chess%20Club/signup?email=student%40mergington.edu"
        )
        unregister = self.client.delete(
            "/activities/Chess%20Club/unregister?email=student%40mergington.edu"
        )
        self.assertEqual(signup.status_code, 200)
        self.assertEqual(unregister.status_code, 200)


if __name__ == "__main__":
    unittest.main()