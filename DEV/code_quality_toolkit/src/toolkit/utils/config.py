"""Configuration loading utilities for the toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, get_type_hints

from ..core.errors import ConfigurationError


class SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        return str(self.__dict__)


# This block of code implements a version check for TOML parsing capability
try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover - Python <3.11 fallback
    raise ConfigurationError("tomllib not available; requires Python 3.11+") from exc


@dataclass(slots=True)
class AnalyzeConfig:
    include: list[str] = field(default_factory=lambda: ["**/*.py"])
    exclude: list[str] = field(default_factory=lambda: ["venv/**"])


@dataclass(slots=True)
class LinterWrapperConfig:
    enabled: bool = True
    linters: list[str] = field(default_factory=lambda: ["pylint"])
    timeout_seconds: int = 60
    max_issues: int = 500
    pylint_args: list[str] = field(default_factory=list)
    # "none", "low", "medium", "high"
    fail_on_severity: str = "high"


@dataclass(slots=True)
class PluginsConfig:
    """Container for plugin-specific configurations."""

    # We use Any/dict to allow dynamic loading of plugin settings
    dead_code_detector: Any = field(
        default_factory=lambda: SimpleNamespace(
            **{
                "ignore_patterns": ["^__", "^test_"],
                "min_name_length": 2,
                "severity": "low",
            }
        )
    )

    cyclomatic_complexity: Any = field(
        default_factory=lambda: SimpleNamespace(
            **{
                "max_complexity": 10,
                "max_function_length": 50,
                "max_arguments": 5,
            }
        )
    )

    # NEW: Specific implementation for LinterWrapper matching dead_code style
    linter_wrapper: LinterWrapperConfig = field(
        default_factory=lambda: LinterWrapperConfig(
            enabled=True,
            linters=["pylint"],
            timeout_seconds=60,
            max_issues=500,
            pylint_args=[],
            fail_on_severity="high",
        )
    )


@dataclass(slots=True)
class RulesConfig:
    # This class acts as the reference source for the code quality toolkit's
    # default rules.
    check_naming: bool = False

    max_line_length: int = 88
    max_complexity: int = 10
    check_whitespace: bool = True
    indent_style: str = "spaces"
    indent_size: int = 4
    allow_mixed_indentation: bool = False

    security_report_level="LOW"

    max_function_length: int = 50
    max_arguments: int = 5

    # FIX: Renamed from min_comment_density to min_density to match existing tests
    min_density: float = 0.1
    max_density: float = 0.5

    # FIX: Restored missing attributes required by DependencyGraph tests
    warn_wildcard_imports: bool = True
    max_relative_import_level: int = 1
    track_stdlib_modules: bool = True


# -------------ToolkitConfig -----------------------
@dataclass(slots=True)
class ToolkitConfig:
    strict: bool = False

    enabled_plugins: list[str] = field(
        default_factory=lambda: ["StyleChecker", "CyclomaticComplexity"]
    )

    rules: RulesConfig = field(default_factory=RulesConfig)

    analyze: AnalyzeConfig = field(default_factory=AnalyzeConfig)

    # 'plugins' now holds the LinterWrapper config inside it
    plugins: PluginsConfig = field(default_factory=PluginsConfig)


# ------------------------------------


def _apply_linter_wrapper_config(
    config: ToolkitConfig,
    plugins_section: dict[str, Any],
) -> None:
    """Apply [plugins.linter_wrapper] configuration to ToolkitConfig."""
    linter_data = plugins_section.get("linter_wrapper")
    if not isinstance(linter_data, dict):
        return

    # Update: Target the config inside 'plugins'
    target_config = config.plugins.linter_wrapper

    # enabled
    if "enabled" in linter_data:
        value = linter_data["enabled"]
        if not isinstance(value, bool):
            raise ConfigurationError(
                "Invalid type for '[plugins.linter_wrapper].enabled'. Expected bool."
            )
        target_config.enabled = value

    # linters
    linters = linter_data.get("linters")
    if isinstance(linters, list) and linters:
        target_config.linters = [str(item) for item in linters]

    # timeout_seconds
    if "timeout_seconds" in linter_data:
        try:
            target_config.timeout_seconds = int(linter_data["timeout_seconds"])
        except (ValueError, TypeError) as ex:
            raise ConfigurationError(
                "Invalid type for '[plugins.linter_wrapper].timeout_seconds'. "
                "Expected int."
            ) from ex

    # max_issues
    if "max_issues" in linter_data:
        try:
            target_config.max_issues = int(linter_data["max_issues"])
        except (ValueError, TypeError) as ex:
            raise ConfigurationError(
                "Invalid type for '[plugins.linter_wrapper].max_issues'. "
                "Expected int."
            ) from ex

    # pylint_args
    pylint_args = linter_data.get("pylint_args")
    if isinstance(pylint_args, list):
        target_config.pylint_args = [str(item) for item in pylint_args]

    # fail_on_severity
    if "fail_on_severity" in linter_data:
        value = str(linter_data["fail_on_severity"])
        allowed = {"none", "low", "medium", "high"}
        if value not in allowed:
            raise ConfigurationError(
                "Invalid value for '[plugins.linter_wrapper].fail_on_severity'. "
                f"Expected one of {sorted(allowed)}, got '{value}'."
            )
        target_config.fail_on_severity = value


def load_config(path: str | Path | None) -> ToolkitConfig:
    """Load configuration from a TOML file or return defaults."""
    config = ToolkitConfig()

    if path is None:
        return config

    config_path = Path(path)
    if not config_path.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)

    # == Applying Overrides from TOML Data ==

    # Load top-level settings
    strict_value = data.get("strict", config.strict)
    if isinstance(strict_value, bool):
        config.strict = strict_value

    # === Plugins sections ===

    plugins_configs(data, config)

    # === Rules Section ===
    rules_data = data.get("rules", {})
    if isinstance(rules_data, dict):
        type_hints = get_type_hints(config.rules)

        for field_name, expected_type in type_hints.items():
            if field_name in rules_data:
                try:
                    new_value = rules_data[field_name]
                    setattr(config.rules, field_name, expected_type(new_value))
                except (ValueError, TypeError) as ex:
                    raise ConfigurationError(
                        f"Invalid type for '[rules].{field_name}'. "
                        f"Expected {expected_type.__name__} but got '{new_value}'."
                    ) from ex

    # === Analyze Section ===
    analyze = data.get("analyze", {})
    if isinstance(analyze, dict):
        include = analyze.get("include")
        exclude = analyze.get("exclude")
        if isinstance(include, list) and include:
            config.analyze.include = [str(item) for item in include]
        if isinstance(exclude, list) and exclude:
            config.analyze.exclude = [str(item) for item in exclude]

    return config

def plugins_configs(data, config):
    plugins = data.get("plugins", {})

    enabled = plugins.get("enabled")
    if isinstance(enabled, list) and enabled:
        config.enabled_plugins = [str(item) for item in enabled]

    if isinstance(plugins, dict):
        # 1. Apply specific LinterWrapper logic (existing)
        _apply_linter_wrapper_config(config, plugins)

        for key, section_data in plugins.items():
            if key in ["enabled", "linter_wrapper"]:
                continue # Handled separately

            # Check if PluginsConfig has this field (e.g. cyclomatic_complexity)
            if hasattr(config.plugins, key) and isinstance(section_data, dict):
                target_obj = getattr(config.plugins, key)
                
                # Update the SimpleNamespace with values from TOML
                if hasattr(target_obj, "__dict__"):
                    target_obj.__dict__.update(section_data)
