import unittest
from enrollment import EnrollmentRegistry
from classroom import Classroom

class ClassroomClientContractTests(unittest.TestCase):
    def test_client_obeys_access_contract_denial(self):
        class DeniedRegistry(EnrollmentRegistry):
            def has_access(self, course_id, student_id):
                return False
        registry = DeniedRegistry()
        registry.enroll("course", "student")
        room = Classroom("course", "teacher", registry)
        with self.assertRaises(PermissionError):
            room.join("student")
