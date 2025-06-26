import unittest

from pydantic import ValidationError

from app.backend.schemas import SUser


class TestSUserPasswordValidation(unittest.TestCase):
    def test_valid_password(self):
        try:
            user = SUser(email="test@example.ru", password="Strong.Password123!")
            self.assertEqual(user.email, "test@example.ru")
            self.assertEqual(user.password, "Strong.Password123!")
        except ValidationError as e:
            self.fail(f"Valid password raised ValidationError: {e}")

    def test_password_too_short(self):
        with self.assertRaises(ValidationError) as cm:
            SUser(email="test@example.ru", password="Pa1!")
        self.assertIn("String should have at least 8 characters", str(cm.exception))

    def test_password_too_long(self):
        with self.assertRaises(ValidationError) as cm:
            SUser(email="test@example.ru",
                  password="Strong.Password123!Strong.Password123!Strong.Password123!Strong.Password123!Strong.Passwor")
        self.assertIn("Ensure that password has at most 32 characters", str(cm.exception))

    def test_password_no_digit(self):
        with self.assertRaises(ValidationError) as cm:
            SUser(email="test@example.ru", password="NoDigitPassword!")
        self.assertIn("Ensure that password should have digits", str(cm.exception))



if __name__ == '__main__':
    unittest.main()

