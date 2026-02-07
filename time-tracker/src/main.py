"""Time Tracker - Simple time tracking application with GUI.

This module provides a GUI application for tracking time spent on different
tasks, with the ability to log time entries and generate daily or weekly reports.
"""

import json
import logging
import logging.handlers
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import (
    END,
    Button,
    Entry,
    Frame,
    Label,
    Listbox,
    Menu,
    Scrollbar,
    StringVar,
    Tk,
    messagebox,
    ttk,
)
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TimeTrackerApp:
    """GUI application for time tracking."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize TimeTrackerApp with configuration.

        Args:
            config_path: Path to configuration YAML file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.data_directory = self._get_data_directory()
        self.time_entries: List[Dict[str, Any]] = []
        self.current_task: Optional[str] = None
        self.start_time: Optional[float] = None
        self.timer_running = False
        self.update_thread: Optional[threading.Thread] = None

        # Initialize GUI
        self.root = Tk()
        self._setup_gui()
        self._load_data()
        self._start_timer_updates()

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.
        """
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
            return {
                "app": {"title": "Time Tracker", "window_size": "700x600"},
                "data": {"directory": "data"},
                "logging": {"level": "INFO", "file": "logs/time_tracker.log"},
            }

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/time_tracker.log")

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
            maxBytes=10485760,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        logger.info("Logging configured successfully")

    def _get_data_directory(self) -> Path:
        """Get data directory path.

        Returns:
            Path to data directory.
        """
        data_dir = self.config.get("data", {}).get("directory", "data")
        data_path = Path(data_dir)

        if not data_path.is_absolute():
            project_root = Path(__file__).parent.parent
            data_path = project_root / data_dir

        data_path.mkdir(parents=True, exist_ok=True)
        return data_path

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to human-readable format.

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted time string (HH:MM:SS).
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _setup_gui(self) -> None:
        """Set up the GUI interface."""
        app_title = self.config.get("app", {}).get("title", "Time Tracker")
        self.root.title(app_title)

        window_size = self.config.get("app", {}).get("window_size", "700x600")
        self.root.geometry(window_size)

        # Create menu bar
        self._create_menu_bar()

        # Main container
        main_frame = Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Current task frame
        current_frame = Frame(main_frame)
        current_frame.pack(fill="x", pady=(0, 10))

        Label(current_frame, text="Current Task:", font=("Arial", 12, "bold")).pack(
            anchor="w"
        )
        self.current_task_label = Label(
            current_frame, text="No active task", font=("Arial", 14), fg="gray"
        )
        self.current_task_label.pack(anchor="w", pady=(5, 0))

        # Timer display
        timer_frame = Frame(main_frame)
        timer_frame.pack(fill="x", pady=(0, 10))

        Label(timer_frame, text="Elapsed Time:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.timer_label = Label(
            timer_frame, text="00:00:00", font=("Courier", 24, "bold"), fg="blue"
        )
        self.timer_label.pack(anchor="w", pady=(5, 0))

        # Task input frame
        task_frame = Frame(main_frame)
        task_frame.pack(fill="x", pady=(0, 10))

        Label(task_frame, text="Task Name:").pack(side="left")
        self.task_entry = Entry(task_frame, width=30)
        self.task_entry.pack(side="left", padx=(5, 0), fill="x", expand=True)

        # Control buttons
        button_frame = Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))

        self.start_button = Button(
            button_frame, text="Start", command=self._start_timer, width=10
        )
        self.start_button.pack(side="left", padx=(0, 5))

        self.stop_button = Button(
            button_frame, text="Stop", command=self._stop_timer, width=10, state="disabled"
        )
        self.stop_button.pack(side="left", padx=(0, 5))

        Button(button_frame, text="Log Entry", command=self._log_entry, width=10).pack(
            side="left", padx=(0, 5)
        )

        Button(button_frame, text="Clear", command=self._clear_timer, width=10).pack(
            side="left"
        )

        # Time entries list
        entries_frame = Frame(main_frame)
        entries_frame.pack(fill="both", expand=True)

        Label(entries_frame, text="Time Entries", font=("Arial", 12, "bold")).pack(anchor="w")

        list_frame = Frame(entries_frame)
        list_frame.pack(fill="both", expand=True, pady=(5, 0))

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.entries_listbox = Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.entries_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.entries_listbox.yview)

        # Summary frame
        summary_frame = Frame(main_frame)
        summary_frame.pack(fill="x", pady=(10, 0))

        self.summary_label = Label(
            summary_frame, text="Total time today: 00:00:00", font=("Arial", 10)
        )
        self.summary_label.pack(anchor="w")

        # Status bar
        self.status_var = StringVar(value="Ready")
        status_bar = Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def _create_menu_bar(self) -> None:
        """Create menu bar."""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Generate Daily Report", command=self._generate_daily_report)
        file_menu.add_command(label="Generate Weekly Report", command=self._generate_weekly_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Delete Selected Entry", command=self._delete_entry)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _load_data(self) -> None:
        """Load time entries from data file."""
        entries_file = self.data_directory / "time_entries.json"

        if entries_file.exists():
            try:
                with open(entries_file, "r", encoding="utf-8") as f:
                    self.time_entries = json.load(f)
                logger.info(f"Loaded {len(self.time_entries)} time entry(ies)")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading time entries: {e}")
                self.time_entries = []
        else:
            self.time_entries = []

        self._refresh_entries_display()
        self._update_summary()

    def _save_data(self) -> None:
        """Save time entries to data file."""
        entries_file = self.data_directory / "time_entries.json"

        try:
            with open(entries_file, "w", encoding="utf-8") as f:
                json.dump(self.time_entries, f, indent=2, ensure_ascii=False)
            logger.debug("Saved time entries")
        except IOError as e:
            logger.error(f"Error saving time entries: {e}")

    def _start_timer(self) -> None:
        """Start timer for current task."""
        task_name = self.task_entry.get().strip()

        if not task_name:
            messagebox.showwarning("Warning", "Please enter a task name.")
            return

        if self.timer_running:
            messagebox.showinfo("Info", "Timer is already running. Stop it first.")
            return

        self.current_task = task_name
        self.start_time = time.time()
        self.timer_running = True

        self.current_task_label.config(text=task_name, fg="green")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.task_entry.config(state="disabled")
        self.status_var.set(f"Tracking: {task_name}")

        logger.info(f"Started timer for task: {task_name}")

    def _stop_timer(self) -> None:
        """Stop current timer."""
        if not self.timer_running:
            return

        self.timer_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.task_entry.config(state="normal")

        if self.start_time:
            elapsed = time.time() - self.start_time
            self.status_var.set(f"Stopped. Elapsed: {self._format_time(elapsed)}")
            logger.info(f"Stopped timer for task: {self.current_task}")

        self.current_task = None
        self.start_time = None
        self.current_task_label.config(text="No active task", fg="gray")
        self.timer_label.config(text="00:00:00")

    def _clear_timer(self) -> None:
        """Clear current timer without logging."""
        self._stop_timer()
        self.task_entry.delete(0, END)
        self.status_var.set("Timer cleared")

    def _log_entry(self) -> None:
        """Log current time entry."""
        if not self.timer_running or not self.start_time:
            messagebox.showwarning("Warning", "No active timer to log.")
            return

        elapsed = time.time() - self.start_time

        entry = {
            "task": self.current_task,
            "duration_seconds": elapsed,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": datetime.now().isoformat(),
        }

        self.time_entries.append(entry)
        self._save_data()
        self._refresh_entries_display()
        self._update_summary()

        messagebox.showinfo(
            "Entry Logged",
            f"Logged {self._format_time(elapsed)} for task: {self.current_task}",
        )

        self._stop_timer()
        self.task_entry.delete(0, END)

    def _delete_entry(self) -> None:
        """Delete selected time entry."""
        selection = self.entries_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry to delete.")
            return

        if messagebox.askyesno("Confirm", "Delete selected entry?"):
            index = selection[0]
            if index < len(self.time_entries):
                del self.time_entries[index]
                self._save_data()
                self._refresh_entries_display()
                self._update_summary()
                self.status_var.set("Entry deleted")

    def _refresh_entries_display(self) -> None:
        """Refresh time entries list display."""
        self.entries_listbox.delete(0, END)

        # Sort by timestamp (newest first)
        sorted_entries = sorted(
            self.time_entries, key=lambda x: x.get("timestamp", ""), reverse=True
        )

        for entry in sorted_entries:
            task = entry.get("task", "Unknown")
            duration = self._format_time(entry.get("duration_seconds", 0))
            date = entry.get("date", "Unknown")
            time_str = entry.get("time", "Unknown")

            display = f"{date} {time_str}  {duration:>10s}  {task}"
            self.entries_listbox.insert(END, display)

    def _update_summary(self) -> None:
        """Update summary display."""
        today = datetime.now().strftime("%Y-%m-%d")
        today_total = sum(
            entry.get("duration_seconds", 0)
            for entry in self.time_entries
            if entry.get("date") == today
        )

        self.summary_label.config(text=f"Total time today: {self._format_time(today_total)}")

    def _start_timer_updates(self) -> None:
        """Start timer update thread."""
        def update_loop():
            while True:
                if self.timer_running and self.start_time:
                    elapsed = time.time() - self.start_time
                    self.root.after(0, lambda: self.timer_label.config(
                        text=self._format_time(elapsed)
                    ))
                time.sleep(1)

        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()

    def _generate_daily_report(self) -> None:
        """Generate daily time report."""
        from tkinter import filedialog

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"time_report_{date_str}.txt",
        )

        if not filename:
            return

        report_content = self._create_daily_report(date_str)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)

        messagebox.showinfo("Success", f"Daily report saved to {filename}")

    def _generate_weekly_report(self) -> None:
        """Generate weekly time report."""
        from tkinter import filedialog

        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        date_str = week_start.strftime("%Y-%m-%d")
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"time_report_week_{date_str}.txt",
        )

        if not filename:
            return

        report_content = self._create_weekly_report()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)

        messagebox.showinfo("Success", f"Weekly report saved to {filename}")

    def _create_daily_report(self, date_str: str) -> str:
        """Create daily report content.

        Args:
            date_str: Date string (YYYY-MM-DD).

        Returns:
            Report content as string.
        """
        day_entries = [e for e in self.time_entries if e.get("date") == date_str]

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(f"Daily Time Report - {date_str}")
        report_lines.append("=" * 60)
        report_lines.append("")

        if not day_entries:
            report_lines.append("No time entries for this day.")
            return "\n".join(report_lines)

        # Group by task
        task_totals: Dict[str, float] = {}
        for entry in day_entries:
            task = entry.get("task", "Unknown")
            duration = entry.get("duration_seconds", 0)
            task_totals[task] = task_totals.get(task, 0) + duration

        total_time = sum(task_totals.values())

        report_lines.append("Task Summary")
        report_lines.append("-" * 60)
        for task, duration in sorted(task_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            report_lines.append(
                f"  {task:30s}  {self._format_time(duration):>10s}  ({percentage:5.1f}%)"
            )

        report_lines.append("")
        report_lines.append(f"Total Time: {self._format_time(total_time)}")
        report_lines.append("")

        # Detailed entries
        report_lines.append("Detailed Entries")
        report_lines.append("-" * 60)
        for entry in sorted(day_entries, key=lambda x: x.get("timestamp", "")):
            task = entry.get("task", "Unknown")
            duration = self._format_time(entry.get("duration_seconds", 0))
            time_str = entry.get("time", "Unknown")
            report_lines.append(f"  {time_str:10s}  {duration:>10s}  {task}")

        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def _create_weekly_report(self) -> str:
        """Create weekly report content.

        Returns:
            Report content as string.
        """
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        week_entries = [
            e
            for e in self.time_entries
            if week_start.strftime("%Y-%m-%d")
            <= e.get("date", "")
            <= week_end.strftime("%Y-%m-%d")
        ]

        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(
            f"Weekly Time Report - {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
        )
        report_lines.append("=" * 60)
        report_lines.append("")

        if not week_entries:
            report_lines.append("No time entries for this week.")
            return "\n".join(report_lines)

        # Group by task
        task_totals: Dict[str, float] = {}
        for entry in week_entries:
            task = entry.get("task", "Unknown")
            duration = entry.get("duration_seconds", 0)
            task_totals[task] = task_totals.get(task, 0) + duration

        total_time = sum(task_totals.values())

        report_lines.append("Task Summary (Week)")
        report_lines.append("-" * 60)
        for task, duration in sorted(task_totals.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_time * 100) if total_time > 0 else 0
            report_lines.append(
                f"  {task:30s}  {self._format_time(duration):>10s}  ({percentage:5.1f}%)"
            )

        report_lines.append("")
        report_lines.append(f"Total Time: {self._format_time(total_time)}")
        report_lines.append("")

        # Daily breakdown
        daily_totals: Dict[str, float] = {}
        for entry in week_entries:
            date = entry.get("date", "Unknown")
            duration = entry.get("duration_seconds", 0)
            daily_totals[date] = daily_totals.get(date, 0) + duration

        report_lines.append("Daily Breakdown")
        report_lines.append("-" * 60)
        for date in sorted(daily_totals.keys()):
            duration = daily_totals[date]
            report_lines.append(f"  {date:12s}  {self._format_time(duration):>10s}")

        report_lines.append("")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Time Tracker\n\n"
            "A simple time tracking application for logging time spent on tasks.\n\n"
            "Features:\n"
            "- Start/stop timer for tasks\n"
            "- Log time entries\n"
            "- Generate daily and weekly reports\n\n"
            "Version 1.0",
        )

    def run(self) -> None:
        """Run the application."""
        logger.info("Starting Time Tracker application")
        self.root.mainloop()


def main() -> int:
    """Main entry point for time tracker application."""
    import argparse

    parser = argparse.ArgumentParser(description="Time tracking application with GUI")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = TimeTrackerApp(config_path=args.config)
        app.run()
        return 0

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
