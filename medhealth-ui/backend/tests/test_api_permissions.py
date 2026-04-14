import pathlib
import sys
import unittest

from fastapi import HTTPException


ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from platform_api import get_settings, require_permission, update_settings  # noqa: E402


class PermissionTests(unittest.TestCase):
    def test_billing_specialist_cannot_write_settings(self) -> None:
        user = {"username": "billing", "role": "Billing Specialist", "user_id": 2}
        with self.assertRaises(HTTPException) as context:
            update_settings({"demo_mode": False}, user)
        self.assertEqual(context.exception.status_code, 403)

    def test_auditor_can_read_audit(self) -> None:
        user = {"username": "auditor", "role": "Compliance Auditor", "user_id": 6}
        require_permission(user, "audit", "read")

    def test_provider_cannot_list_users(self) -> None:
        user = {"username": "provider", "role": "Healthcare Provider", "user_id": 4}
        with self.assertRaises(HTTPException) as context:
            require_permission(user, "users", "read")
        self.assertEqual(context.exception.status_code, 403)

    def test_administrator_can_read_settings(self) -> None:
        user = {"username": "admin", "role": "Administrator", "user_id": 1}
        result = get_settings(user)
        self.assertIn("policy_profiles", result)


if __name__ == "__main__":
    unittest.main()
