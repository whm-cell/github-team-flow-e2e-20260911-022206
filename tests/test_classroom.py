import unittest

from classroom import Classroom
from enrollment import EnrollmentRegistry


class ClassroomIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.enrollment = EnrollmentRegistry()
        self.room = Classroom("demo-course", "demo-teacher", self.enrollment)

    def test_paid_student_can_join_then_replay(self):
        self.enrollment.enroll("demo-course", "demo-student")
        self.assertEqual(self.room.join("demo-student"), {
            "course_id": "demo-course", "student_id": "demo-student", "joined": True})
        self.assertFalse(self.room.can_replay("demo-student"))
        self.room.end("demo-teacher")
        self.assertTrue(self.room.can_replay("demo-student"))

    def test_unpaid_student_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.room.join("unpaid-demo-student")

    def test_enrollment_in_other_course_does_not_grant_access(self):
        self.enrollment.enroll("other-demo-course", "demo-student")
        with self.assertRaises(PermissionError):
            self.room.join("demo-student")

    def test_duplicate_join_is_idempotent(self):
        self.enrollment.enroll("demo-course", "demo-student")
        self.room.join("demo-student")
        self.room.join("demo-student")
        self.assertEqual(self.room.members, {"demo-student"})

    def test_only_teacher_can_end_class(self):
        with self.assertRaises(PermissionError):
            self.room.end("demo-student")
        self.assertFalse(self.room.ended)

    def test_ended_class_rejects_join(self):
        self.enrollment.enroll("demo-course", "demo-student")
        self.room.end("demo-teacher")
        with self.assertRaises(ValueError):
            self.room.join("demo-student")

    def test_unpaid_student_cannot_replay(self):
        self.room.end("demo-teacher")
        self.assertFalse(self.room.can_replay("unpaid-demo-student"))

    def test_enrollment_requires_identifiers(self):
        for course, student in [("", "demo-student"), ("demo-course", "")]:
            with self.assertRaises(ValueError):
                self.enrollment.enroll(course, student)


if __name__ == "__main__":
    unittest.main()
