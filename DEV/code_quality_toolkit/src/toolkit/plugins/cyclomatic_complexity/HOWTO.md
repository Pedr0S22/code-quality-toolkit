# Cyclomatic Complexity Plugin Documentation

## Version
0.2.1

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

#### Disclaimer: This plugin component was build using AI.