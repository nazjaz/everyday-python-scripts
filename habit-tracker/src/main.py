"""Habit Tracker - GUI application for tracking daily habits.

This module provides a GUI application for tracking daily habits, viewing
streaks, and generating weekly progress reports. Includes data persistence,
streak calculation, and comprehensive logging.
"""

import json
import logging
import logging.handlers
import os
from datetime import datetime, timedelta
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


class HabitDataManager:
    """Manages habit data storage and retrieval."""

    def __init__(self, data_file: Path) -> None:
        """Initialize HabitDataManager.

        Args:
            data_file: Path to JSON data file.
        """
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.habits: Dict[str, Dict] = {}
        self.load_data()

    def load_data(self) -> None:
        """Load habit data from file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.habits = data.get("habits", {})
                logger.info(f"Loaded {len(self.habits)} habits from {self.data_file}")
            else:
                self.habits = {}
                logger.info("No existing data file, starting fresh")
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.habits = {}

    def save_data(self) -> bool:
        """Save habit data to file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            data = {"habits": self.habits, "last_updated": datetime.now().isoformat()}
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.habits)} habits to {self.data_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            return False

    def add_habit(self, name: str, description: str = "") -> bool:
        """Add a new habit.

        Args:
            name: Habit name.
            description: Optional habit description.

        Returns:
            True if successful, False if habit already exists.
        """
        if name in self.habits:
            return False

        self.habits[name] = {
            "description": description,
            "entries": {},
            "created": datetime.now().isoformat(),
        }
        self.save_data()
        logger.info(f"Added habit: {name}")
        return True

    def remove_habit(self, name: str) -> bool:
        """Remove a habit.

        Args:
            name: Habit name to remove.

        Returns:
            True if successful, False if habit doesn't exist.
        """
        if name not in self.habits:
            return False

        del self.habits[name]
        self.save_data()
        logger.info(f"Removed habit: {name}")
        return True

    def log_habit(self, name: str, date: Optional[str] = None) -> bool:
        """Log habit completion for a date.

        Args:
            name: Habit name.
            date: Date string (YYYY-MM-DD) or None for today.

        Returns:
            True if successful, False if habit doesn't exist.
        """
        if name not in self.habits:
            return False

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        self.habits[name]["entries"][date] = True
        self.save_data()
        logger.debug(f"Logged habit {name} for {date}")
        return True

    def unlog_habit(self, name: str, date: Optional[str] = None) -> bool:
        """Remove habit log for a date.

        Args:
            name: Habit name.
            date: Date string (YYYY-MM-DD) or None for today.

        Returns:
            True if successful, False if habit doesn't exist.
        """
        if name not in self.habits:
            return False

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        if date in self.habits[name]["entries"]:
            del self.habits[name]["entries"][date]
            self.save_data()
            logger.debug(f"Unlogged habit {name} for {date}")
        return True

    def is_logged(self, name: str, date: Optional[str] = None) -> bool:
        """Check if habit is logged for a date.

        Args:
            name: Habit name.
            date: Date string (YYYY-MM-DD) or None for today.

        Returns:
            True if logged, False otherwise.
        """
        if name not in self.habits:
            return False

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        return date in self.habits[name]["entries"]

    def get_streak(self, name: str) -> int:
        """Calculate current streak for a habit.

        Args:
            name: Habit name.

        Returns:
            Current streak count in days.
        """
        if name not in self.habits:
            return 0

        entries = self.habits[name]["entries"]
        if not entries:
            return 0

        # Sort dates in descending order
        sorted_dates = sorted(entries.keys(), reverse=True)
        today = datetime.now().date()
        streak = 0

        # Check from today backwards
        current_date = today
        for date_str in sorted_dates:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # If date matches expected date in streak
            if date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif date < current_date:
                # Gap in streak, stop
                break
            # If date > current_date, it's a future date, skip

        return streak

    def get_weekly_stats(self, name: str, week_start: Optional[datetime] = None) -> Dict:
        """Get weekly statistics for a habit.

        Args:
            name: Habit name.
            week_start: Start date of week (defaults to Monday of current week).

        Returns:
            Dictionary with weekly statistics.
        """
        if name not in self.habits:
            return {"completed": 0, "total": 7, "percentage": 0.0}

        if week_start is None:
            today = datetime.now().date()
            days_since_monday = today.weekday()
            week_start = datetime.combine(
                today - timedelta(days=days_since_monday), datetime.min.time()
            )

        week_end = week_start + timedelta(days=6)
        entries = self.habits[name]["entries"]

        completed = 0
        for date_str in entries.keys():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if week_start <= date <= week_end:
                completed += 1

        percentage = (completed / 7) * 100 if completed > 0 else 0.0

        return {
            "completed": completed,
            "total": 7,
            "percentage": percentage,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
        }


class HabitTrackerGUI:
    """GUI application for habit tracking."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize HabitTrackerGUI.

        Args:
            config_path: Path to configuration file.
        """
        if tk is None:
            raise ImportError(
                "tkinter is not available. Please install Python with tkinter support."
            )

        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_data_manager()

        self.root = tk.Tk()
        self.root.title("Habit Tracker")
        self.root.geometry(self.config.get("window_size", "800x600"))

        self.selected_habit = tk.StringVar()
        self.habit_listbox = None

        self._create_widgets()
        self._refresh_habit_list()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return {}

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def _setup_logging(self) -> None:
        """Configure logging."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/habit_tracker.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    def _setup_data_manager(self) -> None:
        """Set up data manager."""
        data_file = self.config.get("data_file", "data/habits.json")
        data_path = Path(data_file)
        if not data_path.is_absolute():
            project_root = Path(__file__).parent.parent
            data_path = project_root / data_file

        self.data_manager = HabitDataManager(data_path)

    def _create_widgets(self) -> None:
        """Create GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Habit list frame
        list_frame = ttk.LabelFrame(main_frame, text="Habits", padding="5")
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.habit_listbox = tk.Listbox(list_frame, height=10)
        self.habit_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.habit_listbox.bind("<<ListboxSelect>>", self._on_habit_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.habit_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.habit_listbox.configure(yscrollcommand=scrollbar.set)

        # Habit management frame
        manage_frame = ttk.LabelFrame(main_frame, text="Manage Habits", padding="5")
        manage_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(manage_frame, text="Habit Name:").grid(row=0, column=0, padx=5)
        self.habit_name_entry = ttk.Entry(manage_frame, width=30)
        self.habit_name_entry.grid(row=0, column=1, padx=5)

        ttk.Label(manage_frame, text="Description:").grid(row=1, column=0, padx=5)
        self.habit_desc_entry = ttk.Entry(manage_frame, width=30)
        self.habit_desc_entry.grid(row=1, column=1, padx=5)

        ttk.Button(manage_frame, text="Add Habit", command=self._add_habit).grid(
            row=2, column=0, padx=5, pady=5
        )
        ttk.Button(manage_frame, text="Remove Habit", command=self._remove_habit).grid(
            row=2, column=1, padx=5, pady=5
        )

        # Logging frame
        log_frame = ttk.LabelFrame(main_frame, text="Log Habit", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(log_frame, text="Selected Habit:").grid(row=0, column=0, padx=5)
        self.selected_label = ttk.Label(log_frame, text="None", foreground="gray")
        self.selected_label.grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Button(log_frame, text="Log Today", command=self._log_today).grid(
            row=1, column=0, padx=5, pady=5
        )
        ttk.Button(log_frame, text="Unlog Today", command=self._unlog_today).grid(
            row=1, column=1, padx=5, pady=5
        )

        # Stats frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="5")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.streak_label = ttk.Label(stats_frame, text="Current Streak: 0 days")
        self.streak_label.grid(row=0, column=0, padx=5, pady=5)

        ttk.Button(stats_frame, text="View Weekly Report", command=self._show_weekly_report).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(stats_frame, text="Export Report", command=self._export_report).grid(
            row=0, column=2, padx=5, pady=5
        )

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

    def _refresh_habit_list(self) -> None:
        """Refresh habit list display."""
        if self.habit_listbox:
            self.habit_listbox.delete(0, tk.END)
            for habit_name in sorted(self.data_manager.habits.keys()):
                self.habit_listbox.insert(tk.END, habit_name)

    def _on_habit_select(self, event: tk.Event) -> None:
        """Handle habit selection."""
        selection = self.habit_listbox.curselection()
        if selection:
            habit_name = self.habit_listbox.get(selection[0])
            self.selected_habit.set(habit_name)
            self.selected_label.config(text=habit_name, foreground="black")
            self._update_stats()
        else:
            self.selected_habit.set("")
            self.selected_label.config(text="None", foreground="gray")

    def _add_habit(self) -> None:
        """Add a new habit."""
        name = self.habit_name_entry.get().strip()
        description = self.habit_desc_entry.get().strip()

        if not name:
            messagebox.showwarning("Warning", "Please enter a habit name")
            return

        if self.data_manager.add_habit(name, description):
            messagebox.showinfo("Success", f"Habit '{name}' added successfully")
            self.habit_name_entry.delete(0, tk.END)
            self.habit_desc_entry.delete(0, tk.END)
            self._refresh_habit_list()
        else:
            messagebox.showerror("Error", f"Habit '{name}' already exists")

    def _remove_habit(self) -> None:
        """Remove selected habit."""
        habit_name = self.selected_habit.get()
        if not habit_name:
            messagebox.showwarning("Warning", "Please select a habit to remove")
            return

        if messagebox.askyesno("Confirm", f"Remove habit '{habit_name}'?"):
            if self.data_manager.remove_habit(habit_name):
                messagebox.showinfo("Success", f"Habit '{habit_name}' removed")
                self.selected_habit.set("")
                self.selected_label.config(text="None", foreground="gray")
                self._refresh_habit_list()
                self._update_stats()

    def _log_today(self) -> None:
        """Log habit for today."""
        habit_name = self.selected_habit.get()
        if not habit_name:
            messagebox.showwarning("Warning", "Please select a habit")
            return

        if self.data_manager.log_habit(habit_name):
            messagebox.showinfo("Success", f"Logged '{habit_name}' for today")
            self._update_stats()
        else:
            messagebox.showerror("Error", "Failed to log habit")

    def _unlog_today(self) -> None:
        """Unlog habit for today."""
        habit_name = self.selected_habit.get()
        if not habit_name:
            messagebox.showwarning("Warning", "Please select a habit")
            return

        if self.data_manager.unlog_habit(habit_name):
            messagebox.showinfo("Success", f"Unlogged '{habit_name}' for today")
            self._update_stats()
        else:
            messagebox.showerror("Error", "Failed to unlog habit")

    def _update_stats(self) -> None:
        """Update statistics display."""
        habit_name = self.selected_habit.get()
        if habit_name:
            streak = self.data_manager.get_streak(habit_name)
            self.streak_label.config(text=f"Current Streak: {streak} days")
        else:
            self.streak_label.config(text="Current Streak: 0 days")

    def _show_weekly_report(self) -> None:
        """Show weekly progress report."""
        habit_name = self.selected_habit.get()
        if not habit_name:
            messagebox.showwarning("Warning", "Please select a habit")
            return

        stats = self.data_manager.get_weekly_stats(habit_name)
        report = (
            f"Weekly Report for '{habit_name}'\n"
            f"Period: {stats['week_start']} to {stats['week_end']}\n"
            f"Completed: {stats['completed']} out of {stats['total']} days\n"
            f"Completion Rate: {stats['percentage']:.1f}%"
        )

        messagebox.showinfo("Weekly Report", report)

    def _export_report(self) -> None:
        """Export weekly report to file."""
        habit_name = self.selected_habit.get()
        if not habit_name:
            messagebox.showwarning("Warning", "Please select a habit")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )

        if filename:
            stats = self.data_manager.get_weekly_stats(habit_name)
            streak = self.data_manager.get_streak(habit_name)

            report = (
                f"Habit Tracker - Weekly Report\n"
                f"{'=' * 50}\n\n"
                f"Habit: {habit_name}\n"
                f"Description: {self.data_manager.habits[habit_name].get('description', 'N/A')}\n\n"
                f"Week Period: {stats['week_start']} to {stats['week_end']}\n"
                f"Days Completed: {stats['completed']} out of {stats['total']}\n"
                f"Completion Rate: {stats['percentage']:.1f}%\n\n"
                f"Current Streak: {streak} days\n\n"
                f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report)
                messagebox.showinfo("Success", f"Report exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export report: {e}")

    def run(self) -> None:
        """Run the GUI application."""
        logger.info("Starting Habit Tracker GUI")
        self.root.mainloop()


def main() -> int:
    """Main entry point for habit tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="Habit Tracker GUI Application")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = HabitTrackerGUI(config_path=args.config)
        app.run()
    except ImportError as e:
        print(f"Error: {e}")
        print("Please ensure tkinter is installed with your Python distribution.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
