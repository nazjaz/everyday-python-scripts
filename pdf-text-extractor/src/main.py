"""PDF Text Extractor - Extract text content from PDF files.

This module provides functionality to extract text content from PDF files
and save it to text files with the same name. Handles encrypted PDFs,
multi-page PDFs, and includes comprehensive logging and error handling.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.errors import PdfReadError

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class PDFTextExtractor:
    """Extracts text content from PDF files and saves to text files."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize PDFTextExtractor with configuration.

        Args:
            config_path: Path to configuration YAML file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            yaml.YAMLError: If config file is invalid YAML.
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._setup_directories()
        self.stats = {
            "files_scanned": 0,
            "files_processed": 0,
            "files_skipped": 0,
            "encrypted_skipped": 0,
            "errors": 0,
            "errors_list": [],
            "total_pages": 0,
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
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override with environment variables if present
        if os.getenv("SOURCE_DIRECTORY"):
            config["source_directory"] = os.getenv("SOURCE_DIRECTORY")
        if os.getenv("DESTINATION_DIRECTORY"):
            config["destination_directory"] = os.getenv("DESTINATION_DIRECTORY")
        if os.getenv("PDF_PASSWORD"):
            config["pdf_password"] = os.getenv("PDF_PASSWORD")
        if os.getenv("DRY_RUN"):
            config["operations"]["dry_run"] = (
                os.getenv("DRY_RUN").lower() == "true"
            )

        return config

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("level", "INFO"))
        log_file = log_config.get("file", "logs/pdf_text_extractor.log")

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

    def _setup_directories(self) -> None:
        """Set up source and destination directories."""
        self.source_dir = Path(
            os.path.expanduser(self.config["source_directory"])
        )
        self.dest_dir = Path(
            os.path.expanduser(self.config["destination_directory"])
        )

        if not self.source_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {self.source_dir}"
            )

        if self.config["operations"]["create_destination"]:
            self.dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Destination directory: {self.dest_dir}")

    def _is_pdf_file(self, file_path: Path) -> bool:
        """Check if file is a PDF.

        Args:
            file_path: Path to file to check.

        Returns:
            True if file is a PDF, False otherwise.
        """
        return file_path.suffix.lower() == ".pdf"

    def _extract_text_from_pdf(
        self, pdf_path: Path, password: Optional[str] = None
    ) -> Optional[str]:
        """Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file.
            password: Optional password for encrypted PDFs.

        Returns:
            Extracted text as string, or None if extraction failed.
        """
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PdfReader(file)

                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    logger.info(f"PDF is encrypted: {pdf_path.name}")

                    # Try to decrypt with provided password
                    if password:
                        if pdf_reader.decrypt(password):
                            logger.info(
                                f"Successfully decrypted PDF: {pdf_path.name}"
                            )
                        else:
                            logger.warning(
                                f"Failed to decrypt PDF with provided "
                                f"password: {pdf_path.name}"
                            )
                            if not self.config.get("skip_encrypted", True):
                                return None
                            self.stats["encrypted_skipped"] += 1
                            return None
                    else:
                        logger.warning(
                            f"PDF is encrypted but no password provided: "
                            f"{pdf_path.name}"
                        )
                        if not self.config.get("skip_encrypted", True):
                            return None
                        self.stats["encrypted_skipped"] += 1
                        return None

                # Extract text from all pages
                text_parts = []
                num_pages = len(pdf_reader.pages)
                self.stats["total_pages"] += num_pages

                logger.debug(
                    f"Extracting text from {num_pages} pages in "
                    f"{pdf_path.name}"
                )

                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    try:
                        page_text = page.extract_text()

                        if page_text:
                            # Add page separator if multi-page
                            if num_pages > 1:
                                text_parts.append(
                                    f"\n--- Page {page_num} ---\n"
                                )
                            text_parts.append(page_text)
                        else:
                            logger.debug(
                                f"No text found on page {page_num} of "
                                f"{pdf_path.name}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Error extracting text from page {page_num} of "
                            f"{pdf_path.name}: {e}"
                        )
                        continue

                if text_parts:
                    extracted_text = "\n".join(text_parts)
                    logger.debug(
                        f"Extracted {len(extracted_text)} characters from "
                        f"{pdf_path.name}"
                    )
                    return extracted_text
                else:
                    logger.warning(
                        f"No text extracted from {pdf_path.name} "
                        f"(may be image-based PDF)"
                    )
                    return None

        except PdfReadError as e:
            error_msg = f"Error reading PDF {pdf_path.name}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error processing {pdf_path.name}: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return None

    def _save_text_to_file(
        self, text: str, output_path: Path, pdf_name: str
    ) -> bool:
        """Save extracted text to file.

        Args:
            text: Text content to save.
            output_path: Path to output text file.
            pdf_name: Original PDF filename for logging.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if self.config["operations"]["dry_run"]:
                logger.info(
                    f"[DRY RUN] Would save text to: "
                    f"{output_path.relative_to(self.dest_dir)}"
                )
                return True

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write text to file
            encoding = self.config.get("output_encoding", "utf-8")
            with open(output_path, "w", encoding=encoding) as f:
                f.write(text)

            logger.info(
                f"Saved text from {pdf_name} to "
                f"{output_path.relative_to(self.dest_dir)} "
                f"({len(text)} characters)"
            )
            return True

        except Exception as e:
            error_msg = f"Error saving text to {output_path}: {e}"
            logger.error(error_msg)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            return False

    def _process_pdf_file(self, pdf_path: Path) -> bool:
        """Process a single PDF file.

        Args:
            pdf_path: Path to PDF file to process.

        Returns:
            True if successful, False otherwise.
        """
        self.stats["files_scanned"] += 1

        try:
            # Get password if configured
            password = self.config.get("pdf_password")

            # Extract text from PDF
            extracted_text = self._extract_text_from_pdf(pdf_path, password)

            if extracted_text is None:
                self.stats["files_skipped"] += 1
                return False

            # Determine output file path
            if self.config["operations"]["preserve_structure"]:
                # Preserve directory structure relative to source
                relative_path = pdf_path.relative_to(self.source_dir)
                output_path = self.dest_dir / relative_path.with_suffix(".txt")
            else:
                # Save directly to destination with same name
                output_path = self.dest_dir / pdf_path.with_suffix(".txt").name

            # Save text to file
            if self._save_text_to_file(extracted_text, output_path, pdf_path.name):
                self.stats["files_processed"] += 1
                return True
            else:
                self.stats["files_skipped"] += 1
                return False

        except Exception as e:
            error_msg = f"Error processing {pdf_path}: {e}"
            logger.error(error_msg, exc_info=True)
            self.stats["errors"] += 1
            self.stats["errors_list"].append(error_msg)
            self.stats["files_skipped"] += 1
            return False

    def extract_text_from_pdfs(self) -> Dict[str, any]:
        """Extract text from all PDF files in source directory.

        Returns:
            Dictionary with statistics about the operation.
        """
        logger.info("Starting PDF text extraction")
        logger.info(f"Dry run mode: {self.config['operations']['dry_run']}")

        # Find all PDF files
        pdf_files = []
        if self.config["operations"]["recursive"]:
            for file_path in self.source_dir.rglob("*.pdf"):
                if file_path.is_file() and self._is_pdf_file(file_path):
                    pdf_files.append(file_path)
        else:
            for file_path in self.source_dir.iterdir():
                if file_path.is_file() and self._is_pdf_file(file_path):
                    pdf_files.append(file_path)

        logger.info(f"Found {len(pdf_files)} PDF files to process")

        # Process each PDF file
        for pdf_path in pdf_files:
            self._process_pdf_file(pdf_path)

        logger.info("PDF text extraction completed")
        logger.info(f"Statistics: {self.stats}")

        return self.stats


def main() -> int:
    """Main entry point for PDF text extractor."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract text content from PDF files and save to text files"
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Preview changes without creating text files",
    )
    parser.add_argument(
        "-p",
        "--password",
        help="Password for encrypted PDFs (overrides config)",
    )

    args = parser.parse_args()

    try:
        extractor = PDFTextExtractor(config_path=args.config)

        if args.dry_run:
            extractor.config["operations"]["dry_run"] = True

        if args.password:
            extractor.config["pdf_password"] = args.password

        stats = extractor.extract_text_from_pdfs()

        # Print summary
        print("\n" + "=" * 60)
        print("PDF Text Extraction Summary")
        print("=" * 60)
        print(f"Files Scanned: {stats['files_scanned']}")
        print(f"Files Processed: {stats['files_processed']}")
        print(f"Files Skipped: {stats['files_skipped']}")
        print(f"Encrypted PDFs Skipped: {stats['encrypted_skipped']}")
        print(f"Total Pages Processed: {stats['total_pages']}")
        print(f"Errors: {stats['errors']}")

        if stats["errors_list"]:
            print("\nErrors:")
            for error in stats["errors_list"][:10]:
                print(f"  - {error}")
            if len(stats["errors_list"]) > 10:
                print(f"  ... and {len(stats['errors_list']) - 10} more")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
