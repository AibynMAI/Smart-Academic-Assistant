
from analysis.analyzer import analyze_performance, get_weak_subject
from models.student import Student
from utils.file_handler import save_students, load_students


students = []


while True:
    print("\n===== SMART ACADEMIC ASSISTANT =====")
    print("1. Add Student")
    print("2. Add Grade")
    print("3. View Students")
    print("4. Save Data")
    print("5. Load Data")
    print("6. Exit")

    choice = input("Enter your choice: ")

    # ADD STUDENT
    if choice == "1":
        name = input("Enter student name: ")
        student_id = input("Enter student ID: ")

        student = Student(name, student_id)
        students.append(student)

        print("Student added successfully!")

    # ADD GRADE
    elif choice == "2":
        student_id = input("Enter student ID: ")

        found = False

        for student in students:
            if student.student_id == student_id:

                subject = input("Enter subject: ")
                grade = int(input("Enter grade: "))

                student.add_grade(subject, grade)

                print("Grade added successfully!")

                found = True
                break

        if not found:
            print("Student not found!")

    # VIEW STUDENTS
    elif choice == "3":

        if len(students) == 0:
            print("No students available!")

        else:
            for student in students:

                student.display_info()

                recommendation = analyze_performance(student)

                weak_subject = get_weak_subject(student)

                print(f"Recommendation: {recommendation}")

                if weak_subject:
                    print(f"Weak Subject: {weak_subject}")

    # SAVE DATA
    elif choice == "4":
        save_students(students, "data/students.json")
        print("Data saved successfully!")

    # LOAD DATA
    elif choice == "5":

        loaded_data = load_students("data/students.json")

        print("\n===== LOADED DATA =====")

        for student in loaded_data:
            print(student)

    # EXIT
    elif choice == "6":
        print("Program closed.")
        break

    else:
        print("Invalid choice!")