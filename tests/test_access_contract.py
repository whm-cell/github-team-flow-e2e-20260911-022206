import unittest
from enrollment import EnrollmentRegistry

class AccessContractTests(unittest.TestCase):
    def test_access_requires_paid_enrollment_in_same_course(self):
        registry = EnrollmentRegistry()
        self.assertFalse(registry.has_access("course", "student"))
        registry.enroll("other-course", "student")
        self.assertFalse(registry.has_access("course", "student"))
        registry.enroll("course", "student")
        self.assertTrue(registry.has_access("course", "student"))
