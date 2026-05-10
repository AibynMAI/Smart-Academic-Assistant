def analyze_performance(student):

    average = student.calculate_average()

    if average >= 85:
        return "Excellent performance! Keep it up."

    elif average >= 70:
        return "Good performance, but there is room for improvement."

    elif average >= 50:
        return "Average performance. Focus more on weak subjects."

    else:
        return "Low performance detected. More study time is recommended."


def get_weak_subject(student):

    lowest_average = 101
    weak_subject = None

    for subject, grades in student.subjects.items():

        subject_average = sum(grades) / len(grades)

        if subject_average < lowest_average:
            lowest_average = subject_average
            weak_subject = subject

    return weak_subject