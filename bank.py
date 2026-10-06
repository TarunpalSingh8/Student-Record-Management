"""Banking System - core classes.
Demonstrates: classes, objects, constructors, methods, encapsulation,
inheritance, polymorphism, and abstraction.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


# ---------- Custom exceptions ----------
class BankError(Exception):
    """Base class for banking errors."""


class InvalidAmountError(BankError):
    pass


class InsufficientFundsError(BankError):
    pass


class AccountNotFoundError(BankError):
    pass


# ---------- Transaction ----------
@dataclass(frozen=True)
class Transaction:
    kind: str            # DEPOSIT / WITHDRAW / INTEREST / TRANSFER_IN / TRANSFER_OUT
    amount: float
    balance_after: float
    timestamp: datetime

    def __str__(self):
        return (f"{self.timestamp:%Y-%m-%d %H:%M:%S} | {self.kind:<12} | "
                f"{self.amount:>10.2f} | Balance: {self.balance_after:>10.2f}")


# ---------- Abstract Account ----------
class Account(ABC):
    """Abstract base class. Balance is private (encapsulation)."""

    def __init__(self, account_no, holder, opening_balance=0.0):
        if opening_balance < 0:
            raise InvalidAmountError("Opening balance cannot be negative.")
        self.account_no = account_no
        self.holder = holder
        self.__balance = float(opening_balance)
        self._history = []
        if opening_balance:
            self._record("DEPOSIT", opening_balance)

    # read-only access to the private balance
    @property
    def balance(self):
        return self.__balance

    @abstractmethod
    def available_to_withdraw(self):
        """Max amount that can be withdrawn (differs per account type)."""

    @property
    @abstractmethod
    def account_type(self):
        ...

    def deposit(self, amount):
        self._validate(amount)
        self.__balance += amount
        self._record("DEPOSIT", amount)

    def withdraw(self, amount):
        self._validate(amount)
        if amount > self.available_to_withdraw():
            raise InsufficientFundsError(
                f"Insufficient funds. Available: {self.available_to_withdraw():.2f}")
        self.__balance -= amount
        self._record("WITHDRAW", amount)

    def get_history(self):
        return list(self._history)  # copy, so the original stays protected

    def _record(self, kind, amount):
        self._history.append(Transaction(kind, amount, self.__balance, datetime.now()))

    @staticmethod
    def _validate(amount):
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise InvalidAmountError("Amount must be a positive number.")

    def _add_interest(self, amount):
        self.__balance += amount
        self._record("INTEREST", amount)

    def __str__(self):
        return (f"[{self.account_type}] #{self.account_no} | {self.holder} | "
                f"Balance: {self.balance:.2f}")


# ---------- Concrete accounts (inheritance + polymorphism) ----------
class SavingsAccount(Account):
    MIN_BALANCE = 500
    INTEREST_RATE = 0.04  # 4% per year

    @property
    def account_type(self):
        return "Savings"

    def available_to_withdraw(self):
        return max(0, self.balance - self.MIN_BALANCE)

    def apply_interest(self):
        self._add_interest(self.balance * self.INTEREST_RATE / 12)


class CurrentAccount(Account):
    OVERDRAFT_LIMIT = 5000

    @property
    def account_type(self):
        return "Current"

    def available_to_withdraw(self):
        return self.balance + self.OVERDRAFT_LIMIT


# ---------- Bank (manages accounts) ----------
class Bank:
    def __init__(self, name):
        self.name = name
        self._accounts = {}
        self._next_no = 1001

    def create_account(self, holder, kind="savings", opening_balance=0.0):
        classes = {"savings": SavingsAccount, "current": CurrentAccount}
        if kind not in classes:
            raise BankError("Account type must be 'savings' or 'current'.")
        account = classes[kind](self._next_no, holder, opening_balance)
        self._accounts[self._next_no] = account
        self._next_no += 1
        return account

    def get_account(self, account_no):
        try:
            return self._accounts[account_no]
        except KeyError:
            raise AccountNotFoundError(f"Account {account_no} not found.") from None

    def transfer(self, from_no, to_no, amount):
        source, target = self.get_account(from_no), self.get_account(to_no)
        source.withdraw(amount)
        target.deposit(amount)

    def all_accounts(self):
        return list(self._accounts.values())