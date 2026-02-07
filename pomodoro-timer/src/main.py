"""Pomodoro Timer - Custom Pomodoro timer with GUI.

This module provides a graphical Pomodoro timer application with work and break
intervals, session tracking, and productivity statistics.
"""

import logging
import logging.handlers
import os
import sqlite3
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

from tkinter import (
    Button,
    Frame,
    Label,
    StringVar,
    Tk,
    ttk,
)

try:
    from plyer import notification
except ImportError:
    # Fallback if plyer not available
    notification = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PomodoroTimer:
    """Pomodoro timer with GUI interface."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PomodoroTimer with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_database()

        # Timer state
        self.current_mode = "work"  # work, short_break, long_break
        self.time_remaining = self.config["intervals"]["work"]
        self.is_running = False
        self.is_paused = False
        self.session_count = 0
        self.timer_thread: Optional[threading.Thread] = None

        # Statistics
        self.stats = {
            "total_sessions": 0,
            "total_work_time": 0,  # in seconds
            "total_break_time": 0,  # in seconds
            "today_sessions": 0,
            "today_work_time": 0,
            "current_streak": 0,  # consecutive days with sessions
        }

        # GUI components
        self.root: Optional[Tk] = None
        self.time_var: Optional[StringVar] = None
        self.mode_var: Optional[StringVar] = None
        self.stats_var: Optional[StringVar] = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
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
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("WORK_INTERVAL"):
            config["intervals"]["work"] = int(os.getenv("WORK_INTERVAL"))
        if os.getenv("SHORT_BREAK_INTERVAL"):
            config["intervals"]["short_break"] = int(os.getenv("SHORT_BREAK_INTERVAL"))
        if os.getenv("LONG_BREAK_INTERVAL"):
            config["intervals"]["long_break"] = int(os.getenv("LONG_BREAK_INTERVAL"))

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/pomodoro_timer.log")

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

        logger.info("Logging configured successfully")

    def _setup_database(self) -> None:
        """Set up SQLite database and create tables if needed."""
        db_file = self.config["database"]["file"]
        db_path = Path(db_file)
        if not db_path.is_absolute():
            project_root = Path(__file__).parent.parent
            db_path = project_root / db_file

        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path

        if self.config["database"].get("create_tables", True):
            self._create_tables()

        self._load_statistics()
        logger.info(f"Database initialized: {db_path}")

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                duration INTEGER NOT NULL,
                completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                date TEXT NOT NULL
            )
        """)

        # Daily statistics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                sessions_completed INTEGER DEFAULT 0,
                work_time_seconds INTEGER DEFAULT 0,
                break_time_seconds INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def _load_statistics(self) -> None:
        """Load statistics from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN session_type = 'work' THEN duration ELSE 0 END) as work_time,
                SUM(CASE WHEN session_type IN ('short_break', 'long_break') THEN duration ELSE 0 END) as break_time
            FROM sessions
        """)
        result = cursor.fetchone()
        if result and result[0]:
            self.stats["total_sessions"] = result[0] or 0
            self.stats["total_work_time"] = result[1] or 0
            self.stats["total_break_time"] = result[2] or 0

        # Today's statistics
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            SELECT 
                COUNT(*) as sessions,
                SUM(CASE WHEN session_type = 'work' THEN duration ELSE 0 END) as work_time
            FROM sessions
            WHERE date = ?
        """, (today,))
        result = cursor.fetchone()
        if result:
            self.stats["today_sessions"] = result[0] or 0
            self.stats["today_work_time"] = result[1] or 0

        conn.close()

    def _save_session(self, session_type: str, duration: int) -> None:
        """Save completed session to database.

        Args:
            session_type: Type of session (work, short_break, long_break).
            duration: Duration in seconds.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")

        # Save session
        cursor.execute("""
            INSERT INTO sessions (session_type, duration, completed_at, date)
            VALUES (?, ?, ?, ?)
        """, (session_type, duration, now.isoformat(), date_str))

        # Update daily statistics
        cursor.execute("""
            INSERT OR IGNORE INTO daily_stats (date, sessions_completed, work_time_seconds, break_time_seconds)
            VALUES (?, 0, 0, 0)
        """, (date_str,))

        if session_type == "work":
            cursor.execute("""
                UPDATE daily_stats
                SET sessions_completed = sessions_completed + 1,
                    work_time_seconds = work_time_seconds + ?
                WHERE date = ?
            """, (duration, date_str))
        else:
            cursor.execute("""
                UPDATE daily_stats
                SET break_time_seconds = break_time_seconds + ?
                WHERE date = ?
            """, (duration, date_str))

        conn.commit()
        conn.close()

        logger.info(f"Saved {session_type} session: {duration} seconds")

    def _format_time(self, seconds: int) -> str:
        """Format seconds as MM:SS.

        Args:
            seconds: Time in seconds.

        Returns:
            Formatted time string.
        """
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def _update_display(self) -> None:
        """Update GUI display with current timer state."""
        if not self.time_var:
            return

        self.time_var.set(self._format_time(self.time_remaining))

        mode_text = {
            "work": "Work Session",
            "short_break": "Short Break",
            "long_break": "Long Break",
        }
        if self.mode_var:
            self.mode_var.set(mode_text.get(self.current_mode, "Work Session"))

        # Update statistics display
        if self.stats_var:
            today_min = self.stats['today_work_time'] // 60
            total_min = self.stats['total_work_time'] // 60
            stats_text = (
                f"Today: {self.stats['today_sessions']} sessions, "
                f"{today_min} min\n"
                f"Total: {self.stats['total_sessions']} sessions, "
                f"{total_min} min"
            )
            self.stats_var.set(stats_text)

        # Update session label
        if hasattr(self, 'session_label'):
            self.session_label.config(
                text=f"Sessions today: {self.stats['today_sessions']}"
            )

    def _timer_loop(self) -> None:
        """Main timer countdown loop."""
        while self.is_running and self.time_remaining > 0:
            if not self.is_paused:
                time.sleep(1)
                self.time_remaining -= 1
                self.root.after(0, self._update_display)
            else:
                time.sleep(0.1)

        if self.is_running and self.time_remaining == 0:
            # Timer completed
            self._on_timer_complete()

    def _on_timer_complete(self) -> None:
        """Handle timer completion."""
        self.is_running = False

        # Get duration
        duration = 0
        if self.current_mode == "work":
            duration = self.config["intervals"]["work"]
        elif self.current_mode == "short_break":
            duration = self.config["intervals"]["short_break"]
        elif self.current_mode == "long_break":
            duration = self.config["intervals"]["long_break"]

        # Save session
        self._save_session(self.current_mode, duration)

        # Update statistics
        if self.current_mode == "work":
            self.stats["total_sessions"] += 1
            self.stats["total_work_time"] += duration
            self.stats["today_sessions"] += 1
            self.stats["today_work_time"] += duration
            self.session_count += 1
        else:
            if self.current_mode == "short_break":
                self.stats["total_break_time"] += duration
            else:
                self.stats["total_break_time"] += duration

        # Send notification
        self._send_notification()

        # Switch to next mode
        self._switch_mode()

        # Update display
        self.root.after(0, self._update_display)

    def _switch_mode(self) -> None:
        """Switch to next timer mode."""
        if self.current_mode == "work":
            # Check if it's time for long break
            sessions_before_long = self.config["intervals"]["sessions_before_long_break"]
            if self.session_count % sessions_before_long == 0:
                self.current_mode = "long_break"
                self.time_remaining = self.config["intervals"]["long_break"]
            else:
                self.current_mode = "short_break"
                self.time_remaining = self.config["intervals"]["short_break"]
        else:
            # Break finished, back to work
            self.current_mode = "work"
            self.time_remaining = self.config["intervals"]["work"]

        logger.info(f"Switched to {self.current_mode} mode")

    def _send_notification(self) -> None:
        """Send notification when timer completes."""
        if not self.config.get("notifications", {}).get("enabled", True):
            return

        mode_text = {
            "work": "Work session complete!",
            "short_break": "Short break complete!",
            "long_break": "Long break complete!",
        }

        title = mode_text.get(self.current_mode, "Timer complete!")
        message = "Time to take a break!" if self.current_mode == "work" else "Time to get back to work!"

        # Desktop notification
        if self.config.get("notifications", {}).get("desktop_notification", True):
            if notification:
                try:
                    notification.notify(
                        title=title,
                        message=message,
                        timeout=self.config.get("notifications", {}).get("notification_duration", 5),
                        app_name="Pomodoro Timer",
                    )
                except Exception as e:
                    logger.warning(f"Could not send notification: {e}")

        # Sound notification
        if self.config.get("notifications", {}).get("sound_on_complete", True):
            try:
                # System beep
                sys.stdout.write("\a")
                sys.stdout.flush()
            except Exception:
                pass

    def _start_timer(self) -> None:
        """Start the timer."""
        if self.is_running:
            return

        self.is_running = True
        self.is_paused = False

        if self.timer_thread and self.timer_thread.is_alive():
            return

        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()

        logger.info(f"Timer started: {self.current_mode} mode")

    def _pause_timer(self) -> None:
        """Pause the timer."""
        if not self.is_running:
            return

        self.is_paused = not self.is_paused
        logger.info(f"Timer {'paused' if self.is_paused else 'resumed'}")

    def _reset_timer(self) -> None:
        """Reset the timer."""
        self.is_running = False
        self.is_paused = False

        # Reset to current mode's default time
        if self.current_mode == "work":
            self.time_remaining = self.config["intervals"]["work"]
        elif self.current_mode == "short_break":
            self.time_remaining = self.config["intervals"]["short_break"]
        elif self.current_mode == "long_break":
            self.time_remaining = self.config["intervals"]["long_break"]

        self._update_display()
        logger.info("Timer reset")

    def _skip_session(self) -> None:
        """Skip current session and move to next."""
        self.is_running = False
        self._switch_mode()
        self.time_remaining = (
            self.config["intervals"]["work"]
            if self.current_mode == "work"
            else (
                self.config["intervals"]["long_break"]
                if self.current_mode == "long_break"
                else self.config["intervals"]["short_break"]
            )
        )
        self._update_display()
        logger.info(f"Skipped to {self.current_mode} mode")

    def _create_main_window(self) -> None:
        """Create main application window."""
        self.root = Tk()
        gui_config = self.config.get("gui", {})
        theme = gui_config.get("theme", {})

        self.root.title(gui_config.get("window_title", "Pomodoro Timer"))
        self.root.geometry(
            f"{gui_config.get('window_width', 500)}x{gui_config.get('window_height', 600)}"
        )
        self.root.configure(bg=theme.get("background_color", "#ECF0F1"))

        # Main container
        main_frame = Frame(self.root, bg=theme.get("background_color", "#ECF0F1"))
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Mode label
        self.mode_var = StringVar(value="Work Session")
        mode_label = Label(
            main_frame,
            textvariable=self.mode_var,
            font=("Arial", 16, "bold"),
            bg=theme.get("background_color", "#ECF0F1"),
            fg=theme.get("text_color", "#2C3E50"),
        )
        mode_label.pack(pady=20)

        # Timer display
        timer_frame = Frame(main_frame, bg=theme.get("background_color", "#ECF0F1"))
        timer_frame.pack(pady=30)

        self.time_var = StringVar(value=self._format_time(self.time_remaining))
        time_label = Label(
            timer_frame,
            textvariable=self.time_var,
            font=("Arial", 48, "bold"),
            bg=theme.get("background_color", "#ECF0F1"),
            fg=theme.get("text_color", "#2C3E50"),
        )
        time_label.pack()

        # Control buttons
        button_frame = Frame(main_frame, bg=theme.get("background_color", "#ECF0F1"))
        button_frame.pack(pady=20)

        start_button = Button(
            button_frame,
            text="Start",
            command=self._start_timer,
            bg=theme.get("button_color", "#3498DB"),
            fg="white",
            font=("Arial", 12),
            width=10,
            height=2,
        )
        start_button.pack(side="left", padx=5)

        pause_button = Button(
            button_frame,
            text="Pause",
            command=self._pause_timer,
            bg=theme.get("button_color", "#3498DB"),
            fg="white",
            font=("Arial", 12),
            width=10,
            height=2,
        )
        pause_button.pack(side="left", padx=5)

        reset_button = Button(
            button_frame,
            text="Reset",
            command=self._reset_timer,
            bg="#95A5A6",
            fg="white",
            font=("Arial", 12),
            width=10,
            height=2,
        )
        reset_button.pack(side="left", padx=5)

        skip_button = Button(
            button_frame,
            text="Skip",
            command=self._skip_session,
            bg="#E67E22",
            fg="white",
            font=("Arial", 12),
            width=10,
            height=2,
        )
        skip_button.pack(side="left", padx=5)

        # Statistics display
        stats_frame = Frame(main_frame, bg=theme.get("background_color", "#ECF0F1"))
        stats_frame.pack(pady=30, fill="both", expand=True)

        Label(
            stats_frame,
            text="Statistics",
            font=("Arial", 14, "bold"),
            bg=theme.get("background_color", "#ECF0F1"),
            fg=theme.get("text_color", "#2C3E50"),
        ).pack(pady=10)

        self.stats_var = StringVar()
        stats_label = Label(
            stats_frame,
            textvariable=self.stats_var,
            font=("Arial", 10),
            bg=theme.get("background_color", "#ECF0F1"),
            fg=theme.get("text_color", "#2C3E50"),
            justify="left",
        )
        stats_label.pack()

        # Session counter (will be updated dynamically)
        self.session_frame = Frame(main_frame, bg=theme.get("background_color", "#ECF0F1"))
        self.session_frame.pack(pady=10)

        self.session_label = Label(
            self.session_frame,
            text=f"Sessions today: {self.stats['today_sessions']}",
            font=("Arial", 10),
            bg=theme.get("background_color", "#ECF0F1"),
            fg=theme.get("text_color", "#2C3E50"),
        )
        self.session_label.pack()

        # Initial display update
        self._update_display()

        logger.info("Main window created")

    def run(self) -> None:
        """Run the Pomodoro timer application."""
        self._create_main_window()
        logger.info("Starting Pomodoro timer application")
        self.root.mainloop()
        logger.info("Pomodoro timer application closed")


def main() -> int:
    """Main entry point for Pomodoro timer."""
    import argparse

    parser = argparse.ArgumentParser(description="Pomodoro Timer")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        timer = PomodoroTimer(config_path=args.config)
        timer.run()
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
