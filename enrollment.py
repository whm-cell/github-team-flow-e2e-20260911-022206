class EnrollmentRegistry:
    def __init__(self):
        self._paid = set()

    def enroll(self, course_id, student_id):
        if not course_id or not student_id:
            raise ValueError("course and student are required")
        self._paid.add((course_id, student_id))

    def is_enrolled(self, course_id, student_id):
        return (course_id, student_id) in self._paid

    def has_access(self, course_id, student_id):
        return self.is_enrolled(course_id, student_id)
