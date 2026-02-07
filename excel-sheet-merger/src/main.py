"""Excel Sheet Merger - Process and merge multiple Excel sheets to CSV.

This module provides functionality to read multiple sheets from Excel files,
merge data with configurable strategies, validate data integrity, and export
the merged result to CSV format with comprehensive error handling.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ExcelSheetMerger:
    """Processes Excel files by merging multiple sheets into CSV format."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize ExcelSheetMerger with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.merged_df: Optional[pd.DataFrame] = None
        self.sheet_data: Dict[str, pd.DataFrame] = {}
        self.validation_errors: List[str] = []
        self.stats = {
            "sheets_processed": 0,
            "total_rows": 0,
            "merged_rows": 0,
            "validation_errors": 0,
            "sheets_skipped": 0,
        }

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid.
        """
        config_file = Path(config_path)

        if not config_file.is_absolute():
            if not config_file.exists():
                parent_config = Path(__file__).parent.parent / config_path
                if parent_config.exists():
                    config_file = parent_config
                else:
                    cwd_config = Path.cwd() / config_path
                    if cwd_config.exists():
                        config_file = cwd_config

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("INPUT_FILE"):
            config["files"]["input_file"] = os.getenv("INPUT_FILE")
        if os.getenv("OUTPUT_FILE"):
            config["files"]["output_file"] = os.getenv("OUTPUT_FILE")

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/excel_merger.log")

        log_path = Path(log_file)
        if not log_path.is_absolute():
            project_root = Path(__file__).parent.parent
            log_path = project_root / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()

        file_handler = logging.handlers.RotatingFileHandler(
            str(log_path),
            maxBytes=log_config.get("max_bytes", 10485760),
            backupCount=log_config.get("backup_count", 5),
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            log_config.get(
                "format",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        logger.info("Logging configured successfully")

    def _validate_excel_file(self, file_path: Path) -> bool:
        """Validate that the Excel file exists and is readable.

        Args:
            file_path: Path to Excel file.

        Returns:
            True if file is valid, False otherwise.
        """
        if not file_path.exists():
            error_msg = f"Excel file not found: {file_path}"
            logger.error(error_msg)
            self.validation_errors.append(error_msg)
            return False

        if not file_path.is_file():
            error_msg = f"Path is not a file: {file_path}"
            logger.error(error_msg)
            self.validation_errors.append(error_msg)
            return False

        valid_extensions = {".xlsx", ".xls", ".xlsm"}
        if file_path.suffix.lower() not in valid_extensions:
            error_msg = (
                f"Invalid file extension: {file_path.suffix}. "
                f"Expected one of {valid_extensions}"
            )
            logger.error(error_msg)
            self.validation_errors.append(error_msg)
            return False

        return True

    def load_excel_sheets(
        self, file_path: str, sheet_names: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """Load specified sheets from Excel file.

        Args:
            file_path: Path to Excel file.
            sheet_names: List of sheet names to load. If None, loads all sheets.

        Returns:
            Dictionary mapping sheet names to DataFrames.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If specified sheets don't exist.
            pd.errors.ExcelFileError: If file is not a valid Excel file.
        """
        excel_path = Path(file_path)

        if not self._validate_excel_file(excel_path):
            raise FileNotFoundError(f"Excel file validation failed: {file_path}")

        try:
            excel_file = pd.ExcelFile(excel_path, engine="openpyxl")
            available_sheets = excel_file.sheet_names
            logger.info(
                f"Found {len(available_sheets)} sheet(s) in {file_path}: "
                f"{', '.join(available_sheets)}"
            )

            if sheet_names is None:
                # Load all sheets if none specified
                sheet_names = available_sheets
            else:
                # Validate specified sheets exist
                missing_sheets = set(sheet_names) - set(available_sheets)
                if missing_sheets:
                    error_msg = (
                        f"Specified sheets not found: {', '.join(missing_sheets)}. "
                        f"Available sheets: {', '.join(available_sheets)}"
                    )
                    logger.error(error_msg)
                    self.validation_errors.append(error_msg)
                    raise ValueError(error_msg)

            loaded_sheets = {}
            for sheet_name in sheet_names:
                try:
                    df = pd.read_excel(
                        excel_file,
                        sheet_name=sheet_name,
                        engine="openpyxl",
                        header=self.config.get("reading", {}).get("header_row", 0),
                    )
                    # Add sheet name as column for tracking
                    if self.config.get("merging", {}).get("add_sheet_column", True):
                        df.insert(0, "source_sheet", sheet_name)
                    loaded_sheets[sheet_name] = df
                    logger.info(
                        f"Loaded sheet '{sheet_name}': {len(df)} rows, "
                        f"{len(df.columns)} columns"
                    )
                except Exception as e:
                    error_msg = f"Error loading sheet '{sheet_name}': {e}"
                    logger.error(error_msg)
                    self.validation_errors.append(error_msg)
                    if self.config.get("error_handling", {}).get("skip_invalid_sheets", False):
                        logger.warning(f"Skipping invalid sheet: {sheet_name}")
                        self.stats["sheets_skipped"] += 1
                        continue
                    raise

            self.sheet_data.update(loaded_sheets)
            self.stats["sheets_processed"] = len(loaded_sheets)
            logger.info(f"Successfully loaded {len(loaded_sheets)} sheet(s)")

            return loaded_sheets

        except pd.errors.ExcelFileError as e:
            error_msg = f"Invalid Excel file format: {e}"
            logger.error(error_msg)
            self.validation_errors.append(error_msg)
            raise pd.errors.ExcelFileError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error loading Excel file: {e}"
            logger.error(error_msg, exc_info=True)
            self.validation_errors.append(error_msg)
            raise

    def _validate_dataframe(self, df: pd.DataFrame, sheet_name: str) -> List[str]:
        """Validate DataFrame data quality.

        Args:
            df: DataFrame to validate.
            sheet_name: Name of the sheet being validated.

        Returns:
            List of validation error messages.
        """
        errors = []
        validation_config = self.config.get("validation", {})

        if not validation_config.get("enabled", True):
            return errors

        # Check for empty DataFrame
        if df.empty:
            errors.append(f"Sheet '{sheet_name}' is empty")
            return errors

        # Check required columns
        required_cols = validation_config.get("required_columns", [])
        missing_cols = set(required_cols) - set(df.columns)
        if missing_cols:
            errors.append(
                f"Sheet '{sheet_name}' missing required columns: "
                f"{', '.join(missing_cols)}"
            )

        # Check for duplicate rows
        if validation_config.get("check_duplicates", False):
            duplicates = df.duplicated().sum()
            if duplicates > 0:
                errors.append(
                    f"Sheet '{sheet_name}' contains {duplicates} duplicate row(s)"
                )

        # Check for missing values in critical columns
        critical_cols = validation_config.get("critical_columns", [])
        for col in critical_cols:
            if col in df.columns:
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    errors.append(
                        f"Sheet '{sheet_name}', column '{col}': "
                        f"{missing_count} missing value(s)"
                    )

        # Check data types
        if validation_config.get("check_data_types", False):
            type_checks = validation_config.get("column_types", {})
            for col, expected_type in type_checks.items():
                if col in df.columns:
                    if expected_type == "numeric":
                        if not pd.api.types.is_numeric_dtype(df[col]):
                            errors.append(
                                f"Sheet '{sheet_name}', column '{col}': "
                                f"expected numeric type"
                            )
                    elif expected_type == "date":
                        if not pd.api.types.is_datetime64_any_dtype(df[col]):
                            errors.append(
                                f"Sheet '{sheet_name}', column '{col}': "
                                f"expected date type"
                            )

        return errors

    def _merge_dataframes(self) -> pd.DataFrame:
        """Merge all loaded DataFrames based on configuration strategy.

        Returns:
            Merged DataFrame.

        Raises:
            ValueError: If no sheets are loaded or merge strategy is invalid.
        """
        if not self.sheet_data:
            raise ValueError("No sheets loaded. Call load_excel_sheets() first.")

        merge_config = self.config.get("merging", {})
        strategy = merge_config.get("strategy", "concat")

        logger.info(f"Merging {len(self.sheet_data)} sheet(s) using strategy: {strategy}")

        if strategy == "concat":
            # Simple concatenation of all sheets
            dfs = list(self.sheet_data.values())
            merged = pd.concat(dfs, ignore_index=True)
            logger.info(f"Concatenated {len(dfs)} sheet(s)")

        elif strategy == "union":
            # Union: combine all unique columns
            all_columns = set()
            for df in self.sheet_data.values():
                all_columns.update(df.columns)
            all_columns = sorted(list(all_columns))

            dfs_aligned = []
            for sheet_name, df in self.sheet_data.items():
                df_aligned = df.reindex(columns=all_columns)
                dfs_aligned.append(df_aligned)

            merged = pd.concat(dfs_aligned, ignore_index=True)
            logger.info(f"Union merge: {len(all_columns)} total columns")

        elif strategy == "intersection":
            # Intersection: only common columns
            common_columns = None
            for df in self.sheet_data.values():
                if common_columns is None:
                    common_columns = set(df.columns)
                else:
                    common_columns &= set(df.columns)

            if not common_columns:
                raise ValueError("No common columns found across sheets")

            dfs_aligned = []
            for df in self.sheet_data.values():
                df_aligned = df[list(common_columns)]
                dfs_aligned.append(df_aligned)

            merged = pd.concat(dfs_aligned, ignore_index=True)
            logger.info(f"Intersection merge: {len(common_columns)} common columns")

        elif strategy == "join":
            # Join on specified key columns
            join_config = merge_config.get("join", {})
            join_keys = join_config.get("keys", [])
            join_type = join_config.get("type", "inner")

            if not join_keys:
                raise ValueError("Join strategy requires 'join.keys' configuration")

            merged = None
            for sheet_name, df in self.sheet_data.items():
                if merged is None:
                    merged = df
                else:
                    # Verify join keys exist
                    missing_keys = set(join_keys) - set(df.columns)
                    if missing_keys:
                        logger.warning(
                            f"Sheet '{sheet_name}' missing join keys: "
                            f"{', '.join(missing_keys)}"
                        )
                        continue

                    merged = pd.merge(
                        merged, df, on=join_keys, how=join_type, suffixes=("", f"_{sheet_name}")
                    )

            if merged is None:
                raise ValueError("Failed to perform join merge")

            logger.info(f"Join merge on keys: {', '.join(join_keys)}")

        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        self.stats["total_rows"] = sum(len(df) for df in self.sheet_data.values())
        self.stats["merged_rows"] = len(merged)

        logger.info(
            f"Merged {self.stats['total_rows']} total rows into "
            f"{self.stats['merged_rows']} merged rows"
        )

        return merged

    def _clean_merged_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean merged DataFrame based on configuration.

        Args:
            df: DataFrame to clean.

        Returns:
            Cleaned DataFrame.
        """
        clean_config = self.config.get("cleaning", {})
        if not clean_config.get("enabled", True):
            return df

        cleaned_df = df.copy()

        # Remove duplicate rows
        if clean_config.get("remove_duplicates", False):
            before = len(cleaned_df)
            cleaned_df = cleaned_df.drop_duplicates()
            removed = before - len(cleaned_df)
            if removed > 0:
                logger.info(f"Removed {removed} duplicate row(s)")

        # Remove empty rows
        if clean_config.get("remove_empty_rows", False):
            before = len(cleaned_df)
            cleaned_df = cleaned_df.dropna(how="all")
            removed = before - len(cleaned_df)
            if removed > 0:
                logger.info(f"Removed {removed} empty row(s)")

        # Remove empty columns
        if clean_config.get("remove_empty_columns", False):
            before = len(cleaned_df.columns)
            cleaned_df = cleaned_df.dropna(axis=1, how="all")
            removed = before - len(cleaned_df.columns)
            if removed > 0:
                logger.info(f"Removed {removed} empty column(s)")

        # Reset index
        cleaned_df = cleaned_df.reset_index(drop=True)

        return cleaned_df

    def process(self) -> Dict[str, Any]:
        """Process Excel file: load sheets, merge, validate, and prepare for export.

        Returns:
            Dictionary with processing statistics.

        Raises:
            ValueError: If input file is not specified or processing fails.
        """
        input_file = self.config["files"]["input_file"]
        if not input_file:
            raise ValueError("Input file not specified in configuration")

        logger.info("Starting Excel sheet processing")

        # Load sheets
        sheet_names = self.config.get("sheets", {}).get("names")
        self.load_excel_sheets(input_file, sheet_names)

        # Validate each sheet
        for sheet_name, df in self.sheet_data.items():
            errors = self._validate_dataframe(df, sheet_name)
            self.validation_errors.extend(errors)
            if errors:
                logger.warning(f"Validation errors in sheet '{sheet_name}': {len(errors)}")

        self.stats["validation_errors"] = len(self.validation_errors)

        # Merge sheets
        self.merged_df = self._merge_dataframes()

        # Clean merged data
        self.merged_df = self._clean_merged_data(self.merged_df)

        logger.info("Excel processing completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def export_to_csv(self, file_path: str) -> None:
        """Export merged DataFrame to CSV file.

        Args:
            file_path: Path to output CSV file.

        Raises:
            ValueError: If no merged data is available.
            PermissionError: If output directory is not writable.
        """
        if self.merged_df is None:
            raise ValueError("No merged data available. Call process() first.")

        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            csv_config = self.config.get("csv_export", {})
            self.merged_df.to_csv(
                output_path,
                index=csv_config.get("include_index", False),
                encoding=csv_config.get("encoding", "utf-8"),
                sep=csv_config.get("separator", ","),
                na_rep=csv_config.get("na_representation", ""),
            )
            logger.info(
                f"Exported {len(self.merged_df)} rows to CSV: {output_path}"
            )
        except PermissionError:
            error_msg = f"Permission denied writing to: {output_path}"
            logger.error(error_msg)
            raise PermissionError(error_msg)
        except Exception as e:
            error_msg = f"Error exporting to CSV: {e}"
            logger.error(error_msg, exc_info=True)
            raise


def main() -> int:
    """Main entry point for Excel sheet merger."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process Excel files: merge multiple sheets and export to CSV"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Input Excel file path (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV file path (overrides config)",
    )

    args = parser.parse_args()

    try:
        merger = ExcelSheetMerger(config_path=args.config)

        if args.input:
            merger.config["files"]["input_file"] = args.input
        if args.output:
            merger.config["files"]["output_file"] = args.output

        stats = merger.process()

        # Export to CSV
        output_file = merger.config["files"]["output_file"]
        if output_file:
            merger.export_to_csv(output_file)
        else:
            logger.warning("Output file not specified, skipping export")

        # Print summary
        print("\n" + "=" * 50)
        print("Excel Processing Summary")
        print("=" * 50)
        print(f"Sheets processed: {stats['sheets_processed']}")
        print(f"Total rows: {stats['total_rows']}")
        print(f"Merged rows: {stats['merged_rows']}")
        print(f"Validation errors: {stats['validation_errors']}")
        print(f"Sheets skipped: {stats['sheets_skipped']}")

        if merger.validation_errors:
            print("\nValidation Errors:")
            for error in merger.validation_errors:
                print(f"  - {error}")

        if output_file:
            print(f"\nCSV exported to: {output_file}")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
