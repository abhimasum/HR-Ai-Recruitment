import unittest

from app.core.auth import (
    create_session_token,
    hash_password,
    read_session_token,
    verify_password,
)

TEST_SIGNING_KEY = "test-key-with-enough-entropy-for-unit-tests"


class AuthenticationPrimitiveTests(unittest.TestCase):
    def test_password_hash_is_salted_and_verifies(self):
        first_hash = hash_password("candidate1")
        second_hash = hash_password("candidate1")

        self.assertNotEqual(first_hash, second_hash)
        self.assertTrue(verify_password("candidate1", first_hash))
        self.assertFalse(verify_password("wrong-password", first_hash))

    def test_session_token_is_signed_and_tamper_evident(self):
        token = create_session_token(42, TEST_SIGNING_KEY)
        self.assertEqual(read_session_token(token, TEST_SIGNING_KEY), 42)
        self.assertIsNone(read_session_token(token + "tampered", TEST_SIGNING_KEY))
        self.assertIsNone(read_session_token(None, TEST_SIGNING_KEY))


if __name__ == "__main__":
    unittest.main()
