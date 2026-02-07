# To-Do List GUI

A simple to-do list application with GUI featuring task creation, prioritization, due dates, and completion tracking. Built with Python and tkinter for a clean, user-friendly interface.

## Project Description

To-Do List GUI solves the problem of task management by providing an intuitive graphical interface for creating, organizing, and tracking tasks. Users can create tasks with titles, descriptions, priorities, and due dates, then track their completion status. The application stores all data in a local SQLite database for persistence.

**Target Audience**: Individuals, students, professionals, and anyone who needs a simple, local task management solution without cloud dependencies.

## Features

- **Task Creation**: Create tasks with title, description, priority, and due date
- **Priority Levels**: Set task priority (low, medium, high) with visual indicators
- **Due Date Tracking**: Set and track due dates with overdue warnings
- **Completion Tracking**: Mark tasks as complete/incomplete with visual status
- **Task Filtering**: Filter tasks by completion status or priority level
- **Task Editing**: Edit existing tasks (title, description, priority, due date)
- **Task Deletion**: Delete tasks with confirmation
- **Task Details**: View detailed information about any task
- **Persistent Storage**: All tasks stored in SQLite database
- **Modern GUI**: Clean, intuitive interface built with tkinter
- **Comprehensive Logging**: Log all operations for audit and debugging

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- tkinter (usually included with Python, but may need separate installation on Linux)

### Installing tkinter on Linux

```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

## Installation

### Step 1: Navigate to Project

```bash
cd /Users/nasihjaseem/projects/github/everyday-python-scripts/todo-list-gui
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Settings

Edit `config.yaml` to customize application settings:

```yaml
database:
  file: "data/todo.db"
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **database**: SQLite database file path and table creation settings
- **logging**: Logging level, file path, and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `DATABASE_FILE`: Override database file path

### Example Configuration

```yaml
database:
  file: "data/todo.db"
  create_tables: true

logging:
  level: "INFO"
  file: "logs/todo_list.log"
```

## Usage

### Basic Usage

Start the application:

```bash
python src/main.py
```

The GUI window will open with the following sections:

1. **New Task Section**: Create new tasks with title, description, priority, and due date
2. **Filter Section**: Filter tasks by status (All, Active, Completed) or priority
3. **Task List**: View all tasks with status indicators and due date information
4. **Action Buttons**: Mark complete, edit, delete, or view details of selected tasks

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Show help
python src/main.py --help
```

### GUI Operations

#### Creating a Task

1. Enter task title in the "Title" field (required)
2. Optionally enter description in the "Description" field
3. Select priority from dropdown (low, medium, high)
4. Optionally enter due date in YYYY-MM-DD format
5. Click "Add Task" button

#### Viewing Tasks

- Tasks are displayed in the list with status indicators:
  - `[ ]` = Incomplete task
  - `[✓]` = Completed task
  - `!!!` = High priority
  - `!!` = Medium priority
  - `!` = Low priority
- Due date information shows:
  - `[OVERDUE: N days]` for overdue tasks
  - `[DUE TODAY]` for tasks due today
  - `[Due in N days]` for upcoming tasks

#### Filtering Tasks

Click filter buttons to show:
- **All**: All tasks
- **Active**: Only incomplete tasks
- **Completed**: Only completed tasks
- **High/Medium/Low Priority**: Tasks of specific priority

#### Editing a Task

1. Select a task from the list
2. Click "Edit Task" button
3. Modify fields in the edit window
4. Click "Save" to apply changes

#### Marking Tasks Complete

1. Select a task from the list
2. Click "Mark Complete" button
3. Task status toggles between complete and incomplete

#### Deleting a Task

1. Select a task from the list
2. Click "Delete Task" button
3. Confirm deletion in the dialog

#### Viewing Task Details

1. Select a task from the list
2. Click "View Details" button (or double-click the task)
3. View complete task information in a details window

## Project Structure

```
todo-list-gui/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation
├── data/
│   └── todo.db             # SQLite database (created automatically)
└── logs/
    ├── .gitkeep            # Log directory placeholder
    └── todo_list.log       # Application logs
```

### File Descriptions

- **src/main.py**: Core application code with GUI and database management
- **config.yaml**: YAML configuration file with application settings
- **tests/test_main.py**: Unit tests for core functionality
- **data/todo.db**: SQLite database storing all tasks
- **logs/todo_list.log**: Application log file with rotation

## Database Schema

The SQLite database contains a single table:

### tasks
- `id`: Primary key (auto-increment)
- `title`: Task title (required)
- `description`: Task description (optional)
- `priority`: Task priority (low, medium, high)
- `due_date`: Due date in ISO format (optional)
- `completed`: Completion status (0 = incomplete, 1 = complete)
- `created_at`: Task creation timestamp
- `completed_at`: Task completion timestamp (null if incomplete)

## How It Works

### Task Management

1. **Task Creation**: User enters task details in the input form, which are validated and stored in the database
2. **Task Display**: Tasks are retrieved from the database and displayed in a listbox with status indicators
3. **Task Updates**: Selected tasks can be edited, toggled complete/incomplete, or deleted
4. **Filtering**: Tasks are filtered in the database query based on selected filters

### Priority System

- **High Priority**: Marked with `!!!` indicator
- **Medium Priority**: Marked with `!!` indicator
- **Low Priority**: Marked with `!` indicator

Tasks are sorted by completion status, then priority, then creation date.

### Due Date Tracking

- Due dates are validated to ensure YYYY-MM-DD format
- Overdue tasks are highlighted with `[OVERDUE: N days]`
- Tasks due today show `[DUE TODAY]`
- Upcoming tasks show `[Due in N days]`

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-mock

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Database operations (add, update, delete, get tasks)
- Task filtering
- Task completion toggling
- Data validation
- Error handling

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'tkinter'`

**Solution**: Install tkinter for your Python version:
```bash
# Linux
sudo apt-get install python3-tk

# macOS (usually included)
# If missing, reinstall Python with tkinter support

# Windows (usually included)
# If missing, reinstall Python with tkinter support
```

---

**Issue**: `FileNotFoundError: Configuration file not found`

**Solution**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option.

---

**Issue**: Database locked errors

**Solution**: 
- Ensure only one instance of the application is running
- Check database file permissions
- Close any database viewers that might have the file open

---

**Issue**: GUI window doesn't appear

**Solution**: 
- Check if running in a GUI environment (not headless server)
- Verify tkinter installation
- Check logs for error messages

---

**Issue**: Date validation errors

**Solution**: Ensure dates are entered in YYYY-MM-DD format (e.g., 2024-12-31).

### Error Messages

- **"Please enter a task title"**: Title field is required when creating a task
- **"Invalid date format"**: Due date must be in YYYY-MM-DD format
- **"Please select a task"**: No task selected when performing an action
- **"Task not found"**: Selected task was deleted or database error occurred

## Keyboard Shortcuts

- **Double-click task**: View task details
- **Enter key**: Submit form (when focused on input fields)

## Use Cases

1. **Personal Task Management**: Track daily tasks and to-dos
2. **Project Planning**: Organize tasks for projects with priorities and due dates
3. **Goal Tracking**: Track progress toward goals with completion status
4. **Time Management**: Use due dates to manage deadlines
5. **Task Prioritization**: Focus on high-priority tasks first

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-mock pytest-cov`
5. Create a feature branch: `git checkout -b feature/your-feature`

### Code Style Guidelines

- Follow PEP 8 style guide
- Maximum line length: 88 characters (Black formatter)
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Run tests before committing: `pytest tests/`

### Pull Request Process

1. Ensure all tests pass
2. Update README.md if adding new features
3. Add tests for new functionality
4. Submit pull request with clear description

## License

This project is provided as-is for educational and personal use.
