# Cyclomatic Complexity Plugin Documentation

## USER GUIDE

Using this plugin helps you automatically detect functions that are becoming too complex. By fixing these issues, you can improve your code's quality, making it easier to test, modify, and maintain.

## Version
0.1.2

### What This Plugin Does

The `Cyclomatic Complexity` plugin analyzes Python files and reports on three distinct code quality metrics:

* **Cyclomatic Complexity**: Measures the "decision density" of your functions. It counts decision points (`if`, `while`, `for`, `and`, `or`, `except`, etc.).
* **Function Length**: Measures the number of physical lines in a function or method.
* **Argument Count**: Counts the total number of arguments a function or method accepts.

This plugin helps you find code that is potentially hard to read, test, and maintain.

### How to Enable the Plugin

The plugin must be added in `toolkit.toml` - like is shown below - to be enabled automatically by the core toolkit.

```toml
[plugins]
enabled = ["CyclomaticComplexity","<OtherPlugin>",etc]
```

To configure it, edit the rules described below in your `toolkit.toml` configuration file. The plugin reads its settings from the `[rules.complexity]` section:

```toml
[rules.complexity]
max_complexity = 10
max_function_length = 50
max_arguments = 5
```

You can adjust these values to make the analysis more or less strict.

## How to Use It
1. Run your toolkit's main CLI command:

    ```python -m toolkit.core.cli analyze <path_to_your_code> --out report.json --config toolkit.toml```

    or using make command:
    
    ```make run arg="--config toolkit.toml"```.
2. The CyclomaticComplexity plugin will automatically analyze all Python files from the path you gave.
3. All issues found related to this plugin and others you enable, will be included in a summary and in detail in the final report.

## Example Issues You May See
- **HIGH_COMPLEXITY**: The function's complexity score exceeds the configured max_complexity.

- **LONG_FUNCTION**: The function's line count exceeds the configured max_function_length.

- **TOO_MANY_ARGUMENTS**: The function's argument count exceeds the configured max_arguments.

- **SYNTAX_ERROR**: The file contains invalid Python syntax, and the plugin could not parse it.

Each issue detected includes:
- severity
- line and column
- message
- hint

to help discover where the error was detected.

## How to Fix Common Problems
- **HIGH_COMPLEXITY**: Refactor the function. Try to break it down into smaller, simpler functions that each do one thing.

- **LONG_FUNCTION**: Refactor the function. A long function often means it has too many responsibilities. Split its logic into smaller, well-named helper functions.

- **TOO_MANY_ARGUMENTS**: Refactor the function's signature. Consider grouping related arguments into a single object or data class, or see if the function can be simplified.

- **SYNTAX_ERROR**: Fix the syntax error in the file. The plugin cannot analyze a file that it can't read.

## TECHNICAL DOCUMENTATION

### Description
The `CyclomaticComplexity` plugin performs static analysis on Python source code by parsing it into an Abstract Syntax Tree (AST). It extends the `BasePlugin` contract and implements the golden rule refered in [`src\toolkit\plugins\README.md`](..\README.md). It analyzes each function for three metrics (complexity, length, arguments) and returns structured issues in the format expected by the core engine.

## 1. Purpose
The plugin's purpose is to provide automated, configurable checks for common code "smells" related to complexity. This helps developers adhere to quality standards and catch hard-to-maintain code early.

## 2. How It Works
The plugin performs several checks:

1. The plugin receives the `source_code` as a string from the core engine.

2. It attempts to parse the code using `ast.parse()`.

3. If `ast.parse()` raises a `SyntaxError`, it immediately returns a **SYNTAX_ERROR** issue and sets the status to "partial".

4. If parsing succeeds, it uses `ast.walk()` to find all `ast.FunctionDef` and `ast.AsyncFunctionDef` nodes.

5. For each function node, it performs three calculations:

    - **Complexity**: It runs a custom `_ComplexityVisitor` (an ast.NodeVisitor) on the function body. This visitor increments a counter for each decision-making node (e.g., If, For, While, BoolOp, ExceptHandler).

    - **Length**: The ```_function_length``` helper calculates the line count using `node.end_lineno - node.lineno`.

    - **Arguments**: The `_arg_count` helper inspects the function's `args` attribute to sum all types of arguments (posonlyargs, args, kwonlyargs, vararg, kwarg).

6. Each calculated value is compared against the thresholds loaded from the configuration (max_complexity, max_function_length, max_arguments).

7. If a value exceeds its threshold, a corresponding `IssueResult` dictionary is created.

8. It returns a final dictionary containing a list of all results and a summary object.

9. All other unexpected exceptions are caught to prevent crashing the core engine, returning a "failed" status.

## 3. Main Class: `Plugin`

### Attributes

- **max_complexity** (int): The maximum allowed cyclomatic complexity.

- **max_function_length** (int): The maximum allowed lines for a function body.

- **max_arguments** (int): The maximum allowed arguments for a function.

### Important Methods
- `configure(config: ToolkitConfig)`: Loads the max_complexity, max_function_length, and max_arguments values from the configuration object.

- `get_metadata()` -> dict: Returns the plugin's name ("CyclomaticComplexity"), version, and description.

- `analyze(source_code: str, file_path: str | None)` -> dict: The main entry point. It orchestrates the AST parsing, analysis, and error handling, returning the final results dictionary.

- `_ComplexityVisitor(ast.NodeVisitor)`: (Internal class) A visitor that traverses an AST node and calculates its complexity score.

- `_function_length(node: ast.AST)` -> int | None: (Internal function) A helper to calculate the line count of a function node.

- `_arg_count(fn: ast.AST)` -> int: (Internal function) A helper to count all arguments in a function definition.

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
            "hint": "Corrija a sintaxe antes de medir complexidade.",
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
- **HIGH_COMPLEXITY**: Function complexity exceeds max_complexity.

- **LONG_FUNCTION**: Function line count exceeds max_function_length.

- **TOO_MANY_ARGUMENTS**: Function argument count exceeds max_arguments.

- **SYNTAX_ERROR**: The file could not be parsed due to a syntax error.


## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21