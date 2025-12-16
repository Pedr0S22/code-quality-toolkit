# Dead Code Detector Plugin Documentation

## USER GUIDE

Using this plugin helps you automatically detect defined code that is never used. By fixing these issues, you can clean up the codebase, reduce confusion, and improve your code's quality, making it easier to read and maintain.

## Version
0.2.1

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

To configure it, edit the rules described below in your toolkit.toml configuration file. The plugin reads its settings from the [`plugins.dead_code_detector`] section (**note**: this is not under [`rules`]):

```toml
[plugins.dead_code_detector]
ignore_patterns = ["^__", "tests/"]
min_name_length = 3
severity = "low"
```

You can adjust these values:

- `ignore_patterns`: A list of regex patterns. Names matching these patterns (like "__init__") will be ignored.

- `min_name_length`: Names shorter than this (e.g., i in a loop) will be ignored.

- `severity`: The severity level ("info", "low", "medium", "high") for reported issues.

**Note:** If you are using the web application, these modifications can be done directly in the app, using the information above.

## How to Use It

The Dead Code Detector plugin can be executed in two ways, giving users flexibility depending on their environment and needs:

1. **Run your toolkit's main CLI command:**

    ```bash
    python -m toolkit.core.cli analyze <path_to_your_code> --out report.json --config toolkit.toml
    ```

    or using make command:
    
    ```bash
    make run arg="--config toolkit.toml"
    ```

2. **Run Web Application:**

    **Start the Server:** Launch the core application server.
    ```bash
    make run_server
    ```
    **Access the Client:** Launch the App.
    ```bash
    make run_client
    ```
    **Run Analysis:** Use the interface to upload your file(s), select/configure plugins, and click the **"Run Analysis"** button. The results, including generated dashboards, will be displayed upon completion.

The `DeadCodeDetector` plugin will automatically analyze all Python files from the path you gave.
All issues found related to this plugin and others you enable, will be included in a summary and in detail in the final report.

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

## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21