"""Unit tests for to-do list GUI application."""

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main import TodoDatabase, TodoListGUI


class TestTodoDatabase(unittest.TestCase):
    """Test cases for TodoDatabase class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_todo.db")

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_creates_tables(self) -> None:
        """Test that initialization creates database tables."""
        db = TodoDatabase(self.db_path)
        self.assertTrue(os.path.exists(self.db_path))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='tasks'
        """)
        table = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(table)
        self.assertEqual(table[0], "tasks")

    def test_add_task(self) -> None:
        """Test adding a task to database."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Test Task", "Test Description", "high", "2024-12-31")

        self.assertIsNotNone(task_id)
        self.assertIsInstance(task_id, int)

        # Verify in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[1], "Test Task")
        self.assertEqual(row[2], "Test Description")
        self.assertEqual(row[3], "high")
        self.assertEqual(row[4], "2024-12-31")

    def test_add_task_minimal(self) -> None:
        """Test adding a task with only title."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Minimal Task")

        self.assertIsNotNone(task_id)

        task = db.get_task(task_id)
        self.assertEqual(task["title"], "Minimal Task")
        self.assertEqual(task["priority"], "medium")
        self.assertIsNone(task["due_date"])

    def test_get_tasks_all(self) -> None:
        """Test getting all tasks."""
        db = TodoDatabase(self.db_path)

        # Add multiple tasks
        db.add_task("Task 1", priority="high")
        db.add_task("Task 2", priority="medium")
        db.add_task("Task 3", priority="low")

        tasks = db.get_tasks()
        self.assertEqual(len(tasks), 3)

    def test_get_tasks_filter_completed(self) -> None:
        """Test filtering tasks by completion status."""
        db = TodoDatabase(self.db_path)

        task1_id = db.add_task("Incomplete Task")
        task2_id = db.add_task("Complete Task")

        db.toggle_complete(task2_id)

        incomplete = db.get_tasks(filter_completed=False)
        complete = db.get_tasks(filter_completed=True)

        self.assertEqual(len(incomplete), 1)
        self.assertEqual(len(complete), 1)
        self.assertEqual(incomplete[0]["title"], "Incomplete Task")
        self.assertEqual(complete[0]["title"], "Complete Task")

    def test_get_tasks_filter_priority(self) -> None:
        """Test filtering tasks by priority."""
        db = TodoDatabase(self.db_path)

        db.add_task("High Task", priority="high")
        db.add_task("Medium Task", priority="medium")
        db.add_task("Low Task", priority="low")

        high_tasks = db.get_tasks(filter_priority="high")
        medium_tasks = db.get_tasks(filter_priority="medium")
        low_tasks = db.get_tasks(filter_priority="low")

        self.assertEqual(len(high_tasks), 1)
        self.assertEqual(len(medium_tasks), 1)
        self.assertEqual(len(low_tasks), 1)

    def test_update_task(self) -> None:
        """Test updating a task."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Original Title", "Original Description", "low")

        # Update task
        result = db.update_task(
            task_id,
            title="Updated Title",
            description="Updated Description",
            priority="high",
        )

        self.assertTrue(result)

        task = db.get_task(task_id)
        self.assertEqual(task["title"], "Updated Title")
        self.assertEqual(task["description"], "Updated Description")
        self.assertEqual(task["priority"], "high")

    def test_update_task_partial(self) -> None:
        """Test updating only some fields of a task."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Original Title", "Original Description", "low")

        # Update only title
        result = db.update_task(task_id, title="Updated Title")

        self.assertTrue(result)

        task = db.get_task(task_id)
        self.assertEqual(task["title"], "Updated Title")
        self.assertEqual(task["description"], "Original Description")
        self.assertEqual(task["priority"], "low")

    def test_toggle_complete(self) -> None:
        """Test toggling task completion status."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Test Task")

        # Initially incomplete
        task = db.get_task(task_id)
        self.assertEqual(task["completed"], 0)
        self.assertIsNone(task["completed_at"])

        # Toggle to complete
        result = db.toggle_complete(task_id)
        self.assertTrue(result)

        task = db.get_task(task_id)
        self.assertEqual(task["completed"], 1)
        self.assertIsNotNone(task["completed_at"])

        # Toggle back to incomplete
        db.toggle_complete(task_id)
        task = db.get_task(task_id)
        self.assertEqual(task["completed"], 0)

    def test_delete_task(self) -> None:
        """Test deleting a task."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Task to Delete")

        result = db.delete_task(task_id)
        self.assertTrue(result)

        task = db.get_task(task_id)
        self.assertIsNone(task)

    def test_delete_nonexistent_task(self) -> None:
        """Test deleting a task that doesn't exist."""
        db = TodoDatabase(self.db_path)

        result = db.delete_task(999)
        self.assertFalse(result)

    def test_get_task(self) -> None:
        """Test getting a single task by ID."""
        db = TodoDatabase(self.db_path)
        task_id = db.add_task("Test Task", "Description", "high", "2024-12-31")

        task = db.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task["title"], "Test Task")
        self.assertEqual(task["description"], "Description")
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["due_date"], "2024-12-31")

    def test_get_nonexistent_task(self) -> None:
        """Test getting a task that doesn't exist."""
        db = TodoDatabase(self.db_path)

        task = db.get_task(999)
        self.assertIsNone(task)


class TestTodoListGUI(unittest.TestCase):
    """Test cases for TodoListGUI class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.yaml")
        self.db_path = os.path.join(self.temp_dir, "test_todo.db")

        # Create test config
        config_content = f"""
database:
  file: "{self.db_path}"
  create_tables: true

logging:
  level: "DEBUG"
  file: "{os.path.join(self.temp_dir, 'test.log')}"
  max_bytes: 1048576
  backup_count: 3
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
"""
        with open(self.config_path, "w") as f:
            f.write(config_content)

    def tearDown(self) -> None:
        """Clean up test fixtures."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch("src.main.Tk")
    def test_init_loads_config(self, mock_tk) -> None:
        """Test that initialization loads configuration correctly."""
        app = TodoListGUI(config_path=self.config_path)
        self.assertEqual(app.config["database"]["file"], self.db_path)
        self.assertIsNotNone(app.db)

    @patch("src.main.Tk")
    def test_init_creates_database(self, mock_tk) -> None:
        """Test that initialization creates database."""
        app = TodoListGUI(config_path=self.config_path)
        self.assertTrue(os.path.exists(self.db_path))

    def test_config_file_not_found(self) -> None:
        """Test error handling for missing config file."""
        with self.assertRaises(FileNotFoundError):
            TodoListGUI(config_path="nonexistent_config.yaml")


if __name__ == "__main__":
    unittest.main()
