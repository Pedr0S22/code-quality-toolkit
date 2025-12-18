# Linter Wrapper Plugin – Technical Documentation
## Plugin Name
linter_wrapper

## Version
0.1.0

## Authors
Alfonso Pintado Gracia            2025175710        @alfooonsoo17
Carlos Lomelín Valdés             2025154763        @carloslomelinv
Miguel Pedro Rodrigues Carvalho   2023216436        @parzival3301
Samuel Gomes Esteban              2025178876        @samuugomes
Mathias Gustavo Welz              2025167903        @mathiasgwelz

## ---USER GUIDE---
## What This Plugin Does
The LintWrapper plugin runs pylint (and later other linters) as external tools and integrates their findings into the Toolkit’s unified issue reporting system.
It enables users to:
- Reuse mature and well-tested linting rules without reimplementing them
- Detect errors, bad practices, and style violations
- Combine pylint results with other plugins into a single report
- Avoid crashes thanks to robust error handling (timeouts, missing tools, etc.)

## How to Enable the Plugin
To configure it, edit the rules described below in your toolkit.toml configuration file. The plugin reads its settings from the [`plugins.linter_wrapper`] section (**note**: this is not under [`rules`]):

```toml
[plugins.linter_wrapper]
enabled = true
linters = ["pylint"]
timeout_seconds = 60
max_issues = 500
pylint_args = ["--disable=C0114,C0115,C0116",
]
fail_on_severity = "high"
```

Configuration Meaning
- enabled – toggles the plugin on/off
- linters – which external linters to run (currently only "pylint")
- timeout_seconds – maximum allowed runtime
- max_issues – cap on how many issues the plugin will return
- pylint_args – additional flags to pass to pylint
- fail_on_severity - severity threshold that can cause CI to fail

## How to Use It
1. Ensure pylint is installed (pip install pylint).
2. Run the Toolkit’s CLI analysis command.
3. LintWrapper will automatically run pylint on the provided source files.
4. All lint issues appear in the final report.json.

## Example Issues You May See
- pylint:E1101: accessing an attribute that does not exist
- pylint:W0611: unused import
- pylint:C0114: missing module docstring
- pylint:R0912: too many branches
- LINTER_NOT_FOUND: pylint is not installed or not in PATH
- LINTER_TIMEOUT: pylint exceeded the configured timeout
- LINTER_ERROR: pylint failed and produced no valid output
- LINTER_OUTPUT_INVALID: pylint returned malformed or non-JSON output

Each issue includes:
- severity
- line and column
- message
- hint

## How to Fix Common Problems
- Install pylint if it is missing from PATH
- Add required docstrings (C0114/C0115/C0116)
- Remove unused imports (W0611)
- Reduce function/method complexity (R0912, R0915)
- Follow Python naming and style conventions

## Summary
The LintWrapper plugin makes it easy to integrate pylint into the Toolkit, providing consistent reporting, predictable severities, and safe fallback behavior when the linter fails. It is a key component for centralized code quality analysis.
