# Pattern File Organizer API Documentation

## PatternRule Class

Represents a pattern matching rule for file organization.

### Constructor

```python
PatternRule(
    name: str,
    pattern: str,
    destination: str,
    **kwargs: Any
) -> None
```

Initialize pattern rule.

**Parameters:**
- `name` (str): Rule name/identifier
- `pattern` (str): Regex pattern to match against filenames or paths
- `destination` (str): Destination directory for matched files
- `**kwargs`: Additional rule options:
  - `case_sensitive` (bool): Whether pattern matching is case-sensitive. Default: False
  - `match_type` (str): What to match against (`filename`, `path`, or `extension`). Default: `filename`
  - `priority` (int): Rule priority (higher priority matches first). Default: 0
  - `enabled` (bool): Whether rule is active. Default: True

**Raises:**
- `ValueError`: If regex pattern is invalid

**Example:**
```python
rule = PatternRule(
    name="Images",
    pattern="\\.(jpg|png|gif)$",
    destination="Pictures",
    match_type="extension",
    priority=10
)
```

### Methods

#### matches

```python
matches(file_path: Path) -> bool
```

Check if file matches this rule's pattern.

**Parameters:**
- `file_path` (Path): Path to file to check

**Returns:**
- `bool`: True if file matches rule, False otherwise

**Example:**
```python
file_path = Path("/path/to/image.jpg")
if rule.matches(file_path):
    print("File matches rule")
```

## PatternFileOrganizer Class

Main class for organizing files using custom pattern rules.

### Constructor

```python
PatternFileOrganizer(config_path: str = "config.yaml") -> None
```

Initialize PatternFileOrganizer with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Default: "config.yaml"

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is invalid YAML
- `ValueError`: If configuration is invalid

**Example:**
```python
organizer = PatternFileOrganizer(config_path="config.yaml")
```

### Methods

#### organize_files

```python
organize_files(
    source_directory: Optional[str] = None,
    recursive: bool = True,
    dry_run: bool = False,
    match_mode: str = "first"
) -> Dict[str, Any]
```

Organize files based on pattern rules.

**Parameters:**
- `source_directory` (Optional[str]): Directory to scan. Overrides config if provided
- `recursive` (bool): Whether to search recursively. Default: True
- `dry_run` (bool): If True, show what would be done without actually moving files. Default: False
- `match_mode` (str): "first" to use first matching rule, "all" to apply all matches. Default: "first"

**Returns:**
- `Dict[str, Any]`: Dictionary with operation results:
  - `stats` (dict): Statistics dictionary
  - `operations` (list): List of operation dictionaries

**Raises:**
- `FileNotFoundError`: If source directory doesn't exist
- `ValueError`: If match_mode is invalid

**Example:**
```python
result = organizer.organize_files(
    source_directory="/path/to/organize",
    dry_run=True
)
print(f"Moved {result['stats']['files_moved']} files")
```

#### generate_report

```python
generate_report(output_file: Optional[str] = None) -> str
```

Generate text report of organization operations.

**Parameters:**
- `output_file` (Optional[str]): Path to output file. Overrides config if provided

**Returns:**
- `str`: Report content as string

**Example:**
```python
report = organizer.generate_report(output_file="report.txt")
print(report)
```

#### get_statistics

```python
get_statistics() -> Dict[str, Any]
```

Get processing statistics.

**Returns:**
- `Dict[str, Any]`: Dictionary with statistics:
  - `files_scanned` (int): Total files scanned
  - `files_matched` (int): Number of files matched by rules
  - `files_moved` (int): Number of files moved
  - `files_skipped` (int): Number of files skipped
  - `errors` (int): Number of errors encountered

**Example:**
```python
stats = organizer.get_statistics()
print(f"Scanned {stats['files_scanned']} files")
print(f"Moved {stats['files_moved']} files")
```

### Private Methods

#### _load_config

```python
_load_config(config_path: str) -> dict
```

Load configuration from YAML file.

#### _setup_logging

```python
_setup_logging() -> None
```

Configure logging based on configuration.

#### _load_rules

```python
_load_rules() -> None
```

Load pattern rules from configuration.

#### _is_excluded

```python
_is_excluded(file_path: Path) -> bool
```

Check if file should be excluded from processing.

#### _find_matching_rule

```python
_find_matching_rule(file_path: Path) -> Optional[PatternRule]
```

Find first matching rule for file.

**Parameters:**
- `file_path` (Path): Path to file to match

**Returns:**
- `Optional[PatternRule]`: Matching PatternRule or None if no match

#### _resolve_destination

```python
_resolve_destination(
    file_path: Path,
    rule: PatternRule,
    base_directory: Path
) -> Path
```

Resolve destination path for file.

**Parameters:**
- `file_path` (Path): Path to file being moved
- `rule` (PatternRule): Matching pattern rule
- `base_directory` (Path): Base directory for relative path resolution

**Returns:**
- `Path`: Resolved destination path

### Attributes

#### config

Configuration dictionary loaded from YAML file.

#### rules

List of PatternRule objects, sorted by priority.

#### stats

Dictionary containing processing statistics:
- `files_scanned`: Total files scanned
- `files_matched`: Number of files matched by rules
- `files_moved`: Number of files moved
- `files_skipped`: Number of files skipped
- `errors`: Number of errors encountered

#### operations

List of operation dictionaries, each containing:
- `file` (str): Source file path
- `rule` (str): Rule name that matched
- `destination` (str): Destination path
- `status` (str): Operation status (`moved`, `dry_run`, `error`, `pending`)
- `error` (str, optional): Error message if status is `error`

## Usage Examples

### Basic Usage

```python
from src.main import PatternFileOrganizer

# Initialize
organizer = PatternFileOrganizer(config_path="config.yaml")

# Organize files
result = organizer.organize_files(
    source_directory="/path/to/organize",
    dry_run=True
)

# Generate report
report = organizer.generate_report(output_file="report.txt")

# Get statistics
stats = organizer.get_statistics()
print(f"Found {stats['files_matched']} matching files")
```

### Custom Pattern Rules

```python
from src.main import PatternFileOrganizer, PatternRule

organizer = PatternFileOrganizer()

# Add custom rule
custom_rule = PatternRule(
    name="Custom",
    pattern="^project-.*",
    destination="Projects",
    match_type="filename",
    priority=20
)
organizer.rules.append(custom_rule)

# Organize with custom rules
organizer.organize_files(source_directory="/path/to/files")
```

### Match All Rules

```python
from src.main import PatternFileOrganizer

organizer = PatternFileOrganizer()

# Apply all matching rules
result = organizer.organize_files(
    source_directory="/path/to/organize",
    match_mode="all"
)
```

### Programmatic Rule Management

```python
from src.main import PatternFileOrganizer

organizer = PatternFileOrganizer()

# Disable a rule
for rule in organizer.rules:
    if rule.name == "Images":
        rule.enabled = False

# Re-sort by priority
organizer.rules.sort(key=lambda r: r.priority, reverse=True)

# Organize
organizer.organize_files(source_directory="/path/to/files")
```
