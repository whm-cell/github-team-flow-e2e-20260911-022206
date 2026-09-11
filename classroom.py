class Classroom:
    def __init__(self, course_id, teacher_id, enrollment):
        self.course_id = course_id
        self.teacher_id = teacher_id
        self.enrollment = enrollment
        self.members = set()
        self.ended = False

    def join(self, student_id):
        if self.ended:
            raise ValueError("class has ended")
        if not self.enrollment.has_access(self.course_id, student_id):
            raise PermissionError("paid enrollment is required")
        self.members.add(student_id)
        return {"course_id": self.course_id, "student_id": student_id, "joined": True}

    def end(self, teacher_id):
        if teacher_id != self.teacher_id:
            raise PermissionError("only the teacher can end class")
        self.ended = True

    def can_replay(self, student_id):
        return self.ended and self.enrollment.is_enrolled(self.course_id, student_id)
