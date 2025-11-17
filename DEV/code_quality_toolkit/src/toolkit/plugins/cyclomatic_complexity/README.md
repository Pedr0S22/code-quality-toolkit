# Cyclomatic Complexity Plugin Documentation

## USER GUIDE

Using this plugin helps you automatically detect functions that are becoming too complex. By fixing these issues, you can improve your code's quality, making it easier to test, modify, and maintain.

## Version
0.1.0

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

## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21