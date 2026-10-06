"""Student Record Management System
Covers: functions, parameters, return values, lambda, list comprehensions,
file handling (JSON + CSV), and exception handling (try-except-finally).
"""
import csv
import json
import os

DATA_FILE = "students.json"
CSV_FILE = "students.csv"
FIELDS = ["roll_no", "name", "branch", "marks"]


# ---------- File handling ----------
def load_students(path=DATA_FILE):
    """Return list of student dicts from JSON; empty list if file missing/corrupt."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Warning: data file is corrupted. Starting with empty records.")
        return []


def save_students(students, path=DATA_FILE):
    """Write students to JSON."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(students, f, indent=4)
    except OSError as e:
        print(f"Could not save data: {e}")
    finally:
        pass  # file is closed automatically by `with`; finally shown for clarity


def export_csv(students, path=CSV_FILE):
    """Export records to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(students)
    print(f"Exported {len(students)} records to {path}")


def import_csv(path=CSV_FILE):
    """Import records from CSV and return them as a list."""
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return [
                {**row, "roll_no": int(row["roll_no"]), "marks": float(row["marks"])}
                for row in csv.DictReader(f)
            ]
    except FileNotFoundError:
        print("CSV file not found.")
        return []


# ---------- Helpers ----------
def read_int(prompt):
    """Keep asking until a valid integer is entered."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def read_marks(prompt):
    """Read marks between 0 and 100."""
    while True:
        try:
            marks = float(input(prompt))
            if not 0 <= marks <= 100:
                raise ValueError("Marks must be between 0 and 100.")
            return marks
        except ValueError as e:
            print(f"Invalid input: {e}")


def find_student(students, roll_no):
    """Return the student dict with the given roll number, else None."""
    return next((s for s in students if s["roll_no"] == roll_no), None)


# ---------- CRUD ----------
def add_student(students):
    roll_no = read_int("Roll No: ")
    if find_student(students, roll_no):
        print("A student with this roll number already exists.")
        return
    name = input("Name: ").strip()
    branch = input("Branch: ").strip()
    marks = read_marks("Marks (0-100): ")
    students.append({"roll_no": roll_no, "name": name, "branch": branch, "marks": marks})
    print("Student added.")


def view_students(students):
    if not students:
        print("No records found.")
        return
    print(f"\n{'Roll':<8}{'Name':<20}{'Branch':<12}{'Marks':<8}")
    print("-" * 48)
    for s in sorted(students, key=lambda s: s["roll_no"]):  # lambda
        print(f"{s['roll_no']:<8}{s['name']:<20}{s['branch']:<12}{s['marks']:<8}")


def update_student(students):
    student = find_student(students, read_int("Roll No to update: "))
    if not student:
        print("Student not found.")
        return
    student["name"] = input(f"Name [{student['name']}]: ").strip() or student["name"]
    student["branch"] = input(f"Branch [{student['branch']}]: ").strip() or student["branch"]
    new_marks = input(f"Marks [{student['marks']}]: ").strip()
    if new_marks:
        try:
            student["marks"] = float(new_marks)
        except ValueError:
            print("Invalid marks, keeping old value.")
    print("Student updated.")


def delete_student(students):
    student = find_student(students, read_int("Roll No to delete: "))
    if student:
        students.remove(student)
        print("Student deleted.")
    else:
        print("Student not found.")


def search_by_name(students):
    keyword = input("Search name: ").strip().lower()
    matches = [s for s in students if keyword in s["name"].lower()]  # list comprehension
    view_students(matches)


def show_topper(students):
    if students:
        top = max(students, key=lambda s: s["marks"])
        print(f"Topper: {top['name']} ({top['marks']})")
    else:
        print("No records found.")


# ---------- Main ----------
MENU = """
===== Student Record Management =====
1. Add student      2. View all        3. Update
4. Delete           5. Search by name  6. Show topper
7. Export CSV       8. Import CSV      9. Exit
"""


def main():
    students = load_students()
    actions = {
        "1": add_student, "2": view_students, "3": update_student,
        "4": delete_student, "5": search_by_name, "6": show_topper,
    }
    try:
        while True:
            print(MENU)
            choice = input("Choose an option: ").strip()
            if choice in actions:
                actions[choice](students)
                save_students(students)
            elif choice == "7":
                export_csv(students)
            elif choice == "8":
                students = import_csv() or students
                save_students(students)
            elif choice == "9":
                break
            else:
                print("Invalid choice.")
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        save_students(students)
        print("Data saved. Goodbye!")


if __name__ == "__main__":
    main()