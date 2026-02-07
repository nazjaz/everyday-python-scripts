# API Documentation

## SimilarFileFinder Class

The main class for finding files with similar names using string similarity algorithms.

### Methods

#### `__init__(config_path: str = "config.yaml")`

Initialize the SimilarFileFinder with configuration.

**Parameters:**
- `config_path` (str): Path to configuration YAML file. Defaults to "config.yaml".

**Raises:**
- `FileNotFoundError`: If config file doesn't exist.
- `yaml.YAMLError`: If config file is invalid YAML.

**Side Effects:**
- Loads configuration
- Sets up logging
- Initializes data structures

#### `scan_directory(directory: str) -> None`

Scan directory and collect file information.

**Parameters:**
- `directory` (str): Path to directory to scan.

**Raises:**
- `FileNotFoundError`: If directory doesn't exist.
- `PermissionError`: If directory is not accessible.
- `ValueError`: If path is not a directory.

**Side Effects:**
- Scans directory recursively
- Collects file information
- Updates statistics
- Logs all operations

#### `find_similar_files() -> None`

Find files with similar names using configured algorithm.

**Side Effects:**
- Compares all pairs of files
- Calculates similarity scores
- Populates `similar_pairs` list
- Updates statistics
- Logs results

#### `generate_report(output_path: Optional[str] = None) -> str`

Generate report of similar files.

**Parameters:**
- `output_path` (Optional[str]): Path to save report file. If None, uses default from config.

**Returns:**
- `str`: Report content as string.

**Raises:**
- `IOError`: If report file cannot be written.
- `PermissionError`: If output directory is not writable.

#### `_sequence_similarity(str1: str, str2: str) -> float`

Calculate similarity using SequenceMatcher (difflib).

**Parameters:**
- `str1` (str): First string.
- `str2` (str): Second string.

**Returns:**
- `float`: Similarity ratio between 0.0 and 1.0.

#### `_levenshtein_distance(str1: str, str2: str) -> int`

Calculate Levenshtein distance between two strings.

**Parameters:**
- `str1` (str): First string.
- `str2` (str): Second string.

**Returns:**
- `int`: Levenshtein distance (number of edits needed).

#### `_levenshtein_similarity(str1: str, str2: str) -> float`

Calculate similarity based on Levenshtein distance.

**Parameters:**
- `str1` (str): First string.
- `str2` (str): Second string.

**Returns:**
- `float`: Similarity ratio between 0.0 and 1.0.

#### `_jaro_winkler_similarity(str1: str, str2: str) -> float`

Calculate Jaro-Winkler similarity.

**Parameters:**
- `str1` (str): First string.
- `str2` (str): Second string.

**Returns:**
- `float`: Similarity ratio between 0.0 and 1.0.

#### `_calculate_similarity(str1: str, str2: str, algorithm: str = "sequence") -> float`

Calculate similarity using specified algorithm.

**Parameters:**
- `str1` (str): First string.
- `str2` (str): Second string.
- `algorithm` (str): Algorithm to use ('sequence', 'levenshtein', 'jaro_winkler').

**Returns:**
- `float`: Similarity ratio between 0.0 and 1.0.

#### `_extract_filename_parts(file_path: Path) -> Dict[str, str]`

Extract filename parts for comparison.

**Parameters:**
- `file_path` (Path): Path to file.

**Returns:**
- Dictionary with filename parts:
  - `full_name`: Full filename with extension
  - `name`: Filename without extension
  - `extension`: File extension
  - `path`: Full file path

### Attributes

#### `files: List[Dict[str, Any]]`

List of dictionaries containing file information for each scanned file.

#### `similar_pairs: List[Dict[str, Any]]`

List of dictionaries containing similar file pairs, each with:
- `file1`: Path to first file
- `file2`: Path to second file
- `name1`: Name of first file
- `name2`: Name of second file
- `similarity`: Similarity score (0.0-1.0)
- `algorithm`: Algorithm used

#### `stats: Dict[str, Any]`

Dictionary containing scanning statistics:
- `files_scanned`: Total number of files scanned
- `similar_pairs_found`: Number of similar pairs found
- `directories_scanned`: Number of directories scanned
- `errors`: Number of errors encountered

#### `config: dict`

Configuration dictionary loaded from YAML file.

### Example Usage

```python
from src.main import SimilarFileFinder

# Initialize with default config
finder = SimilarFileFinder()

# Or with custom config
finder = SimilarFileFinder(config_path="custom_config.yaml")

# Scan directory
finder.scan_directory("/path/to/directory")

# Find similar files
finder.find_similar_files()

# Generate report
finder.generate_report()

# Access results
print(f"Found {finder.stats['similar_pairs_found']} similar pairs")
for pair in finder.similar_pairs[:5]:
    print(f"{pair['file1']} <-> {pair['file2']} ({pair['similarity']:.3f})")
```

### Similarity Algorithms Comparison

**SequenceMatcher (Default):**
- Fast and effective
- Good for general-purpose similarity
- Uses Python's difflib library
- Best for: General file name comparison

**Levenshtein:**
- Measures edit distance
- Good for detecting typos
- More computationally intensive
- Best for: Finding files with small variations

**Jaro-Winkler:**
- Optimized for names
- Gives weight to common prefixes
- Good for short strings
- Best for: Person names, file names with prefixes

### Performance Considerations

- Algorithm complexity: O(n²) where n is number of files
- For large directories, scanning may take time
- SequenceMatcher is fastest
- Levenshtein is most computationally intensive
- Consider scanning subdirectories separately for very large trees
