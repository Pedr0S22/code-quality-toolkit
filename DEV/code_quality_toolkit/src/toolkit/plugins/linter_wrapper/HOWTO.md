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

## ---TECHNICAL DOCUMENTATION---
## Description
The LintWrapper plugin acts as an adaptor between the Toolkit and external linters such as pylint.
It:
- Builds and executes the linting command
- Parses its JSON output
- Converts messages into normalized Toolkit Issue objects
- Maps pylint severities to Toolkit severities
- Handles unexpected errors (timeouts, missing binary, abnormal exit codes)
The design is modular to support future linters (flake8, bandit, etc.).

## 1. Purpose
The LintWrapper plugin provides a unified and robust way to run external linters and integrate their results with other Toolkit plugins. It avoids duplicated rule implementations and leverages mature linting ecosystems.

## 2. How It Works
The plugin performs several checks:

1. Splits the source code into lines.
2. Checks if any line exceeds the configured maximum length.
3. Detects trailing whitespace (spaces or tabs at the end of a line).
4. Validates indentation:
   - Only spaces or only tabs (depending on configuration)
   - No mixing of tabs and spaces
   - Indentation width must match indent_size
5. Checks if the filename follows snake_case.py.
6. Checks naming conventions for classes (CamelCase) and functions (snake_case).
7. Returns all issues found together with a summary.

## 3. Main Class: `Plugin`

## Attributes
- enabled: whether the plugin is active
- enabled_linters: list of external linters to execute
- timeout_seconds: maximum allowed runtime for each linter
- max_issues: maximum number of issues to return
- pylint_args: extra command-line arguments passed to pylint
- fail_on_severity: severity threshold used to decide if the build should fail

## Important Methods
- configure(config): loads plugin settings from the toolkit configuration
- get_metadata(): returns plugin name, version and description
- analyze(source_code, file_path): runs the configured linters on a file and returns results
- _run_linters_on_file(file_path): executes all enabled linters and aggregates their issues
- _run_pylint(file_path): runs pylint via subprocess and parses its JSON output
- _should_fail_build(highest_severity): determines whether the analysis should fail based on severity

## 4. Output Format
Example successful result:
```{
  "results": [...],
  "summary": {
    "issues_found": 12,
    "status": "completed"
  }
}```

## 5. Example Issue Codes
From pylint:
- pylint:E1101 — attribute not found
- pylint:W0611 — unused import
- pylint:C0114 — missing module docstring
- pylint:R0915 — too many statements
From the plugin:
- LINTER_NOT_FOUND
- LINTER_TIMEOUT
- LINTER_ERROR

## 6. Conclusion
The LintWrapper plugin is a robust and extensible solution for integrating external linters into the Toolkit.
Its unified output format, strong error handling, and future extensibility make it an essential quality assurance component.