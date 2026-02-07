"""Unit tests for Expense Tracker."""

import csv
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import ExpenseDataManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def data_file(temp_dir):
    """Create a temporary data file."""
    return temp_dir / "test_expenses.json"


def test_expense_data_manager_initialization(data_file):
    """Test ExpenseDataManager initialization."""
    manager = ExpenseDataManager(data_file)
    assert manager.data_file == data_file
    assert isinstance(manager.expenses, list)


def test_add_expense(data_file):
    """Test adding an expense."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")
    assert len(manager.expenses) == 1
    assert manager.expenses[0]["category"] == "Food"
    assert manager.expenses[0]["amount"] == 25.50
    assert manager.expenses[0]["description"] == "Lunch"
    assert manager.expenses[0]["date"] == "2024-01-15"


def test_add_multiple_expenses(data_file):
    """Test adding multiple expenses."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")
    manager.add_expense("Transportation", 10.00, "Bus fare", "2024-01-15")
    manager.add_expense("Food", 15.75, "Dinner", "2024-01-16")

    assert len(manager.expenses) == 3
    assert manager.expenses[0]["id"] == 1
    assert manager.expenses[1]["id"] == 2
    assert manager.expenses[2]["id"] == 3


def test_get_summary_by_category(data_file):
    """Test getting summary by category."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")
    manager.add_expense("Food", 15.75, "Dinner", "2024-01-16")
    manager.add_expense("Transportation", 10.00, "Bus fare", "2024-01-15")

    summary = manager.get_summary_by_category()

    assert summary["Food"] == 41.25
    assert summary["Transportation"] == 10.00
    assert len(summary) == 2


def test_get_summary_empty(data_file):
    """Test getting summary with no expenses."""
    manager = ExpenseDataManager(data_file)

    summary = manager.get_summary_by_category()
    assert len(summary) == 0


def test_get_total_spending(data_file):
    """Test getting total spending."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")
    manager.add_expense("Transportation", 10.00, "Bus fare", "2024-01-15")
    manager.add_expense("Food", 15.75, "Dinner", "2024-01-16")

    total = manager.get_total_spending()
    assert total == 51.25


def test_get_total_spending_empty(data_file):
    """Test getting total spending with no expenses."""
    manager = ExpenseDataManager(data_file)

    total = manager.get_total_spending()
    assert total == 0.0


def test_export_to_csv(data_file, temp_dir):
    """Test exporting expenses to CSV."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")
    manager.add_expense("Transportation", 10.00, "Bus fare", "2024-01-15")

    csv_file = temp_dir / "test_export.csv"
    manager.export_to_csv(csv_file)

    assert csv_file.exists()

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[0]["Category"] == "Food"
    assert rows[0]["Amount"] == "25.5"
    assert rows[1]["Category"] == "Transportation"
    assert rows[1]["Amount"] == "10.0"


def test_export_to_csv_empty(data_file, temp_dir):
    """Test exporting empty expense list to CSV."""
    manager = ExpenseDataManager(data_file)

    csv_file = temp_dir / "test_export_empty.csv"
    manager.export_to_csv(csv_file)

    assert csv_file.exists()

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 1  # Only header row
    assert rows[0] == ["ID", "Category", "Amount", "Description", "Date"]


def test_save_and_load_data(data_file):
    """Test saving and loading data."""
    manager = ExpenseDataManager(data_file)
    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")
    manager.add_expense("Transportation", 10.00, "Bus fare", "2024-01-15")

    manager.save_data()

    manager2 = ExpenseDataManager(data_file)

    assert len(manager2.expenses) == 2
    assert manager2.expenses[0]["category"] == "Food"
    assert manager2.expenses[1]["category"] == "Transportation"


def test_load_nonexistent_data_file(temp_dir):
    """Test loading from non-existent file."""
    data_file = temp_dir / "nonexistent.json"

    manager = ExpenseDataManager(data_file)
    assert isinstance(manager.expenses, list)
    assert len(manager.expenses) == 0


def test_expense_has_timestamp(data_file):
    """Test that expenses include timestamp."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25.50, "Lunch", "2024-01-15")

    assert "timestamp" in manager.expenses[0]
    assert isinstance(manager.expenses[0]["timestamp"], str)

    # Verify timestamp is valid ISO format
    datetime.fromisoformat(manager.expenses[0]["timestamp"])


def test_expense_amount_as_float(data_file):
    """Test that expense amounts are stored as floats."""
    manager = ExpenseDataManager(data_file)

    manager.add_expense("Food", 25, "Lunch", "2024-01-15")
    manager.add_expense("Food", 25.50, "Dinner", "2024-01-15")

    assert isinstance(manager.expenses[0]["amount"], float)
    assert isinstance(manager.expenses[1]["amount"], float)
    assert manager.expenses[0]["amount"] == 25.0
    assert manager.expenses[1]["amount"] == 25.50
