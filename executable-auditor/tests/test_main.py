"""Unit tests for Executable File Auditor."""

import os
import shutil
import stat
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.main import ExecutableAuditor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config():
    """Create a sample configuration."""
    return {
        "detection": {
            "check_permissions": True,
            "check_extensions": True,
            "check_magic_bytes": True,
            "check_shebang": True,
        },
        "categories": {
            "scripts": {
                "extensions": ["sh", "py"],
                "description": "Script files",
                "check_shebang": True,
            },
            "binaries": {
                "extensions": ["exe", "bin"],
                "description": "Binary executables",
            },
        },
        "security_audit": {
            "calculate_hashes": True,
            "hash_algorithm": "sha256",
            "flag_suspicious_permissions": True,
            "suspicious_permissions": ["777", "666"],
            "check_file_size": True,
            "max_normal_size": 104857600,
            "flag_recent_modifications": True,
            "recent_days": 7,
        },
        "exclude_patterns": [],
        "exclude_directories": [],
    }


def test_executable_auditor_initialization(sample_config):
    """Test ExecutableAuditor initialization."""
    auditor = ExecutableAuditor(sample_config)

    assert "sh" in auditor.extension_to_category
    assert auditor.extension_to_category["sh"] == "scripts"


def test_is_executable_by_permission(sample_config, temp_dir):
    """Test checking executable by permission."""
    test_file = temp_dir / "test.sh"
    test_file.write_text("#!/bin/bash")

    # Make executable
    os.chmod(test_file, 0o755)

    auditor = ExecutableAuditor(sample_config)
    is_exec = auditor.is_executable_by_permission(test_file)

    assert is_exec is True


def test_is_executable_by_permission_not_executable(sample_config, temp_dir):
    """Test checking non-executable file."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")

    # Make non-executable
    os.chmod(test_file, 0o644)

    auditor = ExecutableAuditor(sample_config)
    is_exec = auditor.is_executable_by_permission(test_file)

    assert is_exec is False


def test_is_executable_by_extension(sample_config, temp_dir):
    """Test checking executable by extension."""
    test_file = temp_dir / "script.sh"

    auditor = ExecutableAuditor(sample_config)
    is_exec = auditor.is_executable_by_extension(test_file)

    assert is_exec is True


def test_has_shebang(sample_config, temp_dir):
    """Test checking for shebang."""
    test_file = temp_dir / "script.sh"
    test_file.write_text("#!/bin/bash\necho test")

    auditor = ExecutableAuditor(sample_config)
    has_shebang = auditor.has_shebang(test_file)

    assert has_shebang is True


def test_has_shebang_no_shebang(sample_config, temp_dir):
    """Test file without shebang."""
    test_file = temp_dir / "script.txt"
    test_file.write_text("no shebang here")

    auditor = ExecutableAuditor(sample_config)
    has_shebang = auditor.has_shebang(test_file)

    assert has_shebang is False


def test_is_binary_file(sample_config, temp_dir):
    """Test checking if file is binary."""
    test_file = temp_dir / "binary.bin"
    test_file.write_bytes(b"\x7fELF\x00\x01\x01\x00")

    auditor = ExecutableAuditor(sample_config)
    is_binary = auditor.is_binary_file(test_file)

    assert is_binary is True


def test_is_binary_file_text(sample_config, temp_dir):
    """Test checking text file."""
    test_file = temp_dir / "text.txt"
    test_file.write_text("This is text content")

    auditor = ExecutableAuditor(sample_config)
    is_binary = auditor.is_binary_file(test_file)

    assert is_binary is False


def test_get_file_category_by_extension(sample_config, temp_dir):
    """Test getting category by extension."""
    test_file = temp_dir / "script.sh"

    auditor = ExecutableAuditor(sample_config)
    category = auditor.get_file_category(test_file)

    assert category == "scripts"


def test_get_file_category_by_shebang(sample_config, temp_dir):
    """Test getting category by shebang."""
    test_file = temp_dir / "script"
    test_file.write_text("#!/usr/bin/python3\nprint('test')")

    auditor = ExecutableAuditor(sample_config)
    category = auditor.get_file_category(test_file)

    assert category == "scripts"


def test_calculate_file_hash(sample_config, temp_dir):
    """Test calculating file hash."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    auditor = ExecutableAuditor(sample_config)
    file_hash = auditor.calculate_file_hash(test_file)

    assert file_hash is not None
    assert len(file_hash) == 64  # SHA256 hash length


def test_get_file_permissions(sample_config, temp_dir):
    """Test getting file permissions."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    os.chmod(test_file, 0o755)

    auditor = ExecutableAuditor(sample_config)
    octal_perms, perm_str = auditor.get_file_permissions(test_file)

    assert isinstance(octal_perms, int)
    assert isinstance(perm_str, str)


def test_check_security_flags_suspicious_permissions(sample_config, temp_dir):
    """Test security flag for suspicious permissions."""
    test_file = temp_dir / "test.sh"
    test_file.write_text("#!/bin/bash")
    os.chmod(test_file, 0o777)

    file_info = {"size": 100, "modified_time": datetime.now().isoformat()}

    auditor = ExecutableAuditor(sample_config)
    flags = auditor.check_security_flags(test_file, file_info)

    assert len(flags) > 0
    assert any("Suspicious permissions" in flag for flag in flags)


def test_check_security_flags_large_file(sample_config, temp_dir):
    """Test security flag for large file."""
    test_file = temp_dir / "large.bin"
    # Create a file larger than max_normal_size
    test_file.write_bytes(b"x" * 150000000)  # 150MB

    file_info = {"size": 150000000, "modified_time": datetime.now().isoformat()}

    auditor = ExecutableAuditor(sample_config)
    flags = auditor.check_security_flags(test_file, file_info)

    assert len(flags) > 0
    assert any("Unusually large" in flag for flag in flags)


def test_check_security_flags_recent_modification(sample_config, temp_dir):
    """Test security flag for recently modified file."""
    test_file = temp_dir / "test.sh"
    test_file.write_text("#!/bin/bash")

    # Set modification time to 2 days ago
    mod_time = (datetime.now() - timedelta(days=2)).timestamp()
    os.utime(test_file, (mod_time, mod_time))

    file_info = {
        "size": 100,
        "modified_time": datetime.fromtimestamp(mod_time).isoformat(),
    }

    auditor = ExecutableAuditor(sample_config)
    flags = auditor.check_security_flags(test_file, file_info)

    assert len(flags) > 0
    assert any("Recently modified" in flag for flag in flags)


def test_find_executables(sample_config, temp_dir):
    """Test finding executables in directory."""
    # Create executable file
    exec_file = temp_dir / "script.sh"
    exec_file.write_text("#!/bin/bash")
    os.chmod(exec_file, 0o755)

    # Create non-executable file
    normal_file = temp_dir / "normal.txt"
    normal_file.write_text("not executable")

    auditor = ExecutableAuditor(sample_config)
    executables = auditor.find_executables([temp_dir], recursive=False)

    assert len(executables) > 0
    assert "scripts" in executables
    assert len(executables["scripts"]) == 1


def test_find_executables_recursive(sample_config, temp_dir):
    """Test finding executables recursively."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()

    exec_file1 = temp_dir / "script1.sh"
    exec_file1.write_text("#!/bin/bash")
    os.chmod(exec_file1, 0o755)

    exec_file2 = subdir / "script2.sh"
    exec_file2.write_text("#!/bin/bash")
    os.chmod(exec_file2, 0o755)

    auditor = ExecutableAuditor(sample_config)
    executables = auditor.find_executables([temp_dir], recursive=True)

    assert len(executables["scripts"]) == 2


def test_should_exclude_file(sample_config, temp_dir):
    """Test file exclusion."""
    sample_config["exclude_patterns"] = ["\\.tmp$"]

    auditor = ExecutableAuditor(sample_config)

    assert auditor.should_exclude_file(temp_dir / "file.tmp") is True
    assert auditor.should_exclude_file(temp_dir / "file.sh") is False


def test_should_exclude_directory(sample_config, temp_dir):
    """Test directory exclusion."""
    sample_config["exclude_directories"] = ["^\\.git$"]

    auditor = ExecutableAuditor(sample_config)

    assert auditor.should_exclude_directory(temp_dir / ".git") is True
    assert auditor.should_exclude_directory(temp_dir / "normal_dir") is False


def test_generate_json_report(sample_config, temp_dir):
    """Test generating JSON report."""
    exec_file = temp_dir / "script.sh"
    exec_file.write_text("#!/bin/bash")
    os.chmod(exec_file, 0o755)

    auditor = ExecutableAuditor(sample_config)
    executables = auditor.find_executables([temp_dir], recursive=False)

    report_path = temp_dir / "report.json"
    auditor.generate_report(executables, report_path, "json")

    assert report_path.exists()

    import json
    with open(report_path, "r") as f:
        report = json.load(f)

    assert "total_executables" in report
    assert "categories" in report


def test_generate_txt_report(sample_config, temp_dir):
    """Test generating text report."""
    exec_file = temp_dir / "script.sh"
    exec_file.write_text("#!/bin/bash")
    os.chmod(exec_file, 0o755)

    auditor = ExecutableAuditor(sample_config)
    executables = auditor.find_executables([temp_dir], recursive=False)

    report_path = temp_dir / "report.txt"
    auditor.generate_report(executables, report_path, "txt")

    assert report_path.exists()

    content = report_path.read_text()
    assert "EXECUTABLE FILE SECURITY AUDIT REPORT" in content
    assert "script.sh" in content


def test_generate_csv_report(sample_config, temp_dir):
    """Test generating CSV report."""
    exec_file = temp_dir / "script.sh"
    exec_file.write_text("#!/bin/bash")
    os.chmod(exec_file, 0o755)

    auditor = ExecutableAuditor(sample_config)
    executables = auditor.find_executables([temp_dir], recursive=False)

    report_path = temp_dir / "report.csv"
    auditor.generate_report(executables, report_path, "csv")

    assert report_path.exists()

    import csv
    with open(report_path, "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) > 1  # Header + data rows
    assert "Category" in rows[0]
