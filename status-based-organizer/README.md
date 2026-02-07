# Status-Based File Organizer

A Python automation tool for organizing files by status indicators like completed, in-progress, draft, or archived. This script detects file status from naming conventions, metadata, and content, then organizes files into appropriate status-based directories.

## Features

- **Multiple Detection Methods**:
  - **Filename Analysis**: Detects status from filename patterns and keywords
  - **Metadata Analysis**: Uses file age and size as status indicators
  - **Content Analysis**: Searches file content for status keywords (text files)
- **Status Categories**:
  - **Completed**: Files marked as done, finished, or final
  - **In Progress**: Files marked as working, WIP, or in-progress
  - **Draft**: Files marked as draft, temp, or temporary
  - **Archived**: Files marked as archived, old, or backup
- **Flexible Pattern Matching**: Supports regex patterns and keyword matching
- **Configurable Indicators**: Customize status detection patterns
- **Duplicate Detection**: Uses content hashing to prevent duplicates
- **Default Status**: Assigns default status to unmatched files
- **Comprehensive Logging**: Detailed logging with detection method tracking

## Prerequisites

- Python 3.8 or higher
- Write permissions to source and destination directories
- Sufficient disk space for file organization

## Installation

1. Clone or navigate to the project directory:
```bash
cd status-based-organizer
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

4. Copy and configure the environment file (optional):
```bash
cp .env.example .env
# Edit .env with your settings if needed
```

5. Review and customize `config.yaml` with your settings:
   - Configure status indicators and patterns
   - Set source and destination directories
   - Adjust detection methods

## Configuration

### Configuration File (config.yaml)

The main configuration is stored in `config.yaml`. Key settings include:

- **source_directory**: Directory to organize (default: current directory)
- **status_indicators**: Configuration for each status category:
  - **filename_patterns**: Regex patterns to match in filenames
  - **keywords**: Keywords to search for in filenames
  - **content_keywords**: Keywords to search for in file content
  - **use_age_indicator**: Use file age as indicator (for archived)
  - **use_size_indicator**: Use file size as indicator (for draft)
- **organization**: Directory paths and organization settings
- **organization.default_status**: Default status for unmatched files

### Status Indicators

#### Completed
- Patterns: `*completed*`, `*done*`, `*finished*`, `*final*`
- Keywords: completed, done, finished, final, complete
- Content: "status: completed", "[completed]", "[done]"

#### In Progress
- Patterns: `*in-progress*`, `*wip*`, `*working*`
- Keywords: in progress, wip, working, incomplete
- Content: "status: in progress", "[wip]", "[working]"

#### Draft
- Patterns: `*draft*`, `*temp*`, `*temporary*`
- Keywords: draft, temp, temporary, tmp, scratch
- Content: "status: draft", "[draft]"
- Optional: Very small files (<100 bytes)

#### Archived
- Patterns: `*archive*`, `*old*`, `*backup*`
- Keywords: archive, archived, old, backup, bak
- Content: "status: archived", "[archived]"
- Optional: Very old files (>365 days)

### Environment Variables

Optional environment variables can override configuration:

- `SOURCE_DIRECTORY`: Override source directory path
- `COMPLETED_DIRECTORY`: Override completed directory path
- `IN_PROGRESS_DIRECTORY`: Override in-progress directory path
- `DRAFT_DIRECTORY`: Override draft directory path
- `ARCHIVED_DIRECTORY`: Override archived directory path

## Usage

### Basic Usage

Organize files with default configuration:
```bash
python src/main.py
```

### Dry Run

Preview what would be organized without making changes:
```bash
python src/main.py --dry-run
```

### Custom Configuration

Specify a different configuration file:
```bash
python src/main.py --config custom-config.yaml
```

### Verbose Logging

Enable detailed logging output:
```bash
python src/main.py --verbose
```

### Command-Line Options

- `-c, --config`: Path to configuration file (default: config.yaml)
- `-d, --dry-run`: Perform a dry run without making changes
- `-v, --verbose`: Enable verbose logging

## Project Structure

```
status-based-organizer/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
├── src/
│   └── main.py              # Main application code
├── tests/
│   └── test_main.py         # Unit tests
├── docs/
│   └── .gitkeep             # Documentation directory placeholder
└── logs/
    └── .gitkeep             # Logs directory placeholder
```

## Testing

Run tests using pytest:
```bash
pytest tests/
```

Run tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## How It Works

1. **File Discovery**: Recursively scans the source directory for files, excluding system directories and status directories.

2. **Status Detection**: For each file, attempts to detect status using multiple methods:
   - **Filename Analysis**: Checks filename against regex patterns and keywords
   - **Metadata Analysis**: Uses file age (for archived) or size (for draft)
   - **Content Analysis**: Searches file content for status keywords (text files only)

3. **Detection Priority**: Tries methods in order:
   - Filename (most reliable)
   - Metadata
   - Content
   - Default status (if configured)

4. **Organization**: Moves files to appropriate status directories:
   - Completed files → completed_directory
   - In-progress files → in_progress_directory
   - Draft files → draft_directory
   - Archived files → archived_directory

5. **Duplicate Detection**: Uses content hashing to prevent duplicate files.

6. **Logging**: Tracks detection methods used for each file.

## Example Scenarios

### Scenario 1: Completed File
- **Filename**: `report_final.pdf` or `project_done.txt`
- **Detection**: Filename keyword "final" or "done"
- **Result**: Organized to `./completed/`

### Scenario 2: In-Progress File
- **Filename**: `document_wip.docx` or `work_in-progress.md`
- **Detection**: Filename pattern or keyword "wip"
- **Result**: Organized to `./in_progress/`

### Scenario 3: Draft File
- **Filename**: `notes_draft.txt` or `temp_file.py`
- **Detection**: Filename keyword "draft" or "temp"
- **Result**: Organized to `./draft/`

### Scenario 4: Archived File
- **Filename**: `old_backup.zip` or `data_archive.tar`
- **Detection**: Filename keyword "old" or "archive"
- **Result**: Organized to `./archived/`

## Naming Conventions

The script recognizes various naming conventions:

- **Underscore separators**: `file_completed.txt`, `project_done.pdf`
- **Hyphen separators**: `file-in-progress.md`, `work-wip.docx`
- **Mixed case**: `FileCompleted.txt`, `PROJECT_DONE.pdf`
- **Case insensitive**: All matching is case-insensitive

## Customizing Status Detection

### Adding Custom Patterns

Add custom regex patterns to `config.yaml`:

```yaml
status_indicators:
  completed:
    filename_patterns:
      - ".*_done_v\\d+\\..*$"  # Custom pattern
    keywords:
      - "custom_keyword"
```

### Using Metadata Indicators

Enable metadata-based detection:

```yaml
status_indicators:
  archived:
    use_age_indicator: true  # Files >365 days old
  draft:
    use_size_indicator: true  # Files <100 bytes
```

## Troubleshooting

### Files Not Being Detected

If files are not being detected:
- Check that filename patterns match your naming conventions
- Verify keywords are spelled correctly
- Review detection method priority
- Check logs for detection details
- Try adding custom patterns

### Incorrect Status Assignment

If files are assigned incorrect status:
- Review pattern matching order (filename first)
- Check for conflicting patterns
- Adjust pattern specificity
- Use more specific regex patterns
- Review logs for detection method used

### Too Many Files in Default Status

If many files go to default status:
- Add more patterns to status indicators
- Enable metadata indicators
- Review your naming conventions
- Add content keywords for text files

### Permission Errors

If you encounter permission errors:
- Ensure read access to source directory
- Ensure write access to destination directories
- Check file and directory permissions
- Some files may be skipped with warnings

### Duplicate Detection Issues

If duplicates are not detected:
- Ensure check_duplicates is enabled
- Hashes are stored per status directory
- Same content in different statuses will be saved separately

## Use Cases

### Organizing Project Files
Organize project files by completion status:
- Completed: `project_final.pdf`, `report_done.docx`
- In Progress: `document_wip.md`, `work_in-progress.txt`
- Draft: `notes_draft.txt`, `temp_ideas.py`

### Managing Work Documents
Organize work documents by status:
- Completed: `proposal_finished.pdf`
- In Progress: `report_working.docx`
- Draft: `memo_draft.txt`

### Archiving Old Files
Automatically archive old files:
- Enable `use_age_indicator` for archived status
- Files older than 365 days are archived

## Security Considerations

- The script performs file move operations
- Always use `--dry-run` first to preview changes
- Ensure backups are in place before organizing important files
- Duplicate detection reads file contents but does not modify them
- The script does not process files outside the specified source directory

## Performance Considerations

- Content analysis is only performed on text files
- Large text files (>1 MB) are skipped for content analysis
- Processing time increases with number of files
- Consider processing during off-peak hours for large directories

## Contributing

1. Follow PEP 8 style guidelines
2. Add type hints to all functions
3. Include docstrings for all public functions and classes
4. Write tests for new functionality
5. Update documentation as needed
6. Use conventional commit messages

## License

This project is provided as-is for automation purposes.
