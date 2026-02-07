# Pattern File Organizer

A Python automation tool that organizes files using custom pattern rules defined in a configuration file, supporting multiple pattern rules and destinations.

## Features

- Custom pattern matching using regex
- Multiple pattern rules with priorities
- Flexible destination mapping
- Support for filename, path, or extension matching
- Recursive or non-recursive directory scanning
- Configurable exclusions (patterns, directories, extensions)
- Dry-run mode to preview operations
- Backup creation before moving files
- Preserve directory structure option
- Comprehensive error handling and logging
- Detailed operation reports
- Statistics tracking

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. Clone or navigate to the project directory:
```bash
cd pattern-file-organizer
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Configuration File

The tool uses a YAML configuration file (`config.yaml`) for settings. Key configuration sections:

- **source**: Source directory and exclusion settings
- **rules**: Pattern matching rules with destinations
- **operations**: Operation settings (backup, skip existing, etc.)
- **report**: Report generation settings
- **logging**: Logging configuration

### Pattern Rules

Each rule in the configuration defines:

- **name**: Rule identifier
- **pattern**: Regex pattern to match
- **destination**: Destination directory for matched files
- **match_type**: What to match against (`filename`, `path`, or `extension`)
- **case_sensitive**: Whether pattern matching is case-sensitive
- **priority**: Rule priority (higher priority rules checked first)
- **enabled**: Whether rule is active

### Example Rule Configuration

```yaml
rules:
  - name: "Images"
    pattern: "\\.(jpg|jpeg|png|gif)$"
    destination: "Pictures"
    match_type: "extension"
    case_sensitive: false
    priority: 10
    enabled: true

  - name: "Screenshots"
    pattern: "screenshot|screen_shot"
    destination: "Pictures/Screenshots"
    match_type: "filename"
    case_sensitive: false
    priority: 20
    enabled: true
```

### Destination Variables

Destination paths support placeholders:

- `{filename}`: File name without extension
- `{extension}`: File extension (without dot)
- `{year}`: Current year (YYYY)
- `{month}`: Current month (MM)
- `{day}`: Current day (DD)

Example:
```yaml
destination: "Documents/{year}/{month}"
```

### Environment Variables

You can override configuration using environment variables:

- `SOURCE_DIRECTORY`: Source directory to organize (overrides config.yaml)

Create a `.env` file in the project root (see `.env.example` for template).

## Usage

### Command Line Interface

**Organize files using default configuration:**
```bash
python src/main.py
```

**Organize specific directory:**
```bash
python src/main.py --directory /path/to/organize
```

**Non-recursive search:**
```bash
python src/main.py --directory /path/to/organize --no-recursive
```

**Preview operations (dry-run):**
```bash
python src/main.py --directory /path/to/organize --dry-run
```

**Apply all matching rules:**
```bash
python src/main.py --directory /path/to/organize --match-mode all
```

**Generate report:**
```bash
python src/main.py --directory /path/to/organize --output report.txt
```

### Use Cases

**Organize downloads folder:**
```bash
python src/main.py -d ~/Downloads --dry-run
```

**Organize with custom config:**
```bash
python src/main.py -c custom_config.yaml -d /path/to/files
```

**Preview and then organize:**
```bash
# Preview first
python src/main.py -d ~/Downloads --dry-run

# Then actually organize
python src/main.py -d ~/Downloads
```

## Project Structure

```
pattern-file-organizer/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── .gitignore
├── src/
│   └── main.py
├── tests/
│   └── test_main.py
├── docs/
│   └── API.md
└── logs/
    └── .gitkeep
```

- `src/main.py`: Main application code
- `config.yaml`: Configuration file with pattern rules
- `tests/test_main.py`: Unit tests
- `logs/`: Log files directory
- `output/`: Generated reports directory

## How It Works

1. **Load Configuration**: Reads pattern rules from YAML config file
2. **Scan Directory**: Finds all files in specified directory
3. **Match Patterns**: Matches files against pattern rules (by priority)
4. **Resolve Destinations**: Determines destination path for each matched file
5. **Move Files**: Moves files to destinations (with optional backup)
6. **Generate Report**: Creates detailed report of all operations

### Pattern Matching

- Rules are processed in priority order (higher priority first)
- First matching rule is used by default (`match_mode=first`)
- Can apply all matching rules (`match_mode=all`)
- Supports regex patterns for flexible matching
- Can match against filename, full path, or extension

### Match Modes

- **first**: Uses first matching rule (default)
- **all**: Applies all matching rules (may move file multiple times)

## Report Contents

The generated report includes:

1. **Summary Statistics**
   - Files scanned
   - Files matched
   - Files moved
   - Files skipped
   - Errors encountered

2. **Pattern Rules**
   - All configured rules with their settings
   - Priority and enabled status

3. **File Operations**
   - Detailed list of all file operations
   - Source and destination paths
   - Operation status (moved, skipped, error)
   - Error messages if any

## Configuration Options

### Source Settings

- `directory`: Directory to scan
- `recursive`: Search subdirectories (default: true)
- `exclude.patterns`: Regex patterns to exclude
- `exclude.directories`: Directory names to exclude
- `exclude.extensions`: File extensions to exclude

### Operation Settings

- `create_backup`: Create backup before moving (default: false)
- `skip_existing`: Skip if destination exists (default: true)
- `preserve_structure`: Preserve directory structure (default: false)

### Rule Settings

- `name`: Rule identifier
- `pattern`: Regex pattern
- `destination`: Destination directory
- `match_type`: `filename`, `path`, or `extension`
- `case_sensitive`: Case-sensitive matching (default: false)
- `priority`: Rule priority (default: 0)
- `enabled`: Rule enabled (default: true)

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_main.py::test_organize_files
```

## Troubleshooting

### Common Issues

**No files matched:**
- Verify pattern rules are correct
- Check that rules are enabled
- Review exclusion rules
- Test patterns manually with regex

**Files not moved:**
- Check file permissions
- Verify destination directories are writable
- Review logs for error messages
- Ensure `skip_existing` is not preventing moves

**Pattern not matching:**
- Verify regex pattern syntax
- Check `match_type` setting
- Test pattern with regex tester
- Review case sensitivity setting

### Error Messages

The tool provides detailed error messages in logs. Check `logs/organizer.log` for:
- Pattern compilation errors
- File access errors
- Permission issues
- Destination resolution problems

### Best Practices

1. **Test with dry-run first**: Always use `--dry-run` to preview operations
2. **Start with simple patterns**: Begin with basic patterns and add complexity
3. **Use priorities wisely**: Higher priority rules are checked first
4. **Enable backups**: Set `create_backup: true` for important files
5. **Review exclusions**: Configure exclusions to avoid processing system files
6. **Check reports**: Review reports to understand what was done

## Security Considerations

- Be cautious when organizing system directories
- Review exclusion rules to avoid processing sensitive files
- Verify file permissions before bulk operations
- Consider backing up before organizing
- Test with dry-run mode first
- Use version control for code files

## Advanced Usage

### Custom Pattern Examples

**Organize by project name:**
```yaml
- name: "Project Files"
  pattern: "^project-.*"
  destination: "Projects/{filename}"
  match_type: "filename"
```

**Organize by file size pattern:**
```yaml
- name: "Large Files"
  pattern: ".*"
  destination: "LargeFiles"
  match_type: "filename"
```

**Organize by path pattern:**
```yaml
- name: "Temp Files"
  pattern: "/tmp/|/temp/"
  destination: "Trash"
  match_type: "path"
```

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed

## License

This project is part of the everyday-python-scripts collection.
