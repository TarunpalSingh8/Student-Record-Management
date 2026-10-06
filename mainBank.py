from bank import Bank, SavingsAccount, BankError

MENU = """
===== Python Banking System =====
1. Create account   2. Deposit        3. Withdraw
4. Check balance    5. Transfer       6. Transaction history
7. Apply interest (Savings)           8. List accounts
9. Exit
"""


def ask_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def ask_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter a valid number.")


def main():
    bank = Bank("PyBank")
    while True:
        print(MENU)
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                name = input("Holder name: ").strip()
                kind = input("Type (savings/current): ").strip().lower()
                opening = ask_float("Opening balance: ")
                acc = bank.create_account(name, kind, opening)
                print(f"Created: {acc}")
            elif choice == "2":
                acc = bank.get_account(ask_int("Account no: "))
                acc.deposit(ask_float("Amount: "))
                print(acc)
            elif choice == "3":
                acc = bank.get_account(ask_int("Account no: "))
                acc.withdraw(ask_float("Amount: "))
                print(acc)
            elif choice == "4":
                print(bank.get_account(ask_int("Account no: ")))
            elif choice == "5":
                src = ask_int("From account: ")
                dst = ask_int("To account: ")
                bank.transfer(src, dst, ask_float("Amount: "))
                print("Transfer successful.")
            elif choice == "6":
                acc = bank.get_account(ask_int("Account no: "))
                history = acc.get_history()
                print("\n".join(map(str, history)) if history else "No transactions yet.")
            elif choice == "7":
                acc = bank.get_account(ask_int("Account no: "))
                if isinstance(acc, SavingsAccount):
                    acc.apply_interest()
                    print(f"Interest applied. {acc}")
                else:
                    print("Interest applies only to Savings accounts.")
            elif choice == "8":
                for acc in bank.all_accounts():
                    print(acc)  # polymorphism: each type prints itself
            elif choice == "9":
                print("Thank you for banking with us!")
                break
            else:
                print("Invalid choice.")
        except BankError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
    