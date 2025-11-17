# Code Quality Toolkit: Plugin Development Guide

Welcome, developer\! This guide details the technical contract and "best practices" for creating a new plugin for the Code Quality Toolkit.

The core design of this toolkit is **resilience**. The main application is designed to handle plugin failures gracefully. To achieve this, every plugin **must** adhere to the data contract defined below.

> **The "Golden Rule" of Plugin Resilience**
>
> A bug in one plugin **must not** crash the entire analysis run. Your plugin is responsible for catching its own internal errors (`Exception`) and reporting a "failed" status to the main tool, rather than letting an exception propagate upwards.

## The Plugin "Contract"

A valid plugin is a Python file that contains a class named `Plugin`. This class must implement the following methods.

-----

## 1\. `get_metadata()`

This method returns a simple dictionary describing your plugin. The main tool uses this to display information about which plugins were run.

  * **Returns:** `dict[str, str]`

#### Example:

```python
def get_metadata(self) -> dict[str, str]:
    return {
        "name": "MyNewPlugin",
        "version": "1.0.0",
        "description": "Checks for my specific project rules.",
    }
```

-----

## 2\. `configure()`

This method is called by the main engine after loading the configuration. It passes the global `ToolkitConfig` object so your plugin can read its own settings (e.g., from the `[tool.cqt.rules]` section of a `toolkit.toml` file).

  * **Arguments:** `config: ToolkitConfig`
  * **Returns:** `None`

#### Example:

```python
from ...utils.config import ToolkitConfig

class Plugin:
    def __init__(self) -> None:
        # Set sane defaults
        self.my_rule_threshold = 10

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin thresholds from global config."""
        
        # Overwrite defaults with values from the config file
        if config.rules.get("my_rule_threshold"):
            self.my_rule_threshold = config.rules.my_rule_threshold
```

-----

## 3\. `analyze()`

This is the main entry point for your plugin's logic. It receives the source code of a single file and must return a dictionary detailing the results.

This method **must** have its own `try...except` block to enforce the "Golden Rule."

  * **Arguments:**
      * `source_code: str`: The text content of the file.
      * `file_path: str | None`: The path to the file being analyzed.
  * **Returns:** `dict[str, Any]`

### Success Response

When your analysis completes successfully, return a dictionary containing the list of `results` and a `summary` with `status: "completed"`.

```json
{
  "results": [
    {
      "severity": "low",
      "code": "MY_ERROR_CODE",
      "message": "A descriptive message about the issue.",
      "line": 10,
      "col": 5,
      "hint": "How the user can fix it."
    }
  ],
  "summary": {
    "issues_found": 1,
    "status": "completed"
  }
}
```

### Failure Response

If your plugin encounters *any* internal error (a bug, a bad regex, etc.), it **must** catch that error and return this "failure" dictionary. **Do not let the exception escape your `analyze` method.**

```json
{
  "results": [],
  "summary": {
    "issues_found": 0,
    "status": "failed",
    "error": "The string-formatted error message (e.g., str(e))"
  }
}
```

-----

## "Golden Standard" Plugin Template

Use this file as a starting point for your new plugin. It includes all required methods and the critical error-handling logic.

```python
# my_new_plugin.py
from __future__ import annotations

from typing import Any
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig

class Plugin:
    """
    A brief description of what my plugin does.
    """

    def __init__(self) -> None:
        """Set any default values here."""
        self.my_rule_setting = "default_value"

    def get_metadata(self) -> dict[str, str]:
        """Return the plugin's metadata."""
        return {
            "name": "MyNewPlugin",
            "version": "1.0.0",
            "description": "Checks for my specific project rules.",
        }

    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin from the main config object."""
        # Example: loading a value from toolkit.toml [tool.cqt.rules]
        if config.rules.get("my_rule_setting"):
            self.my_rule_setting = config.rules.my_rule_setting

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Run the analysis on a single file.
        This function MUST NOT raise an exception.
        """
        try:
            results: list[IssueResult] = []
            lines = source_code.splitlines()

            # --- Your Logic Goes Here ---
            
            for idx, line in enumerate(lines, start=1):
                if "bad_keyword" in line:
                    results.append({
                        "severity": "medium",
                        "code": "BAD_KEYWORD",
                        "message": "Found a forbidden keyword.",
                        "line": idx,
                        "col": line.find("bad_keyword") + 1,
                        "hint": "Remove the 'bad_keyword'.",
                    })

            # --- End of Your Logic ---

            # Return a Success Response
            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }

        except Exception as e:
            # Catch all errors and Return a Failure Response
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": str(e),
                },
            }

```