# Script Organizer

A command-line tool for organizing script files by programming language based on file extensions and shebang lines. Creates language-specific folders (Python, JavaScript, Shell, etc.) for better organization of script collections.

## Project Description

Script Organizer solves the problem of organizing mixed script files by automatically categorizing them by programming language. It identifies scripts through file extensions and shebang lines, then organizes them into language-specific folders. This helps developers, system administrators, and users maintain organized script collections.

**Target Audience**: Developers, system administrators, and users who have collections of scripts in different programming languages and need to organize them by language for better management and navigation.

## Features

- **Extension-Based Detection**: Identifies scripts by file extensions (.py, .js, .sh, etc.)
- **Shebang Detection**: Identifies scripts by shebang lines (#!/usr/bin/python3, #!/bin/bash, etc.)
- **Language-Specific Folders**: Organizes scripts into folders like Python/, JavaScript/, Shell/, etc.
- **Flexible Priority**: Choose whether to prioritize extension or shebang detection
- **Multiple Language Support**: Supports 20+ programming languages
- **Conflict Resolution**: Handle file conflicts with skip, overwrite, or rename options
- **Dry Run Mode**: Preview what would happen without actually moving files
- **Recursive Processing**: Process directories and subdirectories
- **Comprehensive Logging**: Detailed logs of all file operations
- **Customizable**: Fully configurable via YAML configuration file

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/script-organizer
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

Edit `config.yaml` to customize language mappings and options:

```yaml
source_dir: scripts
output_base_dir: organized
language_extensions:
  python:
    extensions: [py, pyw]
    folder: "Python"
options:
  detection_priority: extension  # or shebang
```

## Usage

### Basic Usage

Organize scripts from the configured source directory:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Specify custom source directory
python src/main.py -s /path/to/scripts

# Specify custom output directory
python src/main.py -o /path/to/organized

# Process directories recursively
python src/main.py -r

# Dry run (preview without moving files)
python src/main.py --dry-run

# Copy files instead of moving
python src/main.py --copy

# Set detection priority
python src/main.py --priority shebang

# Use custom configuration file
python src/main.py -c /path/to/config.yaml
```

### Common Use Cases

**Organize scripts folder**:
```bash
python src/main.py -s ~/scripts -o ~/OrganizedScripts
```

**Preview organization (dry run)**:
```bash
python src/main.py --dry-run
```

**Copy instead of move**:
```bash
python src/main.py --copy
```

**Prioritize shebang over extension**:
```bash
python src/main.py --priority shebang
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### Language Extensions

Define languages and their file extensions:

```yaml
language_extensions:
  python:
    extensions: [py, pyw, pyc]
    folder: "Python"
    description: "Python scripts"
  javascript:
    extensions: [js, jsx, mjs]
    folder: "JavaScript"
    description: "JavaScript scripts"
```

#### Shebang Patterns

Define shebang patterns for language detection:

```yaml
shebang_patterns:
  python:
    patterns: ['python', 'python3', 'env python']
    folder: "Python"
  shell:
    patterns: ['bash', 'sh', 'zsh']
    folder: "Shell"
```

#### Detection Priority

```yaml
options:
  detection_priority: extension  # or shebang
```

- **extension**: Check file extension first, then shebang
- **shebang**: Check shebang first, then extension

#### Options

```yaml
options:
  move_files: true  # Move (true) or copy (false)
  dry_run: false  # Preview mode
  create_extension_subfolders: false  # Create subfolders by extension
```

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `SOURCE_DIR`: Custom source directory
- `OUTPUT_DIR`: Custom output directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Supported Languages

The tool supports organization for:

- **Python** (.py, .pyw, .pyc)
- **JavaScript** (.js, .jsx, .mjs, .cjs)
- **TypeScript** (.ts, .tsx)
- **Shell** (.sh, .bash, .zsh, .fish)
- **Perl** (.pl, .pm, .t)
- **Ruby** (.rb, .rbw)
- **PHP** (.php, .phtml)
- **Lua** (.lua)
- **Go** (.go)
- **Rust** (.rs)
- **Java** (.java, .jar)
- **C/C++** (.c, .cpp, .h, .hpp)
- **HTML** (.html, .htm)
- **CSS** (.css, .scss, .sass)
- **SQL** (.sql, .pgsql, .mysql)
- **R** (.r, .R)
- **MATLAB** (.m)
- **PowerShell** (.ps1, .psm1)
- **Batch** (.bat, .cmd)
- And more (configurable)

## Project Structure

```
script-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Application configuration
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── API.md              # API documentation (if applicable)
├── scripts/                 # Source directory (example)
├── organized/               # Output directory (example)
└── logs/
    └── script_organizer.log  # Application logs
```

## How It Works

1. **File Discovery**: Scans specified directories for files
2. **Language Detection**: Identifies language by:
   - File extension (if priority is "extension")
   - Shebang line (if priority is "shebang" or extension doesn't match)
3. **Folder Assignment**: Assigns file to language-specific folder
4. **File Organization**: Moves or copies files to assigned folders
5. **Conflict Handling**: Resolves conflicts based on configuration

## Detection Methods

### Extension-Based Detection

Files are identified by their extensions:
- `script.py` → Python/
- `app.js` → JavaScript/
- `run.sh` → Shell/

### Shebang-Based Detection

Files are identified by their shebang lines:
- `#!/usr/bin/python3` → Python/
- `#!/bin/bash` → Shell/
- `#!/usr/bin/env node` → JavaScript/

### Priority System

When both extension and shebang are available:
- **extension priority**: Uses extension first, falls back to shebang
- **shebang priority**: Uses shebang first, falls back to extension

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage

The test suite covers:
- Extension-based language detection
- Shebang-based language detection
- Detection priority handling
- File organization
- Conflict handling
- Dry run mode
- Directory exclusion

## Troubleshooting

### Files Not Being Organized

**Check file types**:
- Verify files have recognized extensions
- Check if files have shebang lines
- Review exclusion patterns

**Check configuration**:
- Verify language mappings in config
- Check shebang patterns
- Review detection priority setting

**Use dry run mode**:
```bash
python src/main.py --dry-run
```

### Wrong Language Detection

**Extension vs Shebang conflict**:
- Adjust `detection_priority` in config
- Use `--priority` command-line option
- Review both extension and shebang mappings

**Missing language**:
- Add language to `language_extensions` in config
- Add shebang patterns if needed
- Check default folder assignment

### File Conflicts

**Options**:
- `skip`: Don't move file if destination exists
- `overwrite`: Replace existing file
- `rename`: Add timestamp to filename

Configure in `config.yaml`:
```yaml
file_handling:
  on_conflict: rename  # or skip, overwrite
```

## Best Practices

1. **Test with dry run first**: Always use `--dry-run` before actual organization
2. **Backup important scripts**: Make backups before organizing important scripts
3. **Review language mappings**: Ensure all your script types are covered
4. **Set appropriate priority**: Choose extension or shebang priority based on your needs
5. **Exclude build directories**: Add common directories to exclusions
6. **Use copy mode for safety**: Use `--copy` to preserve originals

## Customizing Language Mappings

Add new languages or modify existing ones in `config.yaml`:

```yaml
language_extensions:
  my_language:
    extensions: [ext1, ext2]
    folder: "MyLanguage"
    description: "My Language scripts"

shebang_patterns:
  my_language:
    patterns: ['mylang', 'env mylang']
    folder: "MyLanguage"
```

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes following PEP 8 style guide
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Commit with conventional commit format
7. Push and create a pull request

### Code Style Guidelines

- Follow PEP 8 strictly
- Maximum line length: 88 characters
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## License

This project is part of the everyday-python-scripts collection. See the main repository for license information.
