"""Configuration loading utilities for the toolkit."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import get_type_hints

from ..core.errors import ConfigurationError

# This block of code implements a version check for TOML parsing capability
# (introduced in Python 3.11 as part of the standard library)
# → try to use the modern, built-in tomllib. If that fails
# (because the Python version is too old), stop the program immediately and tell
# the user they need to upgrade to Python 3.11+."
try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover - Python <3.11 fallback
    raise ConfigurationError("tomllib not available; requires Python 3.11+") from exc


# @dataclass is a decorator that automatically generates special methods for the
# class, such as:
#    __init__ (constructor)
#    __repr__ (string representation)
#    __eq__ (equality comparison)
#
# This reduces the need for boilerplate code, making AnalyzeConfig a simpler,
# efficient container for data.
# 'slots=True' is an optimization setting for data classes. It tells Python to
# use a __slots__ attribute instead of a standard __dict__ to store instance
# attributes, which makes instances of AnalyzeConfig take up less memory.
@dataclass(slots=True)
class AnalyzeConfig:
    # Defines the attribute name (include) and its type hint (a list of strings);
    # these strings specify files to be included in the analysis.
    # field(..): is used to specify per-field metadata, particularly for
    # providing mutable default values.
    # default_factory=lambda: provides a no-argument function (here, a lambda)
    # that is called to create a new default value every time a new 'AnalyzeConfig'
    # object is created without specifying an include value.
    # ["**/*.py"] is a common glob pattern that means: "recursively include all
    # files ending with .py."
    include: list[str] = field(default_factory=lambda: ["**/*.py"])

    # Similarly defines the list of glob patterns for files/directories to be
    # *excluded* from the analysis.
    # default_factory=lambda: ["venv/**"]: Again, this ensures each instance
    # gets its own list.
    # "venv/**" means: recursively exclude everything inside any directory named
    # venv (the virtual environments.
    exclude: list[str] = field(default_factory=lambda: ["venv/**"])

    # Whit the statements abovos, when the analysis tool initializes, it can create
    # a configuration object simply by calling:  "config = AnalyzeConfig()""
    # config.include will be ['**/*.py']
    # config.exclude will be ['venv/**']


@dataclass(slots=True)
class RulesConfig:
    # This class acts as the reference source for the code quality toolkit's
    # default rules. These values can then be overridden if a configuration file
    # specifies different limits.
    max_line_length: int = 88
    max_complexity: int = (
        10  # This is a widely accepted threshold. Functions with a complexity
    )
    # higher than this are generally considered difficult to read, test,
    # and maintain.
    check_whitespace: bool = True
    indent_style = "spaces" 
    indent_size = 4
    allow_mixed_indentation = False
    check_naming = False    max_function_length: int = (
        50  # New rule: maximum number of lines allowed in a function
    )
    max_arguments: int = (
        5  # New rule: maximum number of arguments allowed in a function
    )


# -------------ToolkitConfig -----------------------
@dataclass(slots=True)
class ToolkitConfig:
    # This field defines which specific code analysis plugins the toolkit should
    # load and run.
    # "StyleChecker" and "CyclomaticComplexity" are predefined defaults.
    # 'default_factory' ensures that every new ToolkitConfig instance gets its
    # own independent list object.
    strict: bool = False

    enabled_plugins: list[str] = field(
        default_factory=lambda: ["StyleChecker", "CyclomaticComplexity"]
    )

    # 'rules' the numerical thresholds and specific parameters for the code
    # quality checks (e.g., maximum line length, maximum complexity score).
    # 'default_factory=RulesConfig' ensures that the default RulesConfig object
    # is instantiated only when a new ToolkitConfig object is created, thus
    # maintaining encapsulation.
    rules: RulesConfig = field(default_factory=RulesConfig)

    # This field controls the scope of the analysis,
    # specifying which files and directories to include or exclude during the scan.
    analyze: AnalyzeConfig = field(default_factory=AnalyzeConfig)

    # therefore, 'ToolkitConfig' provides a structured way to manage
    # the application's entire configuration, with clear separation between
    # different concerns (plugins, rules, and analysis scope).


# ------------------------------------

# EXTENSION-POINT HERE: adicionar campos de configuração específicos de plugins aqui.


def load_config(path: str | Path | None) -> ToolkitConfig:
    """Load configuration from a TOML file or return defaults.

    Its primary goal is to merge default settings with user-defined settings
    from a TOML file.
    It ensures that the final configuration object is always valid by starting
    with defaults and then applying overrides from the file.
    """
    config = (
        ToolkitConfig()
    )  # creates a configuration object populated with all the default values.
    # If the user didn't specify a configuration file, the function
    if path is None:
        return config  # immediately returns the default config object.

    # == File Validation and Loading ==
    config_path = Path(path)  # 'path' is converted to a 'pathlib.Path' object for easy
    # file system interaction.
    if not config_path.exists():  # a mandatory check
        raise ConfigurationError(f"Configuration file not found: {config_path}")

    # == TOML configuration file loading ==
    # file is opened in binary read mode ("rb"), as required by the tomllib module.
    with config_path.open("rb") as handle:
        data = tomllib.load(
            handle
        )  # parses the contents of the TOML file into a dictionary (data).

    # == Applying Overrides from TOML Data ==

    # Load top-level settings (e.g., strict mode)
    strict_value = data.get("strict", config.strict)
    if isinstance(strict_value, bool):
        config.strict = strict_value

    # === Plugins sections ===
    plugins = data.get(
        "plugins", {}
    )  # retrieves the [plugins] section, defaulting to an empty
    # dictionary if not found.
    enabled = plugins.get(
        "enabled"
    )  # checks for the 'enabled' key within that section.
    if (
        isinstance(enabled, list) and enabled
    ):  # checks whether enabled is a non-empty list before proceeding
        config.enabled_plugins = [
            str(item) for item in enabled
        ]  # overwrites the default config.enabled_plugins list
        # with the new values,
        # ensuring all list items are converted to strings.

    # === Rules Section ===
    rules_data = data.get("rules", {})  # ensures this section is a dictionary
    # attempts to get the value from the file. If the key is not present,
    # it uses the existing default value (config.rules.max_line_length)
    # as the fallback, guaranteeing that only explicitly set values are changed.
    # The values are explicitly converted to int() to ensure type correctness
    if isinstance(rules_data, dict):
        # Dynamically loop over all fields defined in the RulesConfig class
        type_hints = get_type_hints(config.rules)

        # Loop over the resolved {field_name: type} pairs
        for field_name, expected_type in type_hints.items():
            if field_name in rules_data:
                try:
                    new_value = rules_data[field_name]
                    # Now expected_type is a class (int) and can be called
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
        # Overrides only the specific sub-fields (include and exclude) that are
        # present and valid in the TOML data.
        if isinstance(include, list) and include:
            config.analyze.include = [str(item) for item in include]
        if isinstance(exclude, list) and exclude:
            config.analyze.exclude = [str(item) for item in exclude]

    # the final 'config' object is now a combination of the original safe defaults
    # and any valid overrides found in the (optional) command-line specified
    # TOML file.
    return config


# TODO(alunos): adicionar validação de tipos avançada e suporte a múltiplos
# ambientes.
