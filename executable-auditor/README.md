# Executable File Auditor

A command-line tool for finding all executable files in a directory tree, categorizing them by type, and generating a comprehensive security audit report. Identifies scripts, binaries, and system executables with security flags and file integrity hashes.

## Project Description

Executable File Auditor solves the problem of security auditing by providing a comprehensive tool to scan directory trees for executable files, categorize them, and generate detailed security reports. It helps system administrators, security professionals, and developers identify executable files, detect potential security issues, and maintain an inventory of executables with their properties and security flags.

**Target Audience**: System administrators, security professionals, and developers who need to audit executable files, identify security risks, and maintain inventories of executable files in their systems.

## Features

- **Comprehensive Detection**: Finds executables by permissions, extensions, shebang, and magic bytes
- **File Categorization**: Categorizes executables as scripts, binaries, system executables, etc.
- **Security Auditing**: Flags suspicious permissions, large files, and recently modified executables
- **File Integrity**: Calculates file hashes (MD5, SHA1, SHA256) for integrity checking
- **Permission Analysis**: Analyzes file permissions and flags security issues
- **Multiple Report Formats**: Generate reports in JSON, TXT, or CSV format
- **Recursive Scanning**: Scan directories and subdirectories
- **Flexible Filtering**: Exclude files and directories by patterns
- **Comprehensive Logging**: Detailed logs of all operations

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### Step 1: Navigate to Project

```bash
cd /path/to/everyday-python-scripts/executable-auditor
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

Edit `config.yaml` to customize detection and security audit options:

```yaml
scan_directories:
  - .
detection:
  check_permissions: true
  check_extensions: true
security_audit:
  calculate_hashes: true
  hash_algorithm: sha256
```

## Usage

### Basic Usage

Scan configured directories:

```bash
python src/main.py
```

### Command-Line Options

```bash
# Scan specific directories
python src/main.py -d /path/to/dir1 /path/to/dir2

# Non-recursive scan
python src/main.py --no-recursive

# Specify output file
python src/main.py -o /path/to/report.json

# Specify report format
python src/main.py --format txt

# Use custom configuration file
python src/main.py -c /path/to/config.yaml
```

### Common Use Cases

**Audit Downloads folder**:
```bash
python src/main.py -d ~/Downloads
```

**Generate text report**:
```bash
python src/main.py --format txt -o audit.txt
```

**Non-recursive scan**:
```bash
python src/main.py --no-recursive
```

## Configuration

### Configuration File (config.yaml)

The application uses a YAML configuration file for settings:

#### Detection Options

```yaml
detection:
  check_permissions: true  # Check file execute permissions
  check_extensions: true  # Check file extensions
  check_magic_bytes: true  # Check binary magic bytes
  check_shebang: true  # Check for shebang lines
```

#### File Categories

```yaml
categories:
  scripts:
    extensions: [sh, bash, py, pl, rb, js]
    description: "Script files"
  binaries:
    extensions: [exe, bin, app]
    description: "Binary executables"
```

#### Security Audit Options

```yaml
security_audit:
  calculate_hashes: true  # Calculate file hashes
  hash_algorithm: sha256  # md5, sha1, or sha256
  flag_suspicious_permissions: true  # Flag suspicious perms
  suspicious_permissions: ["777", "666"]  # Permissions to flag
  check_file_size: true  # Flag unusually large files
  max_normal_size: 104857600  # 100MB
  flag_recent_modifications: true  # Flag recently modified
  recent_days: 7  # Days considered "recent"
```

### Environment Variables

Create a `.env` file (use `.env.example` as template) to override configuration:

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Report Formats

### JSON Report

Structured data format with complete information:

```json
{
  "generated_at": "2024-01-15T10:30:00",
  "total_executables": 25,
  "total_security_flags": 3,
  "categories": {
    "scripts": {
      "count": 15,
      "files": [...]
    },
    "binaries": {
      "count": 10,
      "files": [...]
    }
  }
}
```

### Text Report

Human-readable format with detailed information:

```
================================================================================
EXECUTABLE FILE SECURITY AUDIT REPORT
================================================================================

Generated: 2024-01-15T10:30:00

Total Executable Files Found: 25

SUMMARY BY CATEGORY
--------------------------------------------------------------------------------
Scripts: 15 file(s)
Binaries: 10 file(s)

SCRIPTS FILES
--------------------------------------------------------------------------------
Path: /path/to/script.sh
  Size: 2.50 KB
  Permissions: -rwxr-xr-x (755)
  Modified: 2024-01-10T08:00:00
  Hash (sha256): abc123...
  Security Flags:
    - Recently modified: 5 days ago
```

### CSV Report

Tabular format suitable for spreadsheet applications:

| Category | Path | Name | Size (bytes) | Permissions (octal) | Hash | Security Flags |
|----------|------|------|--------------|---------------------|------|----------------|
| scripts | /path/to/script.sh | script.sh | 2560 | 755 | abc123... | Recently modified: 5 days ago |

## Security Flags

The tool flags potential security issues:

- **Suspicious Permissions**: Files with overly permissive permissions (777, 666, etc.)
- **Unusually Large Files**: Executables exceeding normal size limits
- **Recently Modified**: Files modified within specified days
- **Root Ownership**: Files owned by root (if enabled)

## Project Structure

```
executable-auditor/
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
├── data/
│   └── executable_audit.json  # Generated reports
└── logs/
    └── executable_auditor.log  # Application logs
```

## Detection Methods

The tool uses multiple methods to identify executables:

1. **Permission Check**: Files with execute permission bits set
2. **Extension Check**: Files with known executable extensions
3. **Shebang Detection**: Files starting with `#!/` (script files)
4. **Magic Bytes**: Binary files identified by magic bytes (ELF, MZ, etc.)

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
- Executable detection (permissions, extensions, shebang)
- File categorization
- Hash calculation
- Security flag detection
- Report generation (JSON, TXT, CSV)
- File and directory exclusion

## Troubleshooting

### No Executables Found

**Check detection settings**:
- Verify `check_permissions` is enabled
- Check `check_extensions` is enabled
- Ensure files actually have execute permissions
- Verify exclusion patterns aren't too broad

**Check permissions**:
- Ensure read access to scanned directories
- Check file system permissions
- Verify files are actually executable

### Performance Issues

**Large directories**:
- Use exclusion patterns to skip system directories
- Consider non-recursive scanning
- Process directories in batches

**Hash calculation**:
- Disable hash calculation if not needed
- Use faster algorithm (MD5 instead of SHA256)
- Process large files separately

### Security Flags Not Appearing

**Check configuration**:
- Verify `flag_suspicious_permissions` is enabled
- Check `suspicious_permissions` list
- Verify `flag_recent_modifications` is enabled
- Check `recent_days` setting

## Best Practices

1. **Regular Audits**: Run audits regularly to track changes
2. **Review Security Flags**: Investigate flagged files promptly
3. **Exclude System Directories**: Add common system directories to exclusions
4. **Use Hash Verification**: Enable hashes for integrity checking
5. **Store Reports**: Keep reports for comparison and tracking
6. **Review Permissions**: Check and fix suspicious permissions

## Security Considerations

- **File Access**: Tool only reads files, never modifies them
- **Hash Storage**: Hashes can be used for integrity verification
- **Permission Analysis**: Helps identify security misconfigurations
- **Audit Trail**: Reports provide audit trail of executable files

## Use Cases

- **Security Audits**: Identify all executables and potential security risks
- **Compliance**: Maintain inventory of executable files
- **Change Detection**: Track new or modified executables
- **Permission Review**: Identify files with insecure permissions
- **Integrity Checking**: Use hashes to detect file modifications

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
