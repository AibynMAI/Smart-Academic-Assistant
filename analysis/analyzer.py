def analyze_performance(student) -> str:
    average = student.calculate_average()
    if average >= 85:
        return "🌟 Excellent performance! Keep it up."
    elif average >= 70:
        return "👍 Good performance, but there is room for improvement."
    elif average >= 50:
        return "📚 Average performance. Focus more on weak subjects."
    else:
        return "⚠️ Low performance detected. More study time is recommended."


def get_weak_subject(student) -> str | None:
    if not student.subjects:
        return None
    return min(
        student.subjects,
        key=lambda s: sum(student.subjects[s]) / len(student.subjects[s]),
    )


def get_strong_subject(student) -> str | None:
    if not student.subjects:
        return None
    return max(
        student.subjects,
        key=lambda s: sum(student.subjects[s]) / len(student.subjects[s]),
    )


def get_top_student(students):
    if not students:
        return None
    return max(students, key=lambda s: s.calculate_average())


def get_group_stats(students) -> dict:
    if not students:
        return {}
    averages = [s.calculate_average() for s in students]
    return {
        "count":   len(students),
        "highest": max(averages),
        "lowest":  min(averages),
        "group_avg": round(sum(averages) / len(averages), 2),
    }