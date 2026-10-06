# Student Record Management System

A Python-based Student Record Management System created as part of the Codomax Python Fundamentals internship module.

## Features

- Add student records
- View all student records
- Search students by roll number or name
- Update student records
- Delete student records
- Calculate student grades
- Display student statistics
- Store records in a JSON file
- Input validation and exception handling

## Python Concepts Used

- Variables
- Data types
- Operators
- Input and output
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

## Project Structure

```text
Student-Record-Management/
│
├── student_management.py
├── README.md
└── students.json
classDiagram
    class Account {
        <<abstract>>
        +account_no
        +holder
        -__balance
        +balance* (read-only)
        +deposit(amount)
        +withdraw(amount)
        +get_history() list
        +available_to_withdraw()* float
        +account_type* str
    }
    class SavingsAccount {
        +MIN_BALANCE = 500
        +INTEREST_RATE = 0.04
        +available_to_withdraw() float
        +apply_interest()
    }
    class CurrentAccount {
        +OVERDRAFT_LIMIT = 5000
        +available_to_withdraw() float
    }
    class Transaction {
        <<dataclass, frozen>>
        +kind
        +amount
        +balance_after
        +timestamp
    }
    class Bank {
        +name
        -_accounts : dict
        +create_account(holder, kind, opening_balance) Account
        +get_account(account_no) Account
        +transfer(from_no, to_no, amount)
        +all_accounts() list
    }
    class BankError {
        <<exception>>
    }
    BankError <|-- InvalidAmountError
    BankError <|-- InsufficientFundsError
    BankError <|-- AccountNotFoundError

    Account <|-- SavingsAccount
    Account <|-- CurrentAccount
    Account "1" o-- "*" Transaction : records
    Bank "1" o-- "*" Account : manages