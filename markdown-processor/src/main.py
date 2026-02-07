"""Markdown Processor.

A Python script that processes markdown files by validating links, checking
for broken references, and generating table of contents automatically.
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/processor.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available. External link validation disabled.")


class MarkdownProcessor:
    """Processes markdown files for validation and TOC generation."""

    HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    REFERENCE_PATTERN = re.compile(r"\[([^\]]+)\]:\s*(.+)")
    IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def __init__(
        self,
        base_path: Optional[Path] = None,
        validate_external_links: bool = False,
        toc_placement: str = "top",
        toc_min_depth: int = 2,
        toc_max_depth: int = 6,
    ) -> None:
        """Initialize the markdown processor.

        Args:
            base_path: Base path for resolving relative links
            validate_external_links: If True, validate external HTTP/HTTPS links
            toc_placement: Where to place TOC - "top", "after-first-header", or "none"
            toc_min_depth: Minimum header depth for TOC (default: 2)
            toc_max_depth: Maximum header depth for TOC (default: 6)
        """
        self.base_path = base_path
        self.validate_external_links = validate_external_links
        self.toc_placement = toc_placement
        self.toc_min_depth = toc_min_depth
        self.toc_max_depth = toc_max_depth

        self.stats = {
            "files_processed": 0,
            "links_found": 0,
            "broken_links": 0,
            "external_links": 0,
            "internal_links": 0,
            "references_found": 0,
            "broken_references": 0,
            "toc_generated": 0,
        }

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug.

        Args:
            text: Text to slugify

        Returns:
            URL-friendly slug
        """
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        return text.strip("-")

    def _extract_headers(self, content: str) -> List[Tuple[int, str, str]]:
        """Extract headers from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of tuples (level, text, slug)
        """
        headers = []
        for match in self.HEADER_PATTERN.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            slug = self._slugify(text)
            headers.append((level, text, slug))
        return headers

    def _extract_links(self, content: str) -> List[Tuple[str, str, str]]:
        """Extract links from markdown content.

        Args:
            content: Markdown content

        Returns:
            List of tuples (link_text, url, link_type)
        """
        links = []
        for match in self.LINK_PATTERN.finditer(content):
            link_text = match.group(1)
            url = match.group(2)
            link_type = self._classify_link(url)
            links.append((link_text, url, link_type))
        return links

    def _extract_references(self, content: str) -> Dict[str, str]:
        """Extract reference definitions from markdown content.

        Args:
            content: Markdown content

        Returns:
            Dictionary mapping reference labels to URLs
        """
        references = {}
        for match in self.REFERENCE_PATTERN.finditer(content):
            label = match.group(1).lower()
            url = match.group(2).strip()
            references[label] = url
        return references

    def _classify_link(self, url: str) -> str:
        """Classify link type.

        Args:
            url: Link URL

        Returns:
            Link type: "external", "internal", "anchor", or "reference"
        """
        if url.startswith("http://") or url.startswith("https://"):
            return "external"
        elif url.startswith("#"):
            return "anchor"
        elif url.startswith("mailto:"):
            return "email"
        else:
            return "internal"

    def _validate_internal_link(self, url: str, file_path: Path) -> bool:
        """Validate internal file link.

        Args:
            url: Link URL
            file_path: Path to the markdown file containing the link

        Returns:
            True if link is valid, False otherwise
        """
        if self.base_path:
            base = self.base_path
        else:
            base = file_path.parent

        target_path = (base / url).resolve()

        if target_path.exists():
            return True

        if url.startswith("./") or url.startswith("../"):
            relative_path = file_path.parent / url
            if relative_path.resolve().exists():
                return True

        return False

    def _validate_anchor_link(self, url: str, headers: List[Tuple[int, str, str]]) -> bool:
        """Validate anchor link.

        Args:
            url: Anchor URL (without #)
            headers: List of headers in the document

        Returns:
            True if anchor exists, False otherwise
        """
        anchor = url.lstrip("#").lower()
        header_slugs = [slug for _, _, slug in headers]

        if anchor in header_slugs:
            return True

        if anchor == "":
            return True

        return False

    def _validate_external_link(self, url: str) -> bool:
        """Validate external HTTP/HTTPS link.

        Args:
            url: External URL

        Returns:
            True if link is accessible, False otherwise
        """
        if not REQUESTS_AVAILABLE:
            return None

        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except requests.RequestException:
            return False

    def _generate_toc(self, headers: List[Tuple[int, str, str]]) -> str:
        """Generate table of contents from headers.

        Args:
            headers: List of header tuples (level, text, slug)

        Returns:
            Markdown-formatted table of contents
        """
        if not headers:
            return ""

        toc_lines = ["## Table of Contents", ""]

        for level, text, slug in headers:
            if level < self.toc_min_depth or level > self.toc_max_depth:
                continue

            indent = "  " * (level - self.toc_min_depth)
            toc_lines.append(f"{indent}- [{text}](#{slug})")

        return "\n".join(toc_lines) + "\n"

    def _insert_toc(self, content: str, toc: str) -> str:
        """Insert table of contents into markdown content.

        Args:
            content: Original markdown content
            toc: Table of contents to insert

        Returns:
            Content with TOC inserted
        """
        if self.toc_placement == "none":
            return content

        if self.toc_placement == "top":
            return toc + "\n" + content

        if self.toc_placement == "after-first-header":
            first_header_match = self.HEADER_PATTERN.search(content)
            if first_header_match:
                insert_pos = first_header_match.end()
                return content[:insert_pos] + "\n\n" + toc + "\n" + content[insert_pos:]

        return content

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single markdown file.

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary with processing results

        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File does not exist: {file_path}")

        logger.info(f"Processing file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"Encoding error in {file_path}, trying latin-1")
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

        headers = self._extract_headers(content)
        links = self._extract_links(content)
        references = self._extract_references(content)

        self.stats["files_processed"] += 1
        self.stats["links_found"] += len(links)
        self.stats["references_found"] += len(references)

        broken_links = []
        broken_references = []

        for link_text, url, link_type in links:
            if link_type == "external":
                self.stats["external_links"] += 1
                if self.validate_external_links:
                    is_valid = self._validate_external_link(url)
                    if is_valid is False:
                        broken_links.append((link_text, url, "external"))
                        self.stats["broken_links"] += 1
            elif link_type == "internal":
                self.stats["internal_links"] += 1
                if not self._validate_internal_link(url, file_path):
                    broken_links.append((link_text, url, "internal"))
                    self.stats["broken_links"] += 1
            elif link_type == "anchor":
                if not self._validate_anchor_link(url, headers):
                    broken_links.append((link_text, url, "anchor"))
                    self.stats["broken_links"] += 1
            elif link_type == "reference":
                ref_label = url.lower()
                if ref_label not in references:
                    broken_references.append((link_text, url))
                    self.stats["broken_references"] += 1

        toc = ""
        if self.toc_placement != "none":
            toc = self._generate_toc(headers)
            if toc.strip():
                self.stats["toc_generated"] += 1

        result = {
            "file_path": str(file_path),
            "headers": headers,
            "links": links,
            "references": references,
            "broken_links": broken_links,
            "broken_references": broken_references,
            "toc": toc,
        }

        return result

    def process_files(
        self, file_paths: List[Path], update_files: bool = False
    ) -> List[Dict[str, Any]]:
        """Process multiple markdown files.

        Args:
            file_paths: List of file paths to process
            update_files: If True, update files with TOC and fixes

        Returns:
            List of processing results
        """
        results = []

        for file_path in file_paths:
            try:
                result = self.process_file(file_path)

                if update_files and result["toc"]:
                    self._update_file_with_toc(file_path, result["toc"])

                results.append(result)

            except (FileNotFoundError, IOError) as e:
                logger.error(f"Error processing {file_path}: {e}")
                self.stats["broken_links"] += 1

        return results

    def _update_file_with_toc(self, file_path: Path, toc: str) -> None:
        """Update file with table of contents.

        Args:
            file_path: Path to markdown file
            toc: Table of contents to insert
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if "## Table of Contents" in content:
                toc_pattern = re.compile(
                    r"## Table of Contents.*?(?=\n##|\Z)", re.DOTALL
                )
                content = toc_pattern.sub("", content).strip()

            updated_content = self._insert_toc(content, toc)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"Updated {file_path} with table of contents")

        except (IOError, OSError) as e:
            logger.error(f"Error updating file {file_path}: {e}")

    def format_report(self, results: List[Dict[str, Any]]) -> str:
        """Format processing results as a report.

        Args:
            results: List of processing results

        Returns:
            Formatted string report
        """
        lines = [
            "Markdown Processing Report",
            "=" * 80,
            "",
            f"Files processed: {self.stats['files_processed']}",
            f"Links found: {self.stats['links_found']}",
            f"  - External: {self.stats['external_links']}",
            f"  - Internal: {self.stats['internal_links']}",
            f"Broken links: {self.stats['broken_links']}",
            f"References found: {self.stats['references_found']}",
            f"Broken references: {self.stats['broken_references']}",
            f"TOC generated: {self.stats['toc_generated']}",
            "",
            "-" * 80,
            "",
        ]

        for result in results:
            lines.append(f"File: {result['file_path']}")
            lines.append(f"  Headers: {len(result['headers'])}")
            lines.append(f"  Links: {len(result['links'])}")
            lines.append(f"  References: {len(result['references'])}")

            if result["broken_links"]:
                lines.append("  Broken Links:")
                for link_text, url, link_type in result["broken_links"]:
                    lines.append(f"    - [{link_text}]({url}) ({link_type})")

            if result["broken_references"]:
                lines.append("  Broken References:")
                for link_text, url in result["broken_references"]:
                    lines.append(f"    - [{link_text}]: {url}")

            lines.append("")

        return "\n".join(lines)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dictionary containing configuration values

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config if config else {}
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise


def main() -> int:
    """Main entry point for the script.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Process markdown files: validate links and generate TOC"
    )
    parser.add_argument(
        "files",
        type=str,
        nargs="+",
        help="Markdown files to process",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path for resolving relative links",
    )
    parser.add_argument(
        "--validate-external",
        action="store_true",
        help="Validate external HTTP/HTTPS links",
    )
    parser.add_argument(
        "--toc-placement",
        type=str,
        choices=["top", "after-first-header", "none"],
        default="top",
        help="Where to place TOC (default: top)",
    )
    parser.add_argument(
        "--toc-min-depth",
        type=int,
        default=2,
        help="Minimum header depth for TOC (default: 2)",
    )
    parser.add_argument(
        "--toc-max-depth",
        type=int,
        default=6,
        help="Maximum header depth for TOC (default: 6)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update files with generated TOC",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path for report",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to configuration file (YAML)",
    )

    args = parser.parse_args()

    try:
        base_path = Path(args.base_path) if args.base_path else None
        validate_external = args.validate_external
        toc_placement = args.toc_placement
        toc_min_depth = args.toc_min_depth
        toc_max_depth = args.toc_max_depth
        update_files = args.update

        if args.config:
            config = load_config(Path(args.config))
            if "base_path" in config:
                base_path = Path(config["base_path"])
            if "validate_external_links" in config:
                validate_external = config["validate_external_links"]
            if "toc_placement" in config:
                toc_placement = config["toc_placement"]
            if "toc_min_depth" in config:
                toc_min_depth = config["toc_min_depth"]
            if "toc_max_depth" in config:
                toc_max_depth = config["toc_max_depth"]

        processor = MarkdownProcessor(
            base_path=base_path,
            validate_external_links=validate_external,
            toc_placement=toc_placement,
            toc_min_depth=toc_min_depth,
            toc_max_depth=toc_max_depth,
        )

        file_paths = [Path(f).expanduser().resolve() for f in args.files]
        results = processor.process_files(file_paths, update_files=update_files)

        report = processor.format_report(results)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")
        else:
            print(report)

        return 0

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
