"""Grade and GPA tracker."""

import json
import uuid
from pathlib import Path


def load_grades(data_path: str) -> dict:
    path = Path(data_path)
    if not path.exists():
        return {"courses": [], "gpa_scale": _default_scale()}
    with open(path) as f:
        return json.load(f)


def save_grades(data_path: str, data: dict):
    with open(data_path, "w") as f:
        json.dump(data, f, indent=2)


def _default_scale():
    return {"A+": 4.3, "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
            "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0, "F": 0.0}


def add_course(data_path: str, course: dict) -> str:
    data = load_grades(data_path)
    cid = str(uuid.uuid4())[:8]
    course["id"] = cid
    course.setdefault("assignments", [])
    course.setdefault("credits", 3)
    course.setdefault("semester", "")
    data["courses"].append(course)
    save_grades(data_path, data)
    return cid


def delete_course(data_path: str, course_id: str) -> bool:
    data = load_grades(data_path)
    n = len(data["courses"])
    data["courses"] = [c for c in data["courses"] if c.get("id") != course_id]
    if len(data["courses"]) < n:
        save_grades(data_path, data)
        return True
    return False


def add_assignment(data_path: str, course_id: str, assignment: dict) -> str:
    data = load_grades(data_path)
    for course in data["courses"]:
        if course["id"] == course_id:
            aid = str(uuid.uuid4())[:8]
            assignment["id"] = aid
            course.setdefault("assignments", []).append(assignment)
            save_grades(data_path, data)
            return aid
    return None


def delete_assignment(data_path: str, course_id: str, assignment_id: str) -> bool:
    data = load_grades(data_path)
    for course in data["courses"]:
        if course["id"] == course_id:
            n = len(course.get("assignments", []))
            course["assignments"] = [a for a in course.get("assignments", []) if a.get("id") != assignment_id]
            if len(course["assignments"]) < n:
                save_grades(data_path, data)
                return True
    return False


def calculate_course_grade(course: dict) -> float:
    """Calculate weighted average grade for a course."""
    assignments = course.get("assignments", [])
    if not assignments:
        return None

    total_weight = sum(a.get("weight", 0) for a in assignments)
    if total_weight == 0:
        # Equal weight
        grades = [a.get("grade", 0) for a in assignments]
        return sum(grades) / len(grades) if grades else None

    weighted_sum = sum(a.get("grade", 0) * a.get("weight", 0) for a in assignments)
    return weighted_sum / total_weight


def percentage_to_letter(pct: float) -> str:
    """Convert percentage to letter grade."""
    if pct >= 93: return "A"
    if pct >= 90: return "A-"
    if pct >= 87: return "B+"
    if pct >= 83: return "B"
    if pct >= 80: return "B-"
    if pct >= 77: return "C+"
    if pct >= 73: return "C"
    if pct >= 70: return "C-"
    if pct >= 67: return "D+"
    if pct >= 60: return "D"
    return "F"


def calculate_gpa(data_path: str) -> dict:
    """Calculate cumulative GPA."""
    data = load_grades(data_path)
    scale = data.get("gpa_scale", _default_scale())

    total_points = 0
    total_credits = 0
    course_grades = []

    for course in data["courses"]:
        grade_pct = calculate_course_grade(course)
        credits = course.get("credits", 3)

        # Start with all original course data (preserves campus, room, class_days, etc.)
        course_entry = dict(course)
        course_entry["credits"] = credits

        if grade_pct is not None:
            letter = percentage_to_letter(grade_pct)
            gpa_points = scale.get(letter, 0)
            total_points += gpa_points * credits
            total_credits += credits
            course_entry["grade_pct"] = round(grade_pct, 1)
            course_entry["letter"] = letter
            course_entry["gpa_points"] = gpa_points
        else:
            course_entry["grade_pct"] = None
            course_entry["letter"] = "-"
            course_entry["gpa_points"] = None

        course_grades.append(course_entry)

    cumulative_gpa = round(total_points / total_credits, 2) if total_credits > 0 else None

    return {
        "courses": course_grades,
        "cumulative_gpa": cumulative_gpa,
        "total_credits": total_credits,
    }
