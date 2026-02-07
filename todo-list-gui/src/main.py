"""To-Do List GUI Application.

This module provides a GUI application for managing to-do lists with task
creation, prioritization, due dates, and completion tracking.
"""

import logging
import logging.handlers
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import (
    END,
    LEFT,
    RIGHT,
    TOP,
    Button,
    Entry,
    Frame,
    Label,
    Listbox,
    Menu,
    Message,
    Scrollbar,
    StringVar,
    Tk,
    Toplevel,
    ttk,
)
from tkinter import messagebox
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class TodoDatabase:
    """Manages SQLite database for to-do tasks."""

    def __init__(self, db_path: str) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._create_tables()

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                due_date TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.debug("Database tables created/verified")

    def add_task(
        self,
        title: str,
        description: str = "",
        priority: str = "medium",
        due_date: Optional[str] = None,
    ) -> int:
        """Add a new task to the database.

        Args:
            title: Task title.
            description: Task description.
            priority: Task priority (low, medium, high).
            due_date: Due date in ISO format.

        Returns:
            ID of the created task.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO tasks (title, description, priority, due_date)
                VALUES (?, ?, ?, ?)
            """, (title, description, priority, due_date))

            task_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added task: {title} (ID: {task_id})")
            return task_id

        except sqlite3.Error as e:
            logger.error(f"Database error adding task: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_tasks(
        self,
        filter_completed: Optional[bool] = None,
        filter_priority: Optional[str] = None,
    ) -> List[Dict[str, any]]:
        """Get tasks from database.

        Args:
            filter_completed: Filter by completion status (True/False/None).
            filter_priority: Filter by priority (low/medium/high/None).

        Returns:
            List of task dictionaries.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM tasks WHERE 1=1"
            params = []

            if filter_completed is not None:
                query += " AND completed = ?"
                params.append(1 if filter_completed else 0)

            if filter_priority:
                query += " AND priority = ?"
                params.append(filter_priority)

            query += " ORDER BY completed ASC, priority DESC, created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            tasks = []
            for row in rows:
                task = dict(row)
                tasks.append(task)

            return tasks

        except sqlite3.Error as e:
            logger.error(f"Database error getting tasks: {e}")
            return []
        finally:
            conn.close()

    def update_task(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> bool:
        """Update a task.

        Args:
            task_id: Task ID.
            title: New title.
            description: New description.
            priority: New priority.
            due_date: New due date.

        Returns:
            True if updated successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if title is not None:
                updates.append("title = ?")
                params.append(title)

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)

            if due_date is not None:
                updates.append("due_date = ?")
                params.append(due_date)

            if not updates:
                return False

            params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"

            cursor.execute(query, params)
            conn.commit()

            logger.info(f"Updated task ID: {task_id}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error updating task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def toggle_complete(self, task_id: int) -> bool:
        """Toggle task completion status.

        Args:
            task_id: Task ID.

        Returns:
            True if toggled successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get current status
            cursor.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()

            if not row:
                return False

            current_status = row[0]
            new_status = 1 if current_status == 0 else 0
            completed_at = datetime.now().isoformat() if new_status == 1 else None

            cursor.execute("""
                UPDATE tasks
                SET completed = ?, completed_at = ?
                WHERE id = ?
            """, (new_status, completed_at, task_id))

            conn.commit()
            logger.info(f"Toggled task {task_id} completion to {new_status}")
            return True

        except sqlite3.Error as e:
            logger.error(f"Database error toggling task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_task(self, task_id: int) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID.

        Returns:
            True if deleted successfully, False otherwise.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

            logger.info(f"Deleted task ID: {task_id}")
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Database error deleting task: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_task(self, task_id: int) -> Optional[Dict[str, any]]:
        """Get a single task by ID.

        Args:
            task_id: Task ID.

        Returns:
            Task dictionary or None if not found.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Database error getting task: {e}")
            return None
        finally:
            conn.close()


class TodoListGUI:
    """Main GUI application for to-do list management."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize GUI application.

        Args:
            config_path: Path to configuration file.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()

        # Initialize database
        db_file = self.config["database"]["file"]
        db_path = Path(db_file)
        if not db_path.is_absolute():
            project_root = Path(__file__).parent.parent
            db_path = project_root / db_file
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db = TodoDatabase(str(db_path))

        # Initialize GUI
        self.root = Tk()
        self.root.title("To-Do List")
        self.root.geometry("800x600")

        # Filter variables
        self.filter_completed = None
        self.filter_priority = None

        self._create_widgets()
        self._refresh_task_list()

        logger.info("To-Do List GUI initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
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

        # Override with environment variables
        if os.getenv("DATABASE_FILE"):
            config["database"]["file"] = os.getenv("DATABASE_FILE")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/todo_list.log")

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

    def _create_widgets(self) -> None:
        """Create and layout GUI widgets."""
        # Menu bar
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Refresh", command=self._refresh_task_list)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Main container
        main_frame = Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # Task input section
        input_frame = Frame(main_frame)
        input_frame.pack(fill="x", pady=(0, 10))

        Label(input_frame, text="New Task", font=("Arial", 12, "bold")).pack(anchor="w")

        task_input_frame = Frame(input_frame)
        task_input_frame.pack(fill="x", pady=5)

        Label(task_input_frame, text="Title:").grid(row=0, column=0, sticky="w", padx=5)
        self.title_entry = Entry(task_input_frame, width=40)
        self.title_entry.grid(row=0, column=1, padx=5, pady=2)

        Label(task_input_frame, text="Priority:").grid(row=0, column=2, sticky="w", padx=5)
        self.priority_var = StringVar(value="medium")
        priority_combo = ttk.Combobox(
            task_input_frame,
            textvariable=self.priority_var,
            values=["low", "medium", "high"],
            state="readonly",
            width=10,
        )
        priority_combo.grid(row=0, column=3, padx=5, pady=2)

        Label(task_input_frame, text="Due Date (YYYY-MM-DD):").grid(
            row=1, column=0, sticky="w", padx=5
        )
        self.due_date_entry = Entry(task_input_frame, width=40)
        self.due_date_entry.grid(row=1, column=1, padx=5, pady=2)

        Label(task_input_frame, text="Description:").grid(row=2, column=0, sticky="nw", padx=5)
        self.description_entry = Entry(task_input_frame, width=40)
        self.description_entry.grid(row=2, column=1, padx=5, pady=2)

        add_button = Button(
            task_input_frame, text="Add Task", command=self._add_task, bg="#4CAF50", fg="white"
        )
        add_button.grid(row=2, column=3, padx=5, pady=2)

        # Filter section
        filter_frame = Frame(main_frame)
        filter_frame.pack(fill="x", pady=(0, 10))

        Label(filter_frame, text="Filters", font=("Arial", 10, "bold")).pack(anchor="w")

        filter_buttons_frame = Frame(filter_frame)
        filter_buttons_frame.pack(fill="x", pady=5)

        Button(
            filter_buttons_frame,
            text="All",
            command=lambda: self._set_filter(None, None),
            width=10,
        ).pack(side=LEFT, padx=2)

        Button(
            filter_buttons_frame,
            text="Active",
            command=lambda: self._set_filter(False, None),
            width=10,
        ).pack(side=LEFT, padx=2)

        Button(
            filter_buttons_frame,
            text="Completed",
            command=lambda: self._set_filter(True, None),
            width=10,
        ).pack(side=LEFT, padx=2)

        Button(
            filter_buttons_frame,
            text="High Priority",
            command=lambda: self._set_filter(None, "high"),
            width=12,
        ).pack(side=LEFT, padx=2)

        Button(
            filter_buttons_frame,
            text="Medium Priority",
            command=lambda: self._set_filter(None, "medium"),
            width=12,
        ).pack(side=LEFT, padx=2)

        Button(
            filter_buttons_frame,
            text="Low Priority",
            command=lambda: self._set_filter(None, "low"),
            width=12,
        ).pack(side=LEFT, padx=2)

        # Task list section
        list_frame = Frame(main_frame)
        list_frame.pack(fill="both", expand=True)

        Label(list_frame, text="Tasks", font=("Arial", 12, "bold")).pack(anchor="w")

        # Listbox with scrollbar
        scrollbar = Scrollbar(list_frame)
        scrollbar.pack(side=RIGHT, fill="y")

        self.task_listbox = Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.task_listbox.pack(side=LEFT, fill="both", expand=True)
        scrollbar.config(command=self.task_listbox.yview)

        # Task actions
        action_frame = Frame(main_frame)
        action_frame.pack(fill="x", pady=(10, 0))

        Button(
            action_frame,
            text="Mark Complete",
            command=self._toggle_complete,
            bg="#2196F3",
            fg="white",
        ).pack(side=LEFT, padx=5)

        Button(
            action_frame,
            text="Edit Task",
            command=self._edit_task,
            bg="#FF9800",
            fg="white",
        ).pack(side=LEFT, padx=5)

        Button(
            action_frame,
            text="Delete Task",
            command=self._delete_task,
            bg="#F44336",
            fg="white",
        ).pack(side=LEFT, padx=5)

        Button(
            action_frame,
            text="View Details",
            command=self._view_task_details,
            bg="#9C27B0",
            fg="white",
        ).pack(side=LEFT, padx=5)

        # Bind double-click to view details
        self.task_listbox.bind("<Double-Button-1>", lambda e: self._view_task_details())

    def _add_task(self) -> None:
        """Add a new task."""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Warning", "Please enter a task title.")
            return

        description = self.description_entry.get().strip()
        priority = self.priority_var.get()
        due_date = self.due_date_entry.get().strip() or None

        # Validate due date format
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                return

        try:
            self.db.add_task(title, description, priority, due_date)
            self.title_entry.delete(0, END)
            self.description_entry.delete(0, END)
            self.due_date_entry.delete(0, END)
            self.priority_var.set("medium")
            self._refresh_task_list()
            logger.info(f"Added task: {title}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add task: {e}")
            logger.error(f"Error adding task: {e}")

    def _refresh_task_list(self) -> None:
        """Refresh the task list display."""
        self.task_listbox.delete(0, END)

        tasks = self.db.get_tasks(
            filter_completed=self.filter_completed, filter_priority=self.filter_priority
        )

        for task in tasks:
            status = "[✓]" if task["completed"] else "[ ]"
            priority_icon = {"high": "!!!", "medium": "!!", "low": "!"}.get(
                task["priority"], ""
            )

            due_info = ""
            if task["due_date"]:
                try:
                    due_date = datetime.fromisoformat(task["due_date"])
                    days_until = (due_date.date() - datetime.now().date()).days
                    if days_until < 0:
                        due_info = f" [OVERDUE: {abs(days_until)} days]"
                    elif days_until == 0:
                        due_info = " [DUE TODAY]"
                    else:
                        due_info = f" [Due in {days_until} days]"
                except (ValueError, TypeError):
                    pass

            display_text = f"{status} {priority_icon} {task['title']}{due_info}"
            self.task_listbox.insert(END, display_text)
            self.task_listbox.itemconfig(END - 1, {"bg": "#E8F5E9" if task["completed"] else "white"})

    def _get_selected_task_id(self) -> Optional[int]:
        """Get the ID of the selected task.

        Returns:
            Task ID or None if no selection.
        """
        selection = self.task_listbox.curselection()
        if not selection:
            return None

        index = selection[0]
        tasks = self.db.get_tasks(
            filter_completed=self.filter_completed, filter_priority=self.filter_priority
        )

        if 0 <= index < len(tasks):
            return tasks[index]["id"]
        return None

    def _toggle_complete(self) -> None:
        """Toggle completion status of selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task.")
            return

        try:
            self.db.toggle_complete(task_id)
            self._refresh_task_list()
            logger.info(f"Toggled completion for task ID: {task_id}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to toggle task: {e}")
            logger.error(f"Error toggling task: {e}")

    def _edit_task(self) -> None:
        """Edit selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task.")
            return

        task = self.db.get_task(task_id)
        if not task:
            messagebox.showerror("Error", "Task not found.")
            return

        # Create edit window
        edit_window = Toplevel(self.root)
        edit_window.title("Edit Task")
        edit_window.geometry("400x300")

        # Title
        Label(edit_window, text="Title:").pack(anchor="w", padx=10, pady=5)
        title_entry = Entry(edit_window, width=50)
        title_entry.insert(0, task["title"])
        title_entry.pack(padx=10, pady=5)

        # Description
        Label(edit_window, text="Description:").pack(anchor="w", padx=10, pady=5)
        desc_entry = Entry(edit_window, width=50)
        desc_entry.insert(0, task["description"] or "")
        desc_entry.pack(padx=10, pady=5)

        # Priority
        Label(edit_window, text="Priority:").pack(anchor="w", padx=10, pady=5)
        priority_var = StringVar(value=task["priority"])
        priority_combo = ttk.Combobox(
            edit_window,
            textvariable=priority_var,
            values=["low", "medium", "high"],
            state="readonly",
            width=47,
        )
        priority_combo.pack(padx=10, pady=5)

        # Due date
        Label(edit_window, text="Due Date (YYYY-MM-DD):").pack(anchor="w", padx=10, pady=5)
        due_entry = Entry(edit_window, width=50)
        if task["due_date"]:
            due_entry.insert(0, task["due_date"])
        due_entry.pack(padx=10, pady=5)

        def save_changes() -> None:
            title = title_entry.get().strip()
            if not title:
                messagebox.showwarning("Warning", "Title cannot be empty.")
                return

            due_date = due_entry.get().strip() or None
            if due_date:
                try:
                    datetime.strptime(due_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD.")
                    return

            try:
                self.db.update_task(
                    task_id,
                    title=title,
                    description=desc_entry.get().strip() or None,
                    priority=priority_var.get(),
                    due_date=due_date,
                )
                self._refresh_task_list()
                edit_window.destroy()
                logger.info(f"Updated task ID: {task_id}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update task: {e}")
                logger.error(f"Error updating task: {e}")

        Button(edit_window, text="Save", command=save_changes, bg="#4CAF50", fg="white").pack(
            pady=10
        )

    def _delete_task(self) -> None:
        """Delete selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task.")
            return

        task = self.db.get_task(task_id)
        if not task:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete '{task['title']}'?"
        )
        if confirm:
            try:
                self.db.delete_task(task_id)
                self._refresh_task_list()
                logger.info(f"Deleted task ID: {task_id}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete task: {e}")
                logger.error(f"Error deleting task: {e}")

    def _view_task_details(self) -> None:
        """View details of selected task."""
        task_id = self._get_selected_task_id()
        if not task_id:
            messagebox.showwarning("Warning", "Please select a task.")
            return

        task = self.db.get_task(task_id)
        if not task:
            messagebox.showerror("Error", "Task not found.")
            return

        # Create details window
        details_window = Toplevel(self.root)
        details_window.title("Task Details")
        details_window.geometry("500x400")

        details_text = f"""
Title: {task['title']}

Description: {task['description'] or 'No description'}

Priority: {task['priority'].upper()}

Status: {'Completed' if task['completed'] else 'Active'}

Due Date: {task['due_date'] or 'No due date'}

Created: {task['created_at']}

Completed: {task['completed_at'] or 'Not completed'}
"""

        Message(details_window, text=details_text, width=450, justify=LEFT).pack(
            padx=20, pady=20, fill="both", expand=True
        )

        Button(details_window, text="Close", command=details_window.destroy).pack(pady=10)

    def _set_filter(self, completed: Optional[bool], priority: Optional[str]) -> None:
        """Set filter for task list.

        Args:
            completed: Filter by completion status.
            priority: Filter by priority.
        """
        self.filter_completed = completed
        self.filter_priority = priority
        self._refresh_task_list()

    def run(self) -> None:
        """Start the GUI application."""
        self.root.mainloop()


def main() -> int:
    """Main entry point for to-do list application."""
    import argparse

    parser = argparse.ArgumentParser(description="To-Do List GUI Application")
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )

    args = parser.parse_args()

    try:
        app = TodoListGUI(config_path=args.config)
        app.run()
        return 0

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
