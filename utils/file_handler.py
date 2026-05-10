import json


def save_students(students, filename):
    data = []

    for student in students:
        student_data = {
            "name": student.name,
            "student_id": student.student_id,
            "subjects": student.subjects
        }

        data.append(student_data)

    with open(filename, "w") as file:
        json.dump(data, file, indent=4)


def load_students(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)

            return data

    except FileNotFoundError:
        return []