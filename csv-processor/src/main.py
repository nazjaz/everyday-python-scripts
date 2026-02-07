"""CSV Processor - Clean and validate CSV files.

This module provides functionality to process CSV files by removing duplicate
rows, standardizing date formats, cleaning data inconsistencies, and generating
detailed validation reports.
"""

import logging
import logging.handlers
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class CSVProcessor:
    """Processes CSV files with cleaning and validation."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize CSVProcessor with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.df: Optional[pd.DataFrame] = None
        self.original_df: Optional[pd.DataFrame] = None
        self.report_lines: List[str] = []
        self.stats = {
            "original_rows": 0,
            "final_rows": 0,
            "duplicates_removed": 0,
            "dates_standardized": 0,
            "invalid_dates": 0,
            "rows_cleaned": 0,
            "validation_errors": 0,
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
        log_file = log_config.get("file", "logs/csv_processor.log")

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

    def _add_report_line(self, line: str) -> None:
        """Add line to validation report.

        Args:
            line: Line to add to report.
        """
        self.report_lines.append(line)
        logger.debug(line)

    def load_csv(self, file_path: str) -> None:
        """Load CSV file into DataFrame.

        Args:
            file_path: Path to CSV file.

        Raises:
            FileNotFoundError: If file doesn't exist.
            pd.errors.EmptyDataError: If file is empty.
        """
        csv_path = Path(file_path)
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            self.df = pd.read_csv(csv_path, encoding="utf-8")
            self.original_df = self.df.copy()
            self.stats["original_rows"] = len(self.df)
            logger.info(f"Loaded CSV file: {file_path} ({len(self.df)} rows, {len(self.df.columns)} columns)")
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(f"CSV file is empty: {file_path}")
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise

    def _remove_duplicates(self) -> None:
        """Remove duplicate rows based on configuration."""
        if not self.config.get("duplicate_removal", {}).get("enabled", True):
            return

        dup_config = self.config["duplicate_removal"]
        method = dup_config.get("method", "all_columns")
        keep = dup_config.get("keep", "first")

        original_count = len(self.df)

        if method == "all_columns":
            self.df = self.df.drop_duplicates(keep=keep)
        elif method == "specific_columns":
            columns = dup_config.get("columns", [])
            if columns:
                # Verify columns exist
                valid_columns = [col for col in columns if col in self.df.columns]
                if valid_columns:
                    self.df = self.df.drop_duplicates(subset=valid_columns, keep=keep)
                else:
                    logger.warning("No valid columns specified for duplicate removal")
                    return
            else:
                logger.warning("No columns specified for duplicate removal")
                return
        else:
            # ignore_case method
            if not dup_config.get("case_sensitive", True):
                # Convert to lowercase for comparison
                df_lower = self.df.applymap(
                    lambda x: str(x).lower() if pd.notna(x) else x
                )
                self.df = self.df[~df_lower.duplicated(keep=keep)]

        removed = original_count - len(self.df)
        self.stats["duplicates_removed"] = removed

        if removed > 0:
            logger.info(f"Removed {removed} duplicate row(s)")
            self._add_report_line(f"Duplicates Removed: {removed} row(s)")

            if self.config.get("reporting", {}).get("include_duplicates", True):
                self._add_report_line("\nDuplicate Rows Details:")
                # Find and report duplicate rows
                if method == "all_columns":
                    duplicates = self.original_df[
                        self.original_df.duplicated(keep=False)
                    ]
                else:
                    columns = dup_config.get("columns", [])
                    duplicates = self.original_df[
                        self.original_df.duplicated(subset=columns, keep=False)
                    ]

                for idx, row in duplicates.iterrows():
                    self._add_report_line(f"  Row {idx + 1}: {dict(row)}")

    def _standardize_dates(self) -> None:
        """Standardize date formats in specified columns."""
        if not self.config.get("date_standardization", {}).get("enabled", True):
            return

        date_config = self.config["date_standardization"]
        target_format = date_config.get("target_format", "%Y-%m-%d")
        date_columns = date_config.get("date_columns", [])
        input_formats = date_config.get("input_formats", [])
        handle_invalid = date_config.get("handle_invalid_dates", "skip")

        # Auto-detect date columns if not specified
        if not date_columns:
            date_columns = []
            for col in self.df.columns:
                # Try to parse a sample of values
                sample = self.df[col].dropna().head(10)
                if len(sample) > 0:
                    date_count = 0
                    for value in sample:
                        if self._try_parse_date(str(value), input_formats):
                            date_count += 1
                    if date_count >= len(sample) * 0.7:  # 70% are dates
                        date_columns.append(col)

        standardized = 0
        invalid = 0

        for col in date_columns:
            if col not in self.df.columns:
                logger.warning(f"Date column not found: {col}")
                continue

            original_values = self.df[col].copy()
            converted_values = []

            for idx, value in self.df[col].items():
                if pd.isna(value):
                    converted_values.append(value)
                    continue

                parsed_date = self._try_parse_date(str(value), input_formats)
                if parsed_date:
                    converted_values.append(parsed_date.strftime(target_format))
                    standardized += 1
                else:
                    if handle_invalid == "skip":
                        converted_values.append(None)
                        invalid += 1
                    elif handle_invalid == "keep_original":
                        converted_values.append(value)
                    else:  # set_null
                        converted_values.append(None)
                        invalid += 1

            self.df[col] = converted_values

        self.stats["dates_standardized"] = standardized
        self.stats["invalid_dates"] = invalid

        if standardized > 0:
            logger.info(f"Standardized {standardized} date value(s)")
            self._add_report_line(f"Dates Standardized: {standardized} value(s)")

        if invalid > 0:
            logger.warning(f"Found {invalid} invalid date value(s)")
            self._add_report_line(f"Invalid Dates: {invalid} value(s)")

            if self.config.get("reporting", {}).get("include_invalid_dates", True):
                self._add_report_line("\nInvalid Date Values:")
                for col in date_columns:
                    if col in self.df.columns:
                        invalid_mask = self.df[col].isna() & self.original_df[col].notna()
                        invalid_rows = self.original_df[invalid_mask]
                        for idx, row in invalid_rows.iterrows():
                            self._add_report_line(
                                f"  Row {idx + 1}, Column '{col}': {row[col]}"
                            )

    def _try_parse_date(self, value: str, formats: List[str]) -> Optional[datetime]:
        """Try to parse date string using multiple formats.

        Args:
            value: Date string to parse.
            formats: List of date format strings to try.

        Returns:
            Parsed datetime object or None.
        """
        for fmt in formats:
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
        return None

    def _clean_data(self) -> None:
        """Clean data inconsistencies."""
        if not self.config.get("data_cleaning", {}).get("enabled", True):
            return

        clean_config = self.config["data_cleaning"]
        cleaned_count = 0

        # Trim whitespace
        if clean_config.get("trim_whitespace", True):
            for col in self.df.select_dtypes(include=["object"]).columns:
                self.df[col] = self.df[col].apply(
                    lambda x: str(x).strip() if pd.notna(x) else x
                )
                cleaned_count += self.df[col].notna().sum()

        # Normalize whitespace
        if clean_config.get("normalize_whitespace", True):
            for col in self.df.select_dtypes(include=["object"]).columns:
                self.df[col] = self.df[col].apply(
                    lambda x: re.sub(r"\s+", " ", str(x)) if pd.notna(x) else x
                )

        # Strip quotes
        if clean_config.get("strip_quotes", True):
            for col in self.df.select_dtypes(include=["object"]).columns:
                self.df[col] = self.df[col].apply(
                    lambda x: str(x).strip('"\'') if pd.notna(x) else x
                )

        # Remove empty rows
        if clean_config.get("remove_empty_rows", False):
            before = len(self.df)
            self.df = self.df.dropna(how="all")
            removed = before - len(self.df)
            if removed > 0:
                logger.info(f"Removed {removed} empty row(s)")

        # Remove empty columns
        if clean_config.get("remove_empty_columns", False):
            before = len(self.df.columns)
            self.df = self.df.dropna(axis=1, how="all")
            removed = before - len(self.df.columns)
            if removed > 0:
                logger.info(f"Removed {removed} empty column(s)")

        # Lowercase column names
        if clean_config.get("lowercase_columns", False):
            self.df.columns = [col.lower() for col in self.df.columns]

        self.stats["rows_cleaned"] = cleaned_count
        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} value(s)")
            self._add_report_line(f"Values Cleaned: {cleaned_count} value(s)")

    def _validate_data(self) -> None:
        """Validate data and generate validation report."""
        if not self.config.get("validation", {}).get("enabled", True):
            return

        validation_config = self.config["validation"]
        errors = []

        # Check missing values
        if validation_config.get("check_missing_values", True):
            missing = self.df.isnull().sum()
            missing_cols = missing[missing > 0]
            if len(missing_cols) > 0:
                self._add_report_line("\nMissing Values:")
                for col, count in missing_cols.items():
                    percentage = (count / len(self.df)) * 100
                    self._add_report_line(
                        f"  Column '{col}': {count} ({percentage:.1f}%)"
                    )

        # Check required columns
        required = validation_config.get("required_columns", [])
        for col in required:
            if col not in self.df.columns:
                errors.append(f"Required column '{col}' not found")
            elif self.df[col].isnull().any():
                missing_count = self.df[col].isnull().sum()
                errors.append(
                    f"Required column '{col}' has {missing_count} missing value(s)"
                )

        # Check unique columns
        unique_cols = validation_config.get("unique_columns", [])
        for col in unique_cols:
            if col in self.df.columns:
                duplicates = self.df[col].duplicated().sum()
                if duplicates > 0:
                    errors.append(
                        f"Unique column '{col}' has {duplicates} duplicate value(s)"
                    )

        # Check value ranges
        if validation_config.get("check_value_ranges", False):
            ranges = validation_config.get("value_ranges", {})
            for col, range_config in ranges.items():
                if col in self.df.columns:
                    min_val = range_config.get("min")
                    max_val = range_config.get("max")
                    if min_val is not None:
                        below_min = (self.df[col] < min_val).sum()
                        if below_min > 0:
                            errors.append(
                                f"Column '{col}': {below_min} value(s) below minimum {min_val}"
                            )
                    if max_val is not None:
                        above_max = (self.df[col] > max_val).sum()
                        if above_max > 0:
                            errors.append(
                                f"Column '{col}': {above_max} value(s) above maximum {max_val}"
                            )

        self.stats["validation_errors"] = len(errors)

        if errors:
            logger.warning(f"Found {len(errors)} validation error(s)")
            self._add_report_line(f"\nValidation Errors: {len(errors)}")
            for error in errors:
                self._add_report_line(f"  - {error}")

    def _generate_report(self) -> None:
        """Generate validation report file."""
        report_config = self.config.get("reporting", {})
        report_file = self.config["files"].get("report_file", "logs/validation_report.txt")

        report_path = Path(report_file)
        if not report_path.is_absolute():
            project_root = Path(__file__).parent.parent
            report_path = project_root / report_file

        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("CSV Processing Validation Report\n")
            f.write("=" * 60 + "\n\n")

            if report_config.get("include_summary", True):
                f.write("Processing Summary\n")
                f.write("-" * 60 + "\n")
                f.write(f"Original Rows: {self.stats['original_rows']}\n")
                f.write(f"Final Rows: {self.stats['final_rows']}\n")
                f.write(f"Duplicates Removed: {self.stats['duplicates_removed']}\n")
                f.write(f"Dates Standardized: {self.stats['dates_standardized']}\n")
                f.write(f"Invalid Dates: {self.stats['invalid_dates']}\n")
                f.write(f"Values Cleaned: {self.stats['rows_cleaned']}\n")
                f.write(f"Validation Errors: {self.stats['validation_errors']}\n")
                f.write("\n")

            if report_config.get("include_statistics", True):
                f.write("Column Statistics\n")
                f.write("-" * 60 + "\n")
                for col in self.df.columns:
                    f.write(f"\nColumn: {col}\n")
                    f.write(f"  Data Type: {self.df[col].dtype}\n")
                    f.write(f"  Non-null Count: {self.df[col].notna().sum()}\n")
                    f.write(f"  Null Count: {self.df[col].isnull().sum()}\n")
                    if self.df[col].dtype in ["int64", "float64"]:
                        f.write(f"  Min: {self.df[col].min()}\n")
                        f.write(f"  Max: {self.df[col].max()}\n")
                        f.write(f"  Mean: {self.df[col].mean():.2f}\n")
                f.write("\n")

            # Write detailed report lines
            for line in self.report_lines:
                f.write(line + "\n")

        logger.info(f"Validation report saved to: {report_path}")

    def process(self) -> Dict[str, int]:
        """Process CSV file with all configured operations.

        Returns:
            Dictionary with processing statistics.
        """
        input_file = self.config["files"]["input_file"]
        if not input_file:
            raise ValueError("Input file not specified in configuration")

        logger.info("Starting CSV processing")

        # Load CSV
        self.load_csv(input_file)

        # Process data
        self._remove_duplicates()
        self._standardize_dates()
        self._clean_data()
        self._validate_data()

        self.stats["final_rows"] = len(self.df)

        # Generate report
        self._generate_report()

        logger.info("CSV processing completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats

    def save_csv(self, file_path: str) -> None:
        """Save processed DataFrame to CSV file.

        Args:
            file_path: Path to output CSV file.
        """
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"Processed CSV saved to: {output_path}")


def main() -> int:
    """Main entry point for CSV processor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Process CSV files: remove duplicates, standardize dates, clean data"
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
        help="Input CSV file path (overrides config)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV file path (overrides config)",
    )

    args = parser.parse_args()

    try:
        processor = CSVProcessor(config_path=args.config)

        if args.input:
            processor.config["files"]["input_file"] = args.input
        if args.output:
            processor.config["files"]["output_file"] = args.output

        stats = processor.process()

        # Save output
        output_file = processor.config["files"]["output_file"]
        if output_file:
            processor.save_csv(output_file)
        else:
            logger.warning("Output file not specified, skipping save")

        # Print summary
        print("\n" + "=" * 50)
        print("CSV Processing Summary")
        print("=" * 50)
        print(f"Original rows: {stats['original_rows']}")
        print(f"Final rows: {stats['final_rows']}")
        print(f"Duplicates removed: {stats['duplicates_removed']}")
        print(f"Dates standardized: {stats['dates_standardized']}")
        print(f"Invalid dates: {stats['invalid_dates']}")
        print(f"Validation errors: {stats['validation_errors']}")
        print(f"\nReport saved to: {processor.config['files']['report_file']}")

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
