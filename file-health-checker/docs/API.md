# API Documentation

## FileHealthChecker Class

The main class for performing file health checks and corruption detection.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the FileHealthChecker with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

**Side Effects:**
- Loads configuration
- Sets up logging
- Loads magic number definitions

#### `scan_directory(directory: str) -> None`

Scan directory and perform health checks on files.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Performs health checks on all files
- Populates `file_health` list
- Updates statistics
- Logs all operations

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate health check report.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_perform_health_check(file_path: Path) -> Dict[str, Any]`

Perform comprehensive health check on a file.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Dictionary with health check results containing:
  - `path`: Full file path
  - `name`: File name
  - `extension`: File extension
  - `size_bytes`: File size
  - `is_healthy`: Boolean health status
  - `issues`: List of issue descriptions
  - `checksum`: Optional checksum value
  - `status`: Health status string ("healthy", "suspicious", "corrupted", "error")

#### `_check_file_header(file_path: Path) -> Tuple[bool, Optional[str]]`

Check if file header matches expected magic number.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Tuple of (is_valid, error_message).

#### `_check_file_structure(file_path: Path) -> Tuple[bool, Optional[str]]`

Check file structure for common issues.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Tuple of (is_valid, error_message).

**Checks:**
- Empty file detection
- Minimum size validation
- Truncation detection
- Format-specific structure validation

#### `_check_zip_structure(file_path: Path) -> Tuple[bool, Optional[str]]`

Check ZIP file structure.

**Parameters:**
- `file_path` (Path): Path to ZIP file.

**Returns:**
- Tuple of (is_valid, error_message).

#### `_check_jpeg_structure(file_path: Path) -> Tuple[bool, Optional[str]]`

Check JPEG file structure.

**Parameters:**
- `file_path` (Path): Path to JPEG file.

**Returns:**
- Tuple of (is_valid, error_message).

#### `_check_png_structure(file_path: Path) -> Tuple[bool, Optional[str]]`

Check PNG file structure.

**Parameters:**
- `file_path` (Path): Path to PNG file.

**Returns:**
- Tuple of (is_valid, error_message).

#### `_check_pdf_structure(file_path: Path) -> Tuple[bool, Optional[str]]`

Check PDF file structure.

**Parameters:**
- `file_path` (Path): Path to PDF file.

**Returns:**
- Tuple of (is_valid, error_message).

#### `_calculate_file_hash(file_path: Path, algorithm: str = "md5") -> Optional[str]`

Calculate file hash for integrity verification.

**Parameters:**
- `file_path` (Path): Path to file.
- `algorithm` (str): Hash algorithm ("md5", "sha1", "sha256").

**Returns:**
- Hash string or None if error.

### Attributes

#### `file_health: List[Dict[str, Any]]`

List of dictionaries containing health check results for each scanned file.

#### `magic_numbers: Dict[str, List[bytes]]`

Dictionary mapping file extensions to lists of expected magic number bytes.

#### `stats: Dict[str, Any]`

Dictionary containing operation statistics:
- `files_scanned`: Total number of files scanned
- `healthy_files`: Number of healthy files
- `corrupted_files`: Number of corrupted files
- `suspicious_files`: Number of suspicious files
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import FileHealthChecker

# Initialize with default config
checker = FileHealthChecker()

# Or with custom config
checker = FileHealthChecker(config_path="custom_config.yaml")

# Scan directory
checker.scan_directory("/path/to/directory")

# Generate report
checker.generate_report()

# Access results
print(f"Scanned {checker.stats['files_scanned']} files")
print(f"Healthy: {checker.stats['healthy_files']}")
print(f"Corrupted: {checker.stats['corrupted_files']}")

for health_result in checker.file_health:
    if not health_result["is_healthy"]:
        print(f"{health_result['path']}: {health_result['issues']}")
```

### Health Check Process

For each file, the tool performs:

1. **Header Validation:** Checks magic numbers match file extension
2. **Structure Validation:** Validates file structure for known formats
3. **Integrity Checks:** Detects empty, truncated, or suspicious files
4. **Checksum Calculation:** Optional hash calculation for integrity verification

### File Status Values

- **healthy**: No issues detected
- **suspicious**: One issue detected (may need review)
- **corrupted**: Multiple issues or critical problems
- **error**: Cannot be checked (permission errors, etc.)

### Supported File Formats

Built-in validation for:
- PDF files
- PNG images
- JPEG images
- GIF images
- ZIP archives
- Office documents (DOCX, XLSX, PPTX - as ZIP)
- MP3 audio
- MP4 video
- AVI video
- WAV audio
- Executables (EXE, DLL)
- Python bytecode (PYC)

Custom formats can be added via configuration.
