# API Documentation

## TodoDatabase Class

Manages SQLite database for to-do tasks.

### Methods

#### `__init__(db_path: str) -> None`

Initialize database connection.

**Parameters:**
- `db_path`: Path to SQLite database file

---

#### `add_task(title: str, description: str = "", priority: str = "medium", due_date: Optional[str] = None) -> int`

Add a new task to the database.

**Parameters:**
- `title`: Task title (required)
- `description`: Task description (optional)
- `priority`: Task priority - "low", "medium", or "high" (default: "medium")
- `due_date`: Due date in ISO format YYYY-MM-DD (optional)

**Returns:**
ID of the created task

**Raises:**
- `sqlite3.Error`: If database operation fails

---

#### `get_tasks(filter_completed: Optional[bool] = None, filter_priority: Optional[str] = None) -> List[Dict[str, any]]`

Get tasks from database.

**Parameters:**
- `filter_completed`: Filter by completion status (True/False/None)
- `filter_priority`: Filter by priority ("low"/"medium"/"high"/None)

**Returns:**
List of task dictionaries with keys:
- `id`: Task ID
- `title`: Task title
- `description`: Task description
- `priority`: Task priority
- `due_date`: Due date (ISO format)
- `completed`: Completion status (0 or 1)
- `created_at`: Creation timestamp
- `completed_at`: Completion timestamp (or None)

---

#### `update_task(task_id: int, title: Optional[str] = None, description: Optional[str] = None, priority: Optional[str] = None, due_date: Optional[str] = None) -> bool`

Update a task.

**Parameters:**
- `task_id`: Task ID
- `title`: New title (optional)
- `description`: New description (optional)
- `priority`: New priority (optional)
- `due_date`: New due date (optional)

**Returns:**
True if updated successfully, False otherwise

---

#### `toggle_complete(task_id: int) -> bool`

Toggle task completion status.

**Parameters:**
- `task_id`: Task ID

**Returns:**
True if toggled successfully, False otherwise

---

#### `delete_task(task_id: int) -> bool`

Delete a task.

**Parameters:**
- `task_id`: Task ID

**Returns:**
True if deleted successfully, False otherwise

---

#### `get_task(task_id: int) -> Optional[Dict[str, any]]`

Get a single task by ID.

**Parameters:**
- `task_id`: Task ID

**Returns:**
Task dictionary or None if not found

---

## TodoListGUI Class

Main GUI application for to-do list management.

### Methods

#### `__init__(config_path: str = "config.yaml") -> None`

Initialize GUI application.

**Parameters:**
- `config_path`: Path to configuration file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist

---

#### `run() -> None`

Start the GUI application main loop.

---

#### `_add_task() -> None`

Add a new task (internal method, called by GUI).

Validates input and adds task to database.

---

#### `_refresh_task_list() -> None`

Refresh the task list display (internal method).

Updates listbox with current tasks from database.

---

#### `_toggle_complete() -> None`

Toggle completion status of selected task (internal method).

---

#### `_edit_task() -> None`

Edit selected task (internal method).

Opens edit window for task modification.

---

#### `_delete_task() -> None`

Delete selected task (internal method).

Prompts for confirmation before deletion.

---

#### `_view_task_details() -> None`

View details of selected task (internal method).

Opens details window with complete task information.

---

#### `_set_filter(completed: Optional[bool], priority: Optional[str]) -> None`

Set filter for task list (internal method).

**Parameters:**
- `completed`: Filter by completion status
- `priority`: Filter by priority
