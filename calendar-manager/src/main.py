"""Calendar Manager - Local calendar system using iCal files.

This module provides functionality to manage a local calendar system using iCal
files, allowing users to add events, view schedules, and receive reminders
via desktop notifications.
"""

import logging
import logging.handlers
import os
import shutil
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv
from icalendar import Calendar, Event, vText

try:
    from tkinter import (
        Button,
        Entry,
        Frame,
        Label,
        Listbox,
        Scrollbar,
        StringVar,
        Text,
        Tk,
        messagebox,
        ttk,
    )
    from tkcalendar import DateEntry
except ImportError:
    Tk = None
    messagebox = None
    DateEntry = None

try:
    from plyer import notification
except ImportError:
    notification = None

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CalendarManager:
    """Manages calendar events using iCal files."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize CalendarManager with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_calendar_file()
        self.calendar: Optional[Calendar] = None
        self.events: List[Dict] = []
        self.reminder_thread: Optional[threading.Thread] = None
        self.running = False
        self.sent_reminders: set = set()  # Track sent reminders

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
        if os.getenv("CALENDAR_FILE"):
            config["calendar"]["file"] = os.getenv("CALENDAR_FILE")
        if os.getenv("REMINDER_CHECK_INTERVAL"):
            config["reminders"]["check_interval"] = int(os.getenv("REMINDER_CHECK_INTERVAL"))
        if os.getenv("NOTIFICATIONS_ENABLED"):
            config["notifications"]["enabled"] = (
                os.getenv("NOTIFICATIONS_ENABLED").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/calendar_manager.log")

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

    def _setup_calendar_file(self) -> None:
        """Set up calendar file path and create if needed."""
        calendar_file = self.config["calendar"]["file"]
        calendar_path = Path(calendar_file)
        if not calendar_path.is_absolute():
            project_root = Path(__file__).parent.parent
            calendar_path = project_root / calendar_file

        calendar_path.parent.mkdir(parents=True, exist_ok=True)
        self.calendar_path = calendar_path

        if not calendar_path.exists() and self.config["calendar"].get("create_if_missing", True):
            # Create empty calendar
            cal = Calendar()
            cal.add("prodid", "-//Calendar Manager//EN")
            cal.add("version", "2.0")

            with open(calendar_path, "wb") as f:
                f.write(cal.to_ical())

            logger.info(f"Created new calendar file: {calendar_path}")

    def _backup_calendar(self) -> None:
        """Create backup of calendar file."""
        if not self.config["calendar"].get("backup_enabled", True):
            return

        try:
            backup_dir = self.calendar_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"calendar_{timestamp}.ics.bak"

            shutil.copy2(self.calendar_path, backup_file)

            # Clean up old backups
            backup_count = self.config["calendar"].get("backup_count", 5)
            backups = sorted(backup_dir.glob("calendar_*.ics.bak"), reverse=True)
            for old_backup in backups[backup_count:]:
                old_backup.unlink()

            logger.debug(f"Calendar backed up to: {backup_file}")

        except Exception as e:
            logger.warning(f"Failed to backup calendar: {e}")

    def load_calendar(self) -> bool:
        """Load calendar from iCal file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            with open(self.calendar_path, "rb") as f:
                self.calendar = Calendar.from_ical(f.read())

            self.events = []
            for component in self.calendar.walk():
                if component.name == "VEVENT":
                    event_dict = self._parse_event(component)
                    if event_dict:
                        self.events.append(event_dict)

            logger.info(f"Loaded {len(self.events)} event(s) from calendar")
            return True

        except FileNotFoundError:
            logger.warning("Calendar file not found, creating new one")
            self.calendar = Calendar()
            self.calendar.add("prodid", "-//Calendar Manager//EN")
            self.calendar.add("version", "2.0")
            self.events = []
            return True
        except Exception as e:
            logger.error(f"Error loading calendar: {e}", exc_info=True)
            return False

    def _parse_event(self, event: Event) -> Optional[Dict]:
        """Parse iCal event component to dictionary.

        Args:
            event: iCal event component.

        Returns:
            Event dictionary or None if parsing fails.
        """
        try:
            dtstart = event.get("dtstart")
            dtend = event.get("dtend")
            summary = str(event.get("summary", ""))
            description = str(event.get("description", ""))
            location = str(event.get("location", ""))
            uid = str(event.get("uid", ""))

            # Get reminder (VALARM)
            reminder_minutes = None
            for component in event.walk():
                if component.name == "VALARM":
                    trigger = component.get("trigger")
                    if trigger:
                        # Parse trigger (usually "-PT15M" format)
                        trigger_str = str(trigger)
                        if trigger_str.startswith("-PT"):
                            minutes_str = trigger_str[3:-1]
                            try:
                                reminder_minutes = int(minutes_str)
                            except ValueError:
                                pass

            return {
                "uid": uid,
                "summary": summary,
                "description": description,
                "location": location,
                "dtstart": dtstart.dt if dtstart else None,
                "dtend": dtend.dt if dtend else None,
                "reminder_minutes": reminder_minutes,
            }

        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            return None

    def save_calendar(self) -> bool:
        """Save calendar to iCal file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            self._backup_calendar()

            # Rebuild calendar from events
            self.calendar = Calendar()
            self.calendar.add("prodid", "-//Calendar Manager//EN")
            self.calendar.add("version", "2.0")

            for event_dict in self.events:
                event = Event()
                event.add("uid", event_dict.get("uid", ""))
                event.add("summary", event_dict.get("summary", ""))
                event.add("description", event_dict.get("description", ""))
                event.add("location", event_dict.get("location", ""))

                if event_dict.get("dtstart"):
                    event.add("dtstart", event_dict["dtstart"])
                if event_dict.get("dtend"):
                    event.add("dtend", event_dict["dtend"])

                # Add reminder if configured
                reminder_minutes = event_dict.get("reminder_minutes")
                if reminder_minutes:
                    alarm = Event()
                    alarm.add("action", "DISPLAY")
                    alarm.add("description", event_dict.get("summary", "Reminder"))
                    alarm.add("trigger", timedelta(minutes=-reminder_minutes))
                    event.add_component(alarm)

                self.calendar.add_component(event)

            with open(self.calendar_path, "wb") as f:
                f.write(self.calendar.to_ical())

            logger.info(f"Saved {len(self.events)} event(s) to calendar")
            return True

        except Exception as e:
            logger.error(f"Error saving calendar: {e}", exc_info=True)
            return False

    def add_event(
        self,
        summary: str,
        dtstart: datetime,
        dtend: Optional[datetime] = None,
        description: str = "",
        location: str = "",
        reminder_minutes: Optional[int] = None,
    ) -> bool:
        """Add event to calendar.

        Args:
            summary: Event title/summary.
            dtstart: Event start datetime.
            dtend: Event end datetime (optional).
            description: Event description.
            location: Event location.
            reminder_minutes: Reminder time in minutes before event.

        Returns:
            True if successful, False otherwise.
        """
        if not dtend:
            default_duration = self.config.get("event_defaults", {}).get("duration_minutes", 60)
            dtend = dtstart + timedelta(minutes=default_duration)

        if not reminder_minutes:
            reminder_minutes = self.config.get("event_defaults", {}).get("reminder_minutes", 15)

        event_dict = {
            "uid": f"{dtstart.isoformat()}-{summary}",
            "summary": summary,
            "description": description,
            "location": location,
            "dtstart": dtstart,
            "dtend": dtend,
            "reminder_minutes": reminder_minutes,
        }

        self.events.append(event_dict)

        if self.save_calendar():
            logger.info(f"Added event: {summary} at {dtstart}")
            return True

        return False

    def delete_event(self, uid: str) -> bool:
        """Delete event from calendar.

        Args:
            uid: Event UID.

        Returns:
            True if successful, False otherwise.
        """
        original_count = len(self.events)
        self.events = [e for e in self.events if e.get("uid") != uid]

        if len(self.events) < original_count:
            if self.save_calendar():
                logger.info(f"Deleted event: {uid}")
                return True

        return False

    def get_events_for_date(self, date: datetime) -> List[Dict]:
        """Get events for a specific date.

        Args:
            date: Date to get events for.

        Returns:
            List of event dictionaries.
        """
        date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        date_end = date_start + timedelta(days=1)

        matching_events = []
        for event in self.events:
            dtstart = event.get("dtstart")
            if dtstart and date_start <= dtstart < date_end:
                matching_events.append(event)

        return sorted(matching_events, key=lambda x: x.get("dtstart") or datetime.min)

    def _check_reminders(self) -> None:
        """Check for upcoming events and send reminders."""
        if not self.config.get("reminders", {}).get("enabled", True):
            return

        now = datetime.now()
        check_interval = self.config.get("reminders", {}).get("check_interval", 60)

        for event in self.events:
            dtstart = event.get("dtstart")
            if not dtstart:
                continue

            reminder_minutes = event.get("reminder_minutes", 15)
            reminder_time = dtstart - timedelta(minutes=reminder_minutes)

            # Check if reminder time is within check interval
            time_until_reminder = (reminder_time - now).total_seconds()

            if 0 <= time_until_reminder <= check_interval:
                event_id = event.get("uid", "")
                if event_id not in self.sent_reminders:
                    self._send_reminder(event)
                    self.sent_reminders.add(event_id)

        # Clean up old reminders
        self.sent_reminders = {
            eid
            for eid in self.sent_reminders
            if any(e.get("uid") == eid and e.get("dtstart", datetime.max) > now for e in self.events)
        }

    def _send_reminder(self, event: Dict) -> None:
        """Send reminder notification for an event.

        Args:
            event: Event dictionary.
        """
        if not self.config.get("notifications", {}).get("enabled", True):
            return

        summary = event.get("summary", "Event")
        dtstart = event.get("dtstart")
        location = event.get("location", "")

        if dtstart:
            time_str = dtstart.strftime("%Y-%m-%d %H:%M")
            message = f"Event: {summary}\nTime: {time_str}"
            if location:
                message += f"\nLocation: {location}"
        else:
            message = f"Event: {summary}"

        logger.info(f"Reminder: {summary} at {dtstart}")

        if notification:
            try:
                notification.notify(
                    title="Calendar Reminder",
                    message=message,
                    timeout=self.config.get("notifications", {}).get("notification_duration", 10),
                    app_name="Calendar Manager",
                )
            except Exception as e:
                logger.warning(f"Could not send notification: {e}")

    def _reminder_loop(self) -> None:
        """Reminder checking loop."""
        interval = self.config.get("reminders", {}).get("check_interval", 60)

        while self.running:
            try:
                self.load_calendar()
                self._check_reminders()
            except Exception as e:
                logger.error(f"Error in reminder loop: {e}")

            time.sleep(interval)

    def _create_main_window(self) -> None:
        """Create main application window."""
        if Tk is None:
            logger.error("tkinter not available")
            return

        self.root = Tk()
        gui_config = self.config.get("gui", {})
        theme = gui_config.get("theme", {})

        self.root.title(gui_config.get("window_title", "Calendar Manager"))
        self.root.geometry(
            f"{gui_config.get('window_width', 900)}x{gui_config.get('window_height', 700)}"
        )
        self.root.configure(bg=theme.get("background_color", "#FFFFFF"))

        # Main container
        main_frame = Frame(self.root, bg=theme.get("background_color", "#FFFFFF"))
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header_frame = Frame(main_frame, bg=theme.get("header_color", "#2C3E50"))
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = Label(
            header_frame,
            text="Calendar Manager",
            font=("Arial", 18, "bold"),
            bg=theme.get("header_color", "#2C3E50"),
            fg="white",
        )
        title_label.pack(pady=10)

        # Left panel - Event list
        left_panel = Frame(main_frame, bg=theme.get("background_color", "#FFFFFF"))
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        Label(
            left_panel,
            text="Events",
            font=("Arial", 12, "bold"),
            bg=theme.get("background_color", "#FFFFFF"),
            fg=theme.get("text_color", "#333333"),
        ).pack(anchor="w", pady=(0, 5))

        # Event list with scrollbar
        list_frame = Frame(left_panel)
        list_frame.pack(fill="both", expand=True)

        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.event_listbox = Listbox(
            list_frame, yscrollcommand=scrollbar.set, selectmode="single"
        )
        self.event_listbox.pack(side="left", fill="both", expand=True)
        self.event_listbox.bind("<<ListboxSelect>>", lambda e: self._update_details())
        scrollbar.config(command=self.event_listbox.yview)

        # Buttons
        button_frame = Frame(left_panel, bg=theme.get("background_color", "#FFFFFF"))
        button_frame.pack(fill="x", pady=(10, 0))

        Button(
            button_frame,
            text="Add Event",
            command=self._show_add_event_dialog,
            bg=theme.get("button_color", "#3498DB"),
            fg="white",
            font=("Arial", 10),
        ).pack(side="left", padx=2)

        Button(
            button_frame,
            text="Delete",
            command=self._delete_selected_event,
            bg="#E74C3C",
            fg="white",
            font=("Arial", 10),
        ).pack(side="left", padx=2)

        Button(
            button_frame,
            text="Refresh",
            command=self._refresh_display,
            bg="#95A5A6",
            fg="white",
            font=("Arial", 10),
        ).pack(side="left", padx=2)

        # Right panel - Event details
        right_panel = Frame(main_frame, bg=theme.get("background_color", "#FFFFFF"))
        right_panel.pack(side="right", fill="both", expand=True)

        Label(
            right_panel,
            text="Event Details",
            font=("Arial", 12, "bold"),
            bg=theme.get("background_color", "#FFFFFF"),
            fg=theme.get("text_color", "#333333"),
        ).pack(anchor="w", pady=(0, 5))

        self.details_frame = Frame(right_panel, bg=theme.get("background_color", "#FFFFFF"))
        self.details_frame.pack(fill="both", expand=True)

        # Load and display events
        self.load_calendar()
        self._refresh_display()

        logger.info("Main window created")

    def _show_add_event_dialog(self) -> None:
        """Show dialog to add new event."""
        if Tk is None or DateEntry is None:
            return

        dialog = Tk()
        dialog.title("Add Event")
        dialog.geometry("500x400")

        # Form fields
        Frame(dialog).pack(pady=10)

        Label(dialog, text="Title:").pack(anchor="w", padx=20)
        title_var = StringVar()
        Entry(dialog, textvariable=title_var, width=40).pack(padx=20, pady=5)

        Label(dialog, text="Start Date (YYYY-MM-DD):").pack(anchor="w", padx=20, pady=(10, 0))
        use_date_entry = DateEntry is not None
        if use_date_entry:
            start_date = DateEntry(dialog, width=40)
            start_date.pack(padx=20, pady=5)
            start_date_var = None
        else:
            start_date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
            Entry(dialog, textvariable=start_date_var, width=40).pack(padx=20, pady=5)
            start_date = None

        Label(dialog, text="Start Time (HH:MM):").pack(anchor="w", padx=20)
        start_time_var = StringVar(value="09:00")
        Entry(dialog, textvariable=start_time_var, width=40).pack(padx=20, pady=5)

        Label(dialog, text="Duration (minutes):").pack(anchor="w", padx=20)
        duration_var = StringVar(value="60")
        Entry(dialog, textvariable=duration_var, width=40).pack(padx=20, pady=5)

        Label(dialog, text="Location:").pack(anchor="w", padx=20)
        location_var = StringVar()
        Entry(dialog, textvariable=location_var, width=40).pack(padx=20, pady=5)

        Label(dialog, text="Description:").pack(anchor="w", padx=20)
        description_text = Text(dialog, width=40, height=4)
        description_text.pack(padx=20, pady=5)

        Label(dialog, text="Reminder (minutes before):").pack(anchor="w", padx=20)
        reminder_var = StringVar(value="15")
        Entry(dialog, textvariable=reminder_var, width=40).pack(padx=20, pady=5)

        def save_event():
            try:
                title = title_var.get().strip()
                if not title:
                    messagebox.showerror("Error", "Title is required")
                    return

                # Parse date and time
                if use_date_entry:
                    date_obj = start_date.get_date()
                else:
                    date_str = start_date_var.get().strip()
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                time_str = start_time_var.get().strip()
                hour, minute = map(int, time_str.split(":"))
                dtstart = datetime.combine(date_obj, datetime.min.time()).replace(
                    hour=hour, minute=minute
                )

                duration = int(duration_var.get() or "60")
                dtend = dtstart + timedelta(minutes=duration)

                location = location_var.get().strip()
                description = description_text.get("1.0", "end-1c").strip()
                reminder = int(reminder_var.get() or "15")

                if self.add_event(title, dtstart, dtend, description, location, reminder):
                    messagebox.showinfo("Success", "Event added successfully")
                    dialog.destroy()
                    self._refresh_display()
                else:
                    messagebox.showerror("Error", "Failed to add event")

            except Exception as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        Button(dialog, text="Save", command=save_event, bg="#3498DB", fg="white").pack(
            pady=10
        )
        Button(dialog, text="Cancel", command=dialog.destroy).pack()

    def _delete_selected_event(self) -> None:
        """Delete selected event."""
        selection = self.event_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if index < len(self.events):
            event = self.events[index]
            if messagebox.askyesno("Confirm", f"Delete event '{event.get('summary')}'?"):
                if self.delete_event(event.get("uid", "")):
                    self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh event list display."""
        self.load_calendar()
        self.event_listbox.delete(0, "end")

        # Sort events by start time
        sorted_events = sorted(
            self.events, key=lambda x: x.get("dtstart") or datetime.min
        )

        for event in sorted_events:
            dtstart = event.get("dtstart")
            summary = event.get("summary", "Untitled")
            if dtstart:
                display_text = f"{dtstart.strftime('%Y-%m-%d %H:%M')} - {summary}"
            else:
                display_text = summary
            self.event_listbox.insert("end", display_text)

        # Update details
        self._update_details()

    def _update_details(self) -> None:
        """Update event details display."""
        for widget in self.details_frame.winfo_children():
            widget.destroy()

        selection = self.event_listbox.curselection()
        if not selection:
            Label(
                self.details_frame,
                text="Select an event to view details",
                font=("Arial", 10),
            ).pack(pady=20)
            return

        index = selection[0]
        if index < len(self.events):
            event = self.events[index]
            theme = self.config.get("gui", {}).get("theme", {})

            details = [
                f"Title: {event.get('summary', 'N/A')}",
                f"Start: {event.get('dtstart', 'N/A')}",
                f"End: {event.get('dtend', 'N/A')}",
                f"Location: {event.get('location', 'N/A')}",
                f"Reminder: {event.get('reminder_minutes', 'N/A')} minutes before",
            ]

            if event.get("description"):
                details.append(f"Description: {event.get('description')}")

            for detail in details:
                Label(
                    self.details_frame,
                    text=detail,
                    font=("Arial", 9),
                    bg=theme.get("background_color", "#FFFFFF"),
                    fg=theme.get("text_color", "#333333"),
                    justify="left",
                ).pack(anchor="w", pady=2)

    def run(self) -> None:
        """Run the calendar manager application."""
        if Tk is None:
            logger.error("tkinter not available. Cannot run GUI.")
            return

        self._create_main_window()

        # Start reminder thread
        if self.config.get("reminders", {}).get("enabled", True):
            self.running = True
            self.reminder_thread = threading.Thread(target=self._reminder_loop, daemon=True)
            self.reminder_thread.start()

        logger.info("Starting calendar manager application")
        self.root.mainloop()

        # Stop reminder thread
        self.running = False
        logger.info("Calendar manager application closed")


def main() -> int:
    """Main entry point for calendar manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Calendar Manager")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        manager = CalendarManager(config_path=args.config)
        manager.run()
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
