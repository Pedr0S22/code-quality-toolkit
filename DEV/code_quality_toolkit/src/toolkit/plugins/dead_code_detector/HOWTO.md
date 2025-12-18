# Dead Code Detector Plugin Documentation

## Version
0.2.1

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

#### Disclaimer: This plugin component was build using AI.