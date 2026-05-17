def get_best_subject(student):
    """Найти лучший предмет студента"""
    if not student.subjects:
        return None

    best = None
    best_avg = -1

    for subject, grades in student.subjects.items():
        avg = sum(grades) / len(grades)
        if avg > best_avg:
            best_avg = avg
            best = subject

    return best


def get_worst_subject(student):
    """Найти слабый предмет студента"""
    if not student.subjects:
        return None

    worst = None
    worst_avg = 101

    for subject, grades in student.subjects.items():
        avg = sum(grades) / len(grades)
        if avg < worst_avg:
            worst_avg = avg
            worst = subject

    return worst


def get_performance_level(average):
    """Определить уровень успеваемости по среднему баллу"""
    if average >= 90:
        return "Отлично"
    elif average >= 75:
        return "Хорошо"
    elif average >= 60:
        return "Удовлетворительно"
    else:
        return "Критично"


def get_recommendations(student):
    """Сгенерировать рекомендации для студента"""
    recommendations = []
    average = student.calculate_average()
    worst = get_worst_subject(student)
    best = get_best_subject(student)

    if average < 60:
        recommendations.append("Срочно обратитесь к преподавателю за помощью!")
        recommendations.append("Рассмотрите дополнительные занятия или тьюторинг.")

    if worst and student.subjects[worst]:
        worst_avg = sum(student.subjects[worst]) / len(student.subjects[worst])
        if worst_avg < 70:
            recommendations.append(f"Уделите больше времени предмету '{worst}'.")
            recommendations.append(f"Повторите базовые темы по '{worst}'.")

    if average >= 85:
        recommendations.append("Отличная работа! Можете помочь другим студентам.")
        recommendations.append(f"Ваш лучший предмет — '{best}', продолжайте в том же духе!")

    if not recommendations:
        recommendations.append("Продолжайте в том же темпе, вы на правильном пути!")
        recommendations.append("Уделяйте равное внимание всем предметам.")

    return recommendations


def analyze_student(student):
    """Полный анализ одного студента"""
    average = student.calculate_average()
    level = get_performance_level(average)
    best = get_best_subject(student)
    worst = get_worst_subject(student)
    recommendations = get_recommendations(student)

    print("\n" + "=" * 40)
    print(f"АНАЛИЗ: {student.name}")
    print("=" * 40)
    print(f"Средний балл: {average}")
    print(f"Уровень: {level}")

    if best:
        best_avg = round(sum(student.subjects[best]) / len(student.subjects[best]), 2)
        print(f"Лучший предмет: {best} ({best_avg})")

    if worst:
        worst_avg = round(sum(student.subjects[worst]) / len(student.subjects[worst]), 2)
        print(f"Слабый предмет: {worst} ({worst_avg})")

    print("\nРекомендации:")
    for rec in recommendations:
        print(f"  - {rec}")

    print("=" * 40)


def analyze_all_students(students):
    """Общая статистика по всем студентам"""
    if not students:
        print("Нет данных для анализа.")
        return

    print("\n" + "=" * 40)
    print("СТАТИСТИКА ГРУППЫ")
    print("=" * 40)
    print(f"Всего студентов: {len(students)}")

    averages = []
    for s in students:
        avg = s.calculate_average()
        averages.append((s.name, avg))
        print(f"  {s.name}: {avg}")

    if averages:
        best = max(averages, key=lambda x: x[1])
        worst = min(averages, key=lambda x: x[1])
        class_avg = round(sum(a for _, a in averages) / len(averages), 2)

        print(f"\nСредний балл группы: {class_avg}")
        print(f"Лучший студент: {best[0]} ({best[1]})")
        print(f"Нуждается в помощи: {worst[0]} ({worst[1]})")

    print("=" * 40)