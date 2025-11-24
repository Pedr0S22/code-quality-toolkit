"""Pytest configuration and fixtures for integration tests."""

import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_pythonpath():
    """Add toolkit src to Python path for integration tests."""
    toolkit_src = Path(__file__).resolve().parent.parent.parent / "src"
    if str(toolkit_src) not in sys.path:
        sys.path.insert(0, str(toolkit_src))


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a sample Python file for testing."""
    file = tmp_path / "sample.py"
    file.write_text(
        '"""Sample module."""\n'
        "\n"
        "def add(a: int, b: int) -> int:\n"
        '    """Add two numbers."""\n'
        "    return a + b\n",
        encoding="utf-8",
    )
    return file


@pytest.fixture
def messy_python_file(tmp_path: Path) -> Path:
    """Create a Python file with style issues."""
    file = tmp_path / "messy.py"
    file.write_text(
        "x=1\ny=2\ndef  foo( a,b ):\n"
        "    return a+b\n"
        "# Long line " + "x" * 100 + "\n",
        encoding="utf-8",
    )
    return file


@pytest.fixture
def duplicated_code_file(tmp_path: Path) -> Path:
    """Create a Python file with duplicated code."""
    file = tmp_path / "duplicated.py"
    file.write_text(
        "def process_a():\n"
        "    x = 1\n"
        "    y = 2\n"
        "    z = x + y\n"
        "    return z\n"
        "\n"
        "def process_b():\n"
        "    x = 1\n"
        "    y = 2\n"
        "    z = x + y\n"
        "    return z\n",
        encoding="utf-8",
    )
    return file


@pytest.fixture
def project_with_issues(tmp_path: Path) -> Path:
    """Create a project directory with files containing various issues."""
    (tmp_path / "clean.py").write_text(
        '"""Clean module."""\n'
        "\n"
        "def hello() -> None:\n"
        '    """Say hello."""\n'
        "    print('hello')\n",
        encoding="utf-8",
    )

    (tmp_path / "messy.py").write_text(
        "x=1\ny=2\ndef  foo( a,b ):\n"
        "    return a+b\n",
        encoding="utf-8",
    )

    (tmp_path / "duplicated.py").write_text(
        "def process_a():\n"
        "    x = 1\n"
        "    y = 2\n"
        "    z = x + y\n"
        "    return z\n"
        "\n"
        "def process_b():\n"
        "    x = 1\n"
        "    y = 2\n"
        "    z = x + y\n"
        "    return z\n",
        encoding="utf-8",
    )

    return tmp_path
