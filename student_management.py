"""
Student Record Management System

Topics Covered:
- Variables
- Data types
- Operators
- Input / Output
- Conditional statements
- Loops
- Lists
- Tuples
- Sets
- Dictionaries
- Functions
- File handling
- Exception handling
- JSON
- CRUD operations
"""

import json
import os


# ============================================================
# CONSTANTS
# ============================================================

FILE_NAME = "students.json"

# Tuple: fixed collection of available menu options
MENU_OPTIONS = (
    "Add Student",
    "View Students",
    "Search Student",
    "Update Student",
    "Delete Student",
    "Exit"
)

# Tuple: fixed collection of possible grades
GRADE_SCALE = ("A+", "A", "B", "C", "D", "F")


# ============================================================
# FILE HANDLING
# ============================================================

def load_students():
    """
    Load student records from the JSON file.

    Returns:
        dict: Student records stored as a dictionary.
    """

    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r") as file:
                data = json.load(file)

                # Make sure the loaded data is a dictionary
                if isinstance(data, dict):
                    return data

                print("Invalid data format. Starting with empty records.")

        except (json.JSONDecodeError, OSError):
            print("Could not read saved data. Starting fresh.")

    return {}


def save_students(students):
    """
    Save student records to a JSON file.
    """

    try:
        with open(FILE_NAME, "w") as file:
            json.dump(students, file, indent=4)

    except OSError:
        print("Error: Could not save student records.")


# ============================================================
# MENU
# ============================================================

def display_menu():
    """Display the main menu."""

    print("\n" + "=" * 50)
    print("       STUDENT RECORD MANAGEMENT SYSTEM")
    print("=" * 50)

    # Using a tuple with a loop
    for number, option in enumerate(MENU_OPTIONS, start=1):
        print(f"{number}. {option}")

    print("=" * 50)


# ============================================================
# INPUT VALIDATION
# ============================================================

def get_marks(prompt):
    """
    Keep asking until the user enters valid marks between 0 and 100.
    """

    while True:
        try:
            marks = float(input(prompt))

            # Operators + conditional statements
            if 0 <= marks <= 100:
                return marks

            print("Marks must be between 0 and 100.")

        except ValueError:
            print("Please enter a valid number.")


def get_non_empty_input(prompt):
    """
    Get input and make sure it is not empty.
    """

    while True:
        value = input(prompt).strip()

        if value:
            return value

        print("This field cannot be empty.")


# ============================================================
# GRADE CALCULATION
# ============================================================

def calculate_grade(marks):
    """
    Calculate the grade based on marks.
    """

    if marks >= 90:
        return GRADE_SCALE[0]      # A+
    elif marks >= 80:
        return GRADE_SCALE[1]      # A
    elif marks >= 70:
        return GRADE_SCALE[2]      # B
    elif marks >= 60:
        return GRADE_SCALE[3]      # C
    elif marks >= 50:
        return GRADE_SCALE[4]      # D
    else:
        return GRADE_SCALE[5]      # F


# ============================================================
# DISPLAY STUDENT
# ============================================================

def print_student(roll, data):
    """
    Display one student's information.
    """

    print("-" * 50)
    print(f"Roll No : {roll}")
    print(f"Name    : {data['name']}")
    print(f"Course  : {data['course']}")
    print(
        f"Marks   : {data['marks']} "
        f"(Grade: {calculate_grade(data['marks'])})"
    )
    print("-" * 50)


# ============================================================
# ADD STUDENT
# ============================================================

def add_student(students):
    """
    Add a new student record.
    """

    print("\n--- Add Student ---")

    roll = get_non_empty_input("Enter roll number: ")

    # Check if roll number already exists
    if roll in students:
        print("A student with this roll number already exists.")
        return

    name = get_non_empty_input("Enter name: ").title()
    course = get_non_empty_input("Enter course: ").upper()
    marks = get_marks("Enter marks (0-100): ")

    # Dictionary containing student information
    students[roll] = {
        "name": name,
        "course": course,
        "marks": marks
    }

    save_students(students)

    print(f"Student '{name}' added successfully.")


# ============================================================
# VIEW STUDENTS
# ============================================================

def view_students(students):
    """
    Display all student records and statistics.
    """

    print("\n--- View Students ---")

    if not students:
        print("No records found.")
        return

    print(f"\nTotal students: {len(students)}")

    # List containing all marks
    all_marks = []

    # Set containing unique courses
    courses = set()

    # For loop through dictionary
    for roll, data in students.items():

        print_student(roll, data)

        # Add marks to the list
        all_marks.append(data["marks"])

        # Add course to the set
        courses.add(data["course"])

    # Statistics using list functions
    average = sum(all_marks) / len(all_marks)
    highest = max(all_marks)
    lowest = min(all_marks)

    print("\n--- Statistics ---")
    print(f"Average Marks : {average:.2f}")
    print(f"Highest Marks : {highest}")
    print(f"Lowest Marks  : {lowest}")

    print("\nCourses:")
    print(", ".join(sorted(courses)))


# ============================================================
# SEARCH STUDENT
# ============================================================

def search_student(students):
    """
    Search for a student using roll number or name.
    """

    print("\n--- Search Student ---")

    keyword = input(
        "Enter roll number or name to search: "
    ).strip().lower()

    if not keyword:
        print("Search value cannot be empty.")
        return

    found = False

    # Loop through dictionary
    for roll, data in students.items():

        if (
            keyword == roll.lower()
            or keyword in data["name"].lower()
        ):
            print_student(roll, data)
            found = True

    if not found:
        print("No matching student found.")


# ============================================================
# UPDATE STUDENT
# ============================================================

def update_student(students):
    """
    Update an existing student record.
    """

    print("\n--- Update Student ---")

    roll = input("Enter roll number to update: ").strip()

    if roll not in students:
        print("Student not found.")
        return

    data = students[roll]

    print("\nLeave a field blank to keep the current value.")

    name = input(
        f"Name [{data['name']}]: "
    ).strip()

    course = input(
        f"Course [{data['course']}]: "
    ).strip()

    marks_input = input(
        f"Marks [{data['marks']}]: "
    ).strip()

    # Update name
    if name:
        data["name"] = name.title()

    # Update course
    if course:
        data["course"] = course.upper()

    # Update marks
    if marks_input:

        try:
            marks = float(marks_input)

            if 0 <= marks <= 100:
                data["marks"] = marks
            else:
                print("Invalid marks. Keeping old value.")

        except ValueError:
            print("Invalid marks. Keeping old value.")

    save_students(students)

    print("Record updated successfully.")


# ============================================================
# DELETE STUDENT
# ============================================================

def delete_student(students):
    """
    Delete a student record.
    """

    print("\n--- Delete Student ---")

    roll = input("Enter roll number to delete: ").strip()

    if roll not in students:
        print("Student not found.")
        return

    student_name = students[roll]["name"]

    confirm = input(
        f"Are you sure you want to delete {student_name}? (y/n): "
    ).strip().lower()

    if confirm == "y":

        # Delete dictionary item
        del students[roll]

        save_students(students)

        print("Record deleted successfully.")

    else:
        print("Deletion cancelled.")


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    """
    Main function of the Student Record Management System.
    """

    students = load_students()

    print("\nWelcome to Student Record Management System!")

    while True:

        display_menu()

        try:
            choice = input(
                "Enter your choice (1-6): "
            ).strip()

            # Conditional statements
            if choice == "1":
                add_student(students)

            elif choice == "2":
                view_students(students)

            elif choice == "3":
                search_student(students)

            elif choice == "4":
                update_student(students)

            elif choice == "5":
                delete_student(students)

            elif choice == "6":

                save_students(students)

                print("\nData saved successfully.")
                print("Thank you for using the Student Record Management System!")
                break

            else:
                print(
                    "Invalid choice. "
                    "Please enter a number from 1 to 6."
                )

        except KeyboardInterrupt:

            print("\n\nProgram interrupted.")

            save_students(students)

            print("Data saved. Goodbye!")
            break


# ============================================================
# PROGRAM START
# ============================================================

if __name__ == "__main__":
    main()