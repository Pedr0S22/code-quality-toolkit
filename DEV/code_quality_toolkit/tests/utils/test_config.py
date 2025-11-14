import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from toolkit.core.errors import ConfigurationError  # noqa: E402
from toolkit.utils.config import (  # noqa: E402
    ToolkitConfig,
    load_config,
)


def test_load_config_no_path_returns_defaults():
    """Test that calling load_config(None) returns the default config."""
    config = load_config(path=None)

    assert isinstance(config, ToolkitConfig)
    # Check a value from each default dataclass
    assert config.strict is False
    assert config.enabled_plugins == ["StyleChecker", "CyclomaticComplexity"]
    assert config.rules.max_complexity == 10
    assert config.analyze.include == ["**/*.py"]


def test_load_config_non_existent_file_raises_error():
    """Test that loading a file that doesn't exist raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        load_config("non_existent_file.toml")


def test_load_config_empty_file_returns_defaults(tmp_path: Path):
    """Test that loading an empty TOML file results in default config."""
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text("")

    config = load_config(config_file)

    # Should be identical to the no-path test
    assert isinstance(config, ToolkitConfig)
    assert config.strict is False
    assert config.enabled_plugins == ["StyleChecker", "CyclomaticComplexity"]
    assert config.rules.max_complexity == 10
    assert config.analyze.include == ["**/*.py"]


def test_load_config_full_override(tmp_path: Path):
    """Test that all settings can be overridden by a TOML file."""
    toml_content = """
    strict = true

    [plugins]
    enabled = ["MyNewPlugin", "AnotherPlugin"]

    [rules]
    max_line_length = 100
    max_complexity = 20
    max_function_length = 75
    max_arguments = 3

    [analyze]
    include = ["src/**/*.py"]
    exclude = ["*.md", "docs/**"]
    """
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content)

    config = load_config(config_file)

    # Test that all values were correctly overridden
    assert config.strict is True
    assert config.enabled_plugins == ["MyNewPlugin", "AnotherPlugin"]
    assert config.rules.max_line_length == 100
    assert config.rules.max_complexity == 20
    assert config.analyze.include == ["src/**/*.py"]
    assert config.analyze.exclude == ["*.md", "docs/**"]


def test_load_config_partial_override(tmp_path: Path):
    """Test that settings not in the TOML file remain at their defaults."""
    toml_content = """
    [rules]
    max_line_length = 120 # Override one rule

    [analyze]
    exclude = ["tests/**"] # Override one analyze setting
    """
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content)

    config = load_config(config_file)

    # Test that defaults are kept for non-specified keys
    assert config.strict is False  # Default
    assert config.enabled_plugins == ["StyleChecker", "CyclomaticComplexity"]  # Default

    # Test mixed rules (one override, one default)
    assert config.rules.max_line_length == 120  # Overridden
    assert config.rules.max_complexity == 10  # Default

    # Test mixed analyze (one override, one default)
    assert config.analyze.include == ["**/*.py"]  # Default
    assert config.analyze.exclude == ["tests/**"]  # Overridden


def test_load_config_invalid_rule_type_raises_error(tmp_path: Path):
    """Test that a rule with an invalid type (e.g., string for int) raises."""
    toml_content = """
    [rules]
    max_line_length = "eighty-eight" # Invalid type (string)
    """
    config_file = tmp_path / "pyproject.toml"
    config_file.write_text(toml_content)

    # The dynamic loader should catch this type conversion error
    with pytest.raises(ConfigurationError, match="Invalid type"):
        load_config(config_file)
