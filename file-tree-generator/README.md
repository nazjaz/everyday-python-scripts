# File Tree Generator

Generate visual file tree diagrams showing directory structure with file sizes and counts. Outputs to a text file with customizable depth, exclusions, and formatting options. Perfect for documenting project structures, analyzing disk usage, and creating directory visualizations.

## Project Description

File Tree Generator solves the problem of visualizing complex directory structures by creating detailed, human-readable tree diagrams. It displays file sizes in human-readable format, counts files per directory, and supports customizable depth limits and exclusion patterns. Ideal for documentation, disk space analysis, and project structure visualization.

**Target Audience**: Developers documenting project structures, system administrators analyzing disk usage, and users who need visual representations of directory hierarchies.

## Features

- Visual tree diagram with Unicode box-drawing characters
- File size display in human-readable format (B, KB, MB, GB, TB)
- File count per directory
- Customizable maximum depth
- Exclusion patterns for directories, files, and extensions
- Hidden file filtering option
- Output to text file with customizable path
- Console output option
- Comprehensive statistics (directories scanned, files counted, total size)
- Error handling for permission issues
- Recursive directory traversal
- Sorted output (directories first, then files, alphabetically)

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Read permissions to directories being scanned

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/file-tree-generator
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

Edit `config.yaml` to set your root directory and output preferences:

```yaml
root_directory: ~/Documents
output_file: tree.txt
max_depth: null  # null for unlimited, or set to integer
```

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **root_directory**: Directory to generate tree for (default: `~/Documents`)
- **output_file**: Path to save tree diagram (default: `tree.txt`)
- **max_depth**: Maximum depth to traverse (null for unlimited, or integer)
- **show_hidden**: Include hidden files and directories (default: `false`)
- **exclusions**: Directories, patterns, and extensions to exclude
- **logging**: Log file location and rotation settings

### Environment Variables

Optional environment variables can override config.yaml settings:

- `ROOT_DIRECTORY`: Override root directory path
- `OUTPUT_FILE`: Override output file path
- `MAX_DEPTH`: Override maximum depth (integer)
- `SHOW_HIDDEN`: Show hidden files (`true`/`false`)

### Example Configuration

```yaml
root_directory: ~/Projects
output_file: project_tree.txt
max_depth: 3

show_hidden: false

exclusions:
  directories:
    - node_modules
    - .git
    - __pycache__
    - venv
  patterns:
    - .DS_Store
    - .pyc
  extensions:
    - .pyc
    - .cache
```

## Usage

### Basic Usage

Generate tree diagram with default configuration:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Use custom configuration file
python src/main.py -c /path/to/custom_config.yaml

# Specify root directory (overrides config)
python src/main.py -d ~/Projects

# Specify output file (overrides config)
python src/main.py -o my_tree.txt

# Set maximum depth
python src/main.py --max-depth 3

# Print to console instead of saving to file
python src/main.py --print

# Combine options
python src/main.py -d ~/Projects --max-depth 2 -o project_tree.txt
```

### Common Use Cases

1. **Generate Tree for Current Project**:
   ```bash
   python src/main.py -d . -o project_structure.txt
   ```

2. **Quick Preview (Console Output)**:
   ```bash
   python src/main.py -d ~/Documents --print
   ```

3. **Limited Depth Tree**:
   ```bash
   python src/main.py -d ~/Projects --max-depth 2
   ```
   Generates tree with maximum depth of 2 levels.

4. **Document Project Structure**:
   ```bash
   python src/main.py -d . --max-depth 4 -o docs/project_structure.txt
   ```

5. **Analyze Disk Usage**:
   ```bash
   python src/main.py -d ~/Downloads
   ```
   Shows file sizes and counts to identify large directories.

6. **Exclude Common Directories**:
   - Edit `config.yaml` to add directories to `exclusions.directories`
   - Common exclusions: `node_modules`, `.git`, `__pycache__`, `venv`

## Project Structure

```
file-tree-generator/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .gitignore              # Git ignore rules
├── src/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main application code
├── tests/
│   └── test_main.py        # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
└── logs/
    └── .gitkeep            # Log directory placeholder
```

### File Descriptions

- **src/main.py**: Core tree generation logic, file size calculation, and output formatting
- **config.yaml**: YAML configuration file with all settings
- **tests/test_main.py**: Unit tests for core functionality
- **logs/**: Directory for log files (created automatically)
- **tree.txt**: Generated tree diagram (created when script runs)

## Output Format

The generated tree diagram includes:

- Visual tree structure with Unicode box-drawing characters
- Directory names with file counts and total sizes
- Individual file names with sizes
- Header with root directory and max depth
- Footer with statistics (directories scanned, files counted, total size)

Example output:

```
================================================================================
File Tree: /Users/username/Projects
Max Depth: 3
================================================================================

Projects [42 files, 15.23 MB]
├── src [25 files, 8.45 MB]
│   ├── main.py (2.34 KB)
│   ├── utils.py (1.56 KB)
│   └── config.py (0.89 KB)
├── tests [15 files, 5.12 MB]
│   ├── test_main.py (3.45 KB)
│   └── test_utils.py (2.11 KB)
└── docs [2 files, 1.66 MB]
    └── README.md (1.66 MB)

================================================================================
Statistics
================================================================================
Directories Scanned: 3
Files Counted: 42
Total Size: 15.23 MB
Errors: 0
```

## Testing

Run tests using pytest:

```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html
```

Test coverage includes:
- Tree generation with various depths
- File size calculation and formatting
- Directory statistics calculation
- Exclusion logic (directories, patterns, extensions)
- Hidden file filtering
- Error handling for permission issues
- Output file generation
- Command-line argument parsing

## Troubleshooting

### Common Issues

**Issue**: `FileNotFoundError: Root directory does not exist`

**Solution**: Ensure the root directory path in `config.yaml` is correct and exists. Use absolute paths or ensure `~` expands correctly.

---

**Issue**: `PermissionError` when scanning directories

**Solution**: Ensure you have read permissions to the directories being scanned. On Linux/Mac, you may need to use `sudo` or adjust directory permissions. The script will continue and log permission errors.

---

**Issue**: Tree output is too large or takes too long

**Solution**: 
- Set `max_depth` in `config.yaml` to limit traversal depth
- Add more directories to `exclusions.directories`
- Exclude common large directories like `node_modules`, `.git`, `venv`

---

**Issue**: Hidden files appearing in tree

**Solution**: Set `show_hidden: false` in `config.yaml` or ensure it's not set to `true`.

---

**Issue**: Output file not created

**Solution**: Check that the output directory is writable. The script creates parent directories automatically. Verify the path in `config.yaml` or use `--output` option.

### Error Messages

- **"Configuration file not found"**: Ensure `config.yaml` exists in the project root or provide correct path with `-c` option
- **"Root directory does not exist"**: Verify the path in `config.yaml` or command-line argument
- **"Error accessing file"**: File may be locked by another process or permissions may be insufficient (logged but script continues)
- **"Error reading directory"**: Directory may have permission restrictions (logged but script continues)

## Contributing

### Development Setup

1. Fork the repository
2. Create a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Install development dependencies: `pip install pytest pytest-cov`
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
