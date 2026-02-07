"""Expense Tracker - GUI application for tracking expenses by category.

This module provides a GUI application for logging expenses, viewing spending
summaries by category, and exporting expense data to CSV. Includes data
persistence, category-based filtering, and comprehensive logging.
"""

import argparse
import csv
import json
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:
    tk = None
    ttk = None
    messagebox = None
    filedialog = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ExpenseDataManager:
    """Manages expense data storage and retrieval."""

    def __init__(self, data_file: Path) -> None:
        """Initialize ExpenseDataManager.

        Args:
            data_file: Path to JSON data file.
        """
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.expenses: List[Dict] = []
        self.load_data()

    def load_data(self) -> None:
        """Load expense data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
                logger.info(
                    f"Loaded {len(self.expenses)} expenses from {self.data_file}"
                )
            else:
                self.expenses = []
                logger.info(f"Data file not found, starting with empty list")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading data: {e}")
            self.expenses = []
            messagebox.showerror(
                "Error", f"Failed to load expense data: {e}"
            ) if messagebox else None

    def save_data(self) -> None:
        """Save expense data to file."""
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.expenses, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.expenses)} expenses to {self.data_file}")
        except IOError as e:
            logger.error(f"Error saving data: {e}")
            messagebox.showerror(
                "Error", f"Failed to save expense data: {e}"
            ) if messagebox else None

    def add_expense(
        self, category: str, amount: float, description: str, date: str
    ) -> None:
        """Add a new expense.

        Args:
            category: Expense category.
            amount: Expense amount.
            description: Expense description.
            date: Expense date in YYYY-MM-DD format.
        """
        expense = {
            "id": len(self.expenses) + 1,
            "category": category,
            "amount": float(amount),
            "description": description,
            "date": date,
            "timestamp": datetime.now().isoformat(),
        }
        self.expenses.append(expense)
        self.save_data()
        logger.info(f"Added expense: {category} - ${amount:.2f}")

    def get_summary_by_category(self) -> Dict[str, float]:
        """Get spending summary grouped by category.

        Returns:
            Dictionary mapping category names to total amounts.
        """
        summary: Dict[str, float] = {}
        for expense in self.expenses:
            category = expense["category"]
            summary[category] = summary.get(category, 0.0) + expense["amount"]
        return summary

    def get_total_spending(self) -> float:
        """Get total spending across all expenses.

        Returns:
            Total amount spent.
        """
        return sum(expense["amount"] for expense in self.expenses)

    def export_to_csv(self, filepath: Path) -> None:
        """Export expenses to CSV file.

        Args:
            filepath: Path where CSV file will be saved.

        Raises:
            IOError: If file cannot be written.
        """
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                if not self.expenses:
                    writer = csv.writer(f)
                    writer.writerow(["ID", "Category", "Amount", "Description", "Date"])
                    return

                fieldnames = ["ID", "Category", "Amount", "Description", "Date"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for expense in self.expenses:
                    writer.writerow(
                        {
                            "ID": expense["id"],
                            "Category": expense["category"],
                            "Amount": expense["amount"],
                            "Description": expense["description"],
                            "Date": expense["date"],
                        }
                    )

            logger.info(f"Exported {len(self.expenses)} expenses to {filepath}")
        except IOError as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise


class ExpenseTrackerGUI:
    """Main GUI application for expense tracking."""

    def __init__(self, root: tk.Tk, config: Dict) -> None:
        """Initialize ExpenseTrackerGUI.

        Args:
            root: Tkinter root window.
            config: Configuration dictionary.
        """
        self.root = root
        self.config = config
        self.data_manager = ExpenseDataManager(
            Path(config["data_file"])
        )

        self.setup_window()
        self.create_widgets()
        self.refresh_expense_list()
        self.refresh_summary()

    def setup_window(self) -> None:
        """Configure main window properties."""
        self.root.title("Expense Tracker")
        window_size = self.config.get("window_size", "900x700")
        self.root.geometry(window_size)

    def create_widgets(self) -> None:
        """Create and layout all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Add Expense Section
        add_frame = ttk.LabelFrame(main_frame, text="Add Expense", padding="10")
        add_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Category
        ttk.Label(add_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        categories = self.config.get("categories", ["Food", "Transportation", "Other"])
        self.category_combo = ttk.Combobox(
            add_frame, textvariable=self.category_var, values=categories, width=20
        )
        self.category_combo.grid(row=0, column=1, padx=5, pady=5)
        self.category_combo.set(categories[0] if categories else "")

        # Amount
        ttk.Label(add_frame, text="Amount ($):").grid(row=0, column=2, padx=5, pady=5)
        self.amount_var = tk.StringVar()
        amount_entry = ttk.Entry(add_frame, textvariable=self.amount_var, width=15)
        amount_entry.grid(row=0, column=3, padx=5, pady=5)

        # Description
        ttk.Label(add_frame, text="Description:").grid(row=1, column=0, padx=5, pady=5)
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(
            add_frame, textvariable=self.description_var, width=40
        )
        desc_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        # Date
        ttk.Label(add_frame, text="Date:").grid(row=1, column=3, padx=5, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = ttk.Entry(add_frame, textvariable=self.date_var, width=15)
        date_entry.grid(row=1, column=4, padx=5, pady=5)

        # Add Button
        add_button = ttk.Button(
            add_frame, text="Add Expense", command=self.add_expense
        )
        add_button.grid(row=2, column=0, columnspan=5, pady=10)

        # Summary Section
        summary_frame = ttk.LabelFrame(main_frame, text="Spending Summary", padding="10")
        summary_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Summary Treeview
        summary_columns = ("Category", "Amount")
        self.summary_tree = ttk.Treeview(
            summary_frame, columns=summary_columns, show="headings", height=8
        )
        self.summary_tree.heading("Category", text="Category")
        self.summary_tree.heading("Amount", text="Amount ($)")
        self.summary_tree.column("Category", width=200)
        self.summary_tree.column("Amount", width=150)

        scrollbar_summary = ttk.Scrollbar(
            summary_frame, orient=tk.VERTICAL, command=self.summary_tree.yview
        )
        self.summary_tree.configure(yscrollcommand=scrollbar_summary.set)

        self.summary_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_summary.grid(row=0, column=1, sticky=(tk.N, tk.S))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)

        # Total label
        self.total_label = ttk.Label(
            summary_frame, text="Total: $0.00", font=("TkDefaultFont", 10, "bold")
        )
        self.total_label.grid(row=1, column=0, pady=5)

        # Expense List Section
        list_frame = ttk.LabelFrame(main_frame, text="Recent Expenses", padding="10")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Expense Treeview
        expense_columns = ("ID", "Date", "Category", "Amount", "Description")
        self.expense_tree = ttk.Treeview(
            list_frame, columns=expense_columns, show="headings", height=10
        )
        for col in expense_columns:
            self.expense_tree.heading(col, text=col)
            self.expense_tree.column(col, width=100)

        self.expense_tree.column("Description", width=200)
        self.expense_tree.column("ID", width=50)

        scrollbar_expense = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.expense_tree.yview
        )
        self.expense_tree.configure(yscrollcommand=scrollbar_expense.set)

        self.expense_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_expense.grid(row=0, column=1, sticky=(tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        export_button = ttk.Button(
            button_frame, text="Export to CSV", command=self.export_to_csv
        )
        export_button.pack(side=tk.LEFT, padx=5)

        refresh_button = ttk.Button(
            button_frame, text="Refresh", command=self.refresh_all
        )
        refresh_button.pack(side=tk.LEFT, padx=5)

    def add_expense(self) -> None:
        """Handle add expense button click."""
        category = self.category_var.get().strip()
        amount_str = self.amount_var.get().strip()
        description = self.description_var.get().strip()
        date = self.date_var.get().strip()

        if not category:
            messagebox.showerror("Error", "Please select a category")
            return

        if not amount_str:
            messagebox.showerror("Error", "Please enter an amount")
            return

        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be greater than 0")
                return
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number")
            return

        if not description:
            description = "No description"

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror(
                    "Error", "Invalid date format. Please use YYYY-MM-DD"
                )
                return

        self.data_manager.add_expense(category, amount, description, date)
        self.amount_var.set("")
        self.description_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.refresh_all()
        messagebox.showinfo("Success", "Expense added successfully")

    def refresh_expense_list(self) -> None:
        """Refresh the expense list display."""
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)

        for expense in sorted(
            self.data_manager.expenses, key=lambda x: x["date"], reverse=True
        ):
            self.expense_tree.insert(
                "",
                tk.END,
                values=(
                    expense["id"],
                    expense["date"],
                    expense["category"],
                    f"${expense['amount']:.2f}",
                    expense["description"],
                ),
            )

    def refresh_summary(self) -> None:
        """Refresh the spending summary display."""
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        summary = self.data_manager.get_summary_by_category()
        total = self.data_manager.get_total_spending()

        for category, amount in sorted(
            summary.items(), key=lambda x: x[1], reverse=True
        ):
            self.summary_tree.insert(
                "", tk.END, values=(category, f"${amount:.2f}")
            )

        self.total_label.config(text=f"Total: ${total:.2f}")

    def refresh_all(self) -> None:
        """Refresh both expense list and summary."""
        self.refresh_expense_list()
        self.refresh_summary()

    def export_to_csv(self) -> None:
        """Handle export to CSV button click."""
        if not self.data_manager.expenses:
            messagebox.showwarning("Warning", "No expenses to export")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Expenses as CSV",
        )

        if filepath:
            try:
                self.data_manager.export_to_csv(Path(filepath))
                messagebox.showinfo("Success", f"Exported to {filepath}")
            except IOError as e:
                messagebox.showerror("Error", f"Failed to export: {e}")


def setup_logging(config: Dict) -> None:
    """Configure logging based on config file.

    Args:
        config: Configuration dictionary with logging settings.
    """
    log_config = config.get("logging", {})
    log_level = os.getenv("LOG_LEVEL", log_config.get("level", "INFO"))
    log_file = log_config.get("file", "logs/expense_tracker.log")
    max_bytes = log_config.get("max_bytes", 10485760)
    backup_count = log_config.get("backup_count", 5)
    log_format = log_config.get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(log_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)


def load_config(config_path: Optional[Path] = None) -> Dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If config file is invalid.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Override with environment variables if present
    data_file_env = os.getenv("DATA_FILE_PATH")
    if data_file_env:
        config["data_file"] = data_file_env

    return config


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Expense Tracker GUI Application")
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        setup_logging(config)

        if tk is None:
            logger.error("tkinter is not available. Please install python3-tk")
            print("Error: tkinter is not available. Please install python3-tk")
            return

        root = tk.Tk()
        app = ExpenseTrackerGUI(root, config)
        root.mainloop()

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        print(f"Error: {e}")
    except yaml.YAMLError as e:
        logger.error(f"Invalid configuration file: {e}")
        print(f"Error: Invalid configuration file: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
