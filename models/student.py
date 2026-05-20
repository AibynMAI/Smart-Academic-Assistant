class Student:
    def __init__(self, name: str, student_id: str):
        self.name = name
        self.student_id = student_id
        self.subjects: dict[str, list[float]] = {}

    def add_grade(self, subject: str, grade: float) -> None:
        self.subjects.setdefault(subject, []).append(grade)

    def calculate_average(self) -> float:
        total, count = 0, 0
        for grades in self.subjects.values():
            total += sum(grades)
            count += len(grades)
        return round(total / count, 2) if count else 0.0

    def subject_average(self, subject: str) -> float:
        grades = self.subjects.get(subject, [])
        return round(sum(grades) / len(grades), 2) if grades else 0.0

    def display_info(self) -> None:
        print("\n===== STUDENT REPORT =====")
        print(f"Name   : {self.name}")
        print(f"ID     : {self.student_id}")
        print(f"Average: {self.calculate_average()}")
        print("Subjects:")
        for subj, grades in self.subjects.items():
            avg = round(sum(grades) / len(grades), 2)
            print(f"  {subj}: {avg}  {grades}")

    def to_dict(self) -> dict:
        return {
            "name":       self.name,
            "student_id": self.student_id,
            "subjects":   self.subjects,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        s = cls(name=data["name"], student_id=data["student_id"])
        s.subjects = data.get("subjects", {})
        return s