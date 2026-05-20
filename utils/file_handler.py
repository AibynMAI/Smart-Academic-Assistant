import json
import os


def save_students(students, filename: str) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    data = [s.to_dict() for s in students]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_students(filename: str) -> list[dict]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []