import unittest

from app.backend.controllers.schemas import SUser


class TestSUserPasswordValidation(unittest.TestCase):
    def test_password_no_digit(self):
        with self.assertRaises(ValueError) as cm:
            SUser(email="test@example.ru", password="NoDi@gitPassword!")
        self.assertIn("Password must contain at least one number.", str(cm.exception))

    def test_password_too_short(self):
        with self.assertRaises(ValueError) as cm:
            SUser(email="test@example.ru", password="P1@Sal!")
        self.assertIn("String should have at least 8 characters", str(cm.exception))

    def test_password_too_long(self):
        with self.assertRaises(ValueError) as cm:
            SUser(email="test@example.ru",
                  password="Strong.Password123!Strong.Password123!Strong.Password123!Strong.Password123!Strong.Passwor")
        self.assertIn("String should have at most 32 characters", str(cm.exception))

    def test_email(self):
        with self.assertRaises(ValueError) as cm:
            SUser(email="test.test", password="SoMeGrE@tPa22WoRd!")
        self.assertIn("value is not a valid email address", str(cm.exception))

    def test_valid_password(self):
        try:
            user = SUser(email="test@example.ru", password="Strong.Password123!")
            self.assertEqual(user.email, "test@example.ru")
            self.assertEqual(user.password, "Strong.Password123!")
        except ValueError as e:
            self.fail(f"Valid password raised ValidationError: {e}")

if __name__ == '__main__':
    unittest.main()

