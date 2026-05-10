
from decorators.logger import log_action

class Student:
    def __init__(self, name, student_id):
        self.name = name
        self.student_id = student_id
        self.subjects = {}

    @log_action
    def add_grade(self, subject, grade):
        if subject not in self.subjects:
            self.subjects[subject] = []

        self.subjects[subject].append(grade)

    def calculate_average(self):
        total = 0
        count = 0

        for grades in self.subjects.values():
            total += sum(grades)
            count += len(grades)

        if count == 0:
            return 0

        return round(total / count, 2)

    def display_info(self):
        print("\n===== STUDENT REPORT =====")
        print(f"Name: {self.name}")
        print(f"ID: {self.student_id}")
        print(f"Subjects: {self.subjects}")
        print(f"Average: {self.calculate_average()}")