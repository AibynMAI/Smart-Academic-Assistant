from models.student import Student
from utils.file_handler import save_students, load_students
from analysis.analyzer import (
    analyze_performance,
    get_weak_subject,
    get_top_student
)

DATA_FILE = "data/students.json"

# Загружаем студентов из файла при старте
def load_all():
    data = load_students(DATA_FILE)
    students = []
    for item in data:
        s = Student(name=item["name"], student_id=item["student_id"])
        s.subjects = item.get("subjects", {})
        students.append(s)
    return students


def save_all(students):
    save_students(students, DATA_FILE)


def show_menu():
    print("\n" + "=" * 40)
    print("   SMART ACADEMIC ASSISTANT")
    print("=" * 40)
    print("1. Добавить студента")
    print("2. Добавить оценку")
    print("3. Показать студента")
    print("4. Показать всех студентов")
    print("5. Анализ студента")
    print("6. Статистика группы")
    print("0. Выход")
    print("=" * 40)


def find_student(students, student_id):
    for s in students:
        if s.student_id == student_id:
            return s
    return None


def main():
    students = load_all()
    print(f"Загружено студентов: {len(students)}")

    while True:
        show_menu()
        choice = input("Выберите действие: ").strip()

        if choice == "1":
            name = input("Имя студента: ").strip()
            sid = input("ID студента: ").strip()
            if find_student(students, sid):
                print(f"Студент с ID '{sid}' уже существует!")
            else:
                s = Student(name=name, student_id=sid)
                students.append(s)
                save_all(students)
                print(f"Студент '{name}' добавлен!")

        elif choice == "2":
            sid = input("ID студента: ").strip()
            s = find_student(students, sid)
            if not s:
                print("Студент не найден!")
            else:
                subject = input("Предмет: ").strip()
                try:
                    grade = float(input("Оценка (0-100): "))
                    if 0 <= grade <= 100:
                        s.add_grade(subject=subject, grade=grade)
                        save_all(students)
                        print(f"Оценка {grade} по '{subject}' добавлена!")
                    else:
                        print("Оценка должна быть от 0 до 100!")
                except ValueError:
                    print("Введите число!")

        elif choice == "3":
            sid = input("ID студента: ").strip()
            s = find_student(students, sid)
            if not s:
                print("Студент не найден!")
            else:
                s.display_info()

        elif choice == "4":
            if not students:
                print("Список студентов пуст.")
            else:
                for s in students:
                    print(f"  {s.name} (ID: {s.student_id}) | Среднее: {s.calculate_average()}")

        elif choice == "5":
            sid = input("ID студента: ").strip()
            s = find_student(students, sid)
            if not s:
                print("Студент не найден!")
            else:
                analyze_student(s)

        elif choice == "6":
            analyze_all_students(students)

        elif choice == "0":
            print("До свидания!")
            break

        else:
            print("Неверный выбор!")


if __name__ == "__main__":
    main()