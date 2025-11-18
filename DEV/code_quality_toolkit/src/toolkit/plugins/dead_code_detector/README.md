# Dead Code Detector Plugin Documentation

## USER GUIDE

Using this plugin helps you automatically detect defined code that is never used. By fixing these issues, you can clean up the codebase, reduce confusion, and improve your code's quality, making it easier to read and maintain.

## Version
0.1.0

### What This Plugin Does

The `Dead Code Detector` plugin analyzes Python files and reports on defined elements that are never used (loaded) within the same file.

It detects:
* **Unused Functions**: Functions or methods that are defined but never called.
* **Unused Classes**: Classes that are defined but never instantiated or referenced.
* **Unused Variables**: Variables that are assigned a value but never read.

This plugin helps you find and remove redundant code that clutters the project.

### How to Enable the Plugin

The plugin must be added in `toolkit.toml` - like is shown below - to be enabled automatically by the core toolkit.

```toml
[plugins]
enabled = ["DeadCodeDetector","<OtherPlugin>",etc]
```

To configure it, edit the rules described below in your toolkit.toml configuration file. The plugin reads its settings from the [`plugins.dead_code`] section (**note**: this is not under [`rules`]):

```toml
[plugins.dead_code]
ignore_patterns = ["^__", "tests/"]
min_name_length = 3
severity = "low"
```

You can adjust these values:

- `ignore_patterns`: A list of regex patterns. Names matching these patterns (like "__init__") will be ignored.

- `min_name_length`: Names shorter than this (e.g., i in a loop) will be ignored.

- `severity`: The severity level ("info", "low", "medium", "high") for reported issues.

## How to Use It
1. Run your toolkit's main CLI command:

    ```python -m toolkit.core.cli analyze <path_to_your_code> --out report.json --config toolkit.toml```

    or using make command:
    
    ```make run arg="--config toolkit.toml"```.
2. The `DeadCodeDetector` plugin will automatically analyze all Python files from the path you gave.
3. All issues found related to this plugin and others you enable, will be included in a summary and in detail in the final report.

## Example Issues You May See
- **DEAD_CODE**: A function, class, or variable was defined but never used (loaded) anywhere in the file.

- **SYNTAX_ERROR**: The file contains invalid Python syntax, and the plugin could not parse it.

Each issue detected includes:
- severity
- line and column
- message
- hint

to help discover where the error was detected.

## How to Fix Common Problems
- **DEAD_CODE**: Review the reported name (e.g., my_old_function).

    - If it is truly obsolete, delete the function, class, or variable definition.

    - If it's a helper you forgot to call, add the code to use it.

    - If it's intended for use by other files (e.g., a public API), add its name or a pattern (like ^public_) to the ignore_patterns list in your config.

- **SYNTAX_ERROR**: Fix the syntax error in the file. The plugin cannot analyze a file that it can't read.

## TECHNICAL DOCUMENTATION

### Description

The `DeadCodeDetector` plugin performs static analysis on Python source code by parsing it into an Abstract Syntax Tree (AST). It extends the BasePlugin contract and implements the golden rule refered in [`src\toolkit\plugins\README.md`](..\README.md). It analyzes each file by collecting all definitions and all uses, then reports definitions that are never used.

## 1. Purpose
Dead code makes a project harder to read, increases the codebase size, and creates confusion between active and obsolete components. This plugin helps keep the project clean, clear, and easier to maintain over time.

## 2. How It Works
The plugin performs several checks:

1. The plugin receives the `source_code` as a string from the core engine.

2. It attempts to parse the code using `ast.parse()`.

3. If `ast.parse()` raises a `SyntaxError`, it immediately returns a **SYNTAX_ERROR** issue and sets the status to "partial".

4. If parsing succeeds, it uses `ast.walk()` with a custom `_DefUseVisitor` to find all definitions and uses.

5. The visitor collects:

    - Definitions (FunctionDef, ClassDef, Assign, AnnAssign) into a defs dictionary ({name: line_number}).

    - Uses (Name nodes with ast.Load context) into a uses set ({name}).

    - Imports (Import, ImportFrom) into an imports set to prevent reporting imported names as unused.

6. After the tree is visited, the plugin iterates through the defs dictionary.

7. For each defined name, it checks if it should be skipped (matches `ignore_patterns`, is shorter than `min_name_length`, or is in the imports set).

8. If a name is not skipped and is not in the uses set, a `DEAD_CODE` issue is created.

9. It returns a final dictionary containing a list of all results and a summary object.

10. All other unexpected exceptions are caught to prevent crashing the core engine, returning a "failed" status.

## 3. Main Class: `Plugin`

### Attributes

- **ignore_patterns** (list[re.Pattern[str]]): A list of compiled regex patterns for names to ignore.

- **severity** (str): The severity level to report for issues (e.g., "low").

- **min_name_len** (int): The minimum length of a name to be considered for analysis.

### Important Methods
- `configure(config: ToolkitConfig)`: Loads the ignore_patterns, severity, and min_name_length values from the configuration object.

- `get_metadata()` -> dict: Returns the plugin's name ("DeadCodeDetector"), version, and description.

- `analyze(source_code: str, file_path: str | None)` -> dict: The main entry point. It orchestrates the AST parsing, analysis, and error handling.

- `_ignored(self, name: str)` -> bool: (Internal helper) Checks if a given name should be skipped based on config rules.

- `_DefUseVisitor(ast.NodeVisitor)`: (Internal class) The visitor that traverses the AST to collect all definitions, uses, and imports.

## 4. Output Format
The plugin return a report in dictionary format and it can be in 3 formats:
- Status: "completed"

```json
{
   "results": [... list of issues ...],
   "summary": {
      "issues_found": X,
      "status": "completed"
   }
}
```

- Status: "partial"

```json
{
    "results": [
        {
            "severity": "high",
            "code": "SYNTAX_ERROR",
            "message": "Erro de sintaxe: <X>",
            "line": Y,
            "col": Z,
            "hint": "Corrija a sintaxe para permitir a análise de dead code.",
        }
    ],
    "summary": {"issues_found": 1, "status": "partial"},
}
```

- Status: "failed"

```json
{
   "results": [... list of issues ...],
   "summary": {
      "issues_found": 0,
      "status": "failed",
      "error": <X>,
   }
}
```

## 5. Example Issue Codes
- **DEAD_CODE**: A function, class, or variable was defined but never used.

- **SYNTAX_ERROR**: The file could not be parsed due to a syntax error.


## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21
