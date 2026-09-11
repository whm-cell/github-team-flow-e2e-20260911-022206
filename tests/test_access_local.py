import unittest
from enrollment import EnrollmentRegistry

class AccessTests(unittest.TestCase):
    def test_new_contract_preserves_paid_access(self):
        registry = EnrollmentRegistry()
        self.assertFalse(registry.has_access("course", "student"))
        registry.enroll("course", "student")
        self.assertTrue(registry.has_access("course", "student"))
