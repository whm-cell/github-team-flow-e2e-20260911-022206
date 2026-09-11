import unittest
from enrollment import EnrollmentRegistry

class StudentIdentityTests(unittest.TestCase):
    def test_enrollment_of_one_student_does_not_authorize_another(self):
        registry = EnrollmentRegistry()
        registry.enroll("course", "alice")
        self.assertTrue(registry.has_access("course", "alice"))
        self.assertFalse(registry.has_access("course", "bob"))
