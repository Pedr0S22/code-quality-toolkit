# StyleChecker Plugin – Technical Documentation
## Plugin Name
style_checker

## Version
0.1.3

## Authors
Alfonso Pintado Gracia            2025175710        @alfooonsoo17
Carlos Lomelín Valdés             2025154763        @carloslomelinv
Miguel Pedro Rodrigues Carvalho   2023216436        @parzival3301
Samuel Gomes Esteban              2025178876        @samuugomes
Mathias Gustavo Welz              2025167903        @mathiasgwelz

## ---USER GUIDE---
## What This Plugin Does
The StyleChecker plugin analyzes Python files and reports basic style issues such as:
- Long lines
- Trailing whitespace
- Incorrect indentation
- Non-snake_case filenames
- Class and function naming conventions (CamelCase for classes, snake_case for functions)
It helps maintain cleaner and more consistent code.

## How to Enable the Plugin
The StyleChecker is enabled automatically.
To configure it, edit the TOML configuration file under the rules table:
   [rules]
   max_line_length = 100
   check_whitespace = true
   indent_style = "spaces"
   indent_size = 4
   allow_mixed_indentation = false
   check_naming = true

## How to Use It
1. Run your toolkit's CLI command (depends on your project).
2. The StyleChecker will automatically analyze each file.
3. All issues found will appear in the generated report.json.

## Example Issues You May See
- LINE_LENGTH: the line is longer than allowed
- TRAILING_WHITESPACE: trailing spaces or tabs
- INDENT_MIXED: indentation mixes tabs and spaces
- INDENT_TABS_NOT_ALLOWED: tabs used when only spaces allowed
- INDENT_SPACES_NOT_ALLOWED: spaces used when only tabs allowed
- INDENT_WIDTH: indentation does not match indent size
- FILENAME_STYLE: filename does not follow snake_case
- CLASS_NAMING: class name is not in CamelCase
- FUNC_NAMING: function name is not in snake_case

Each issue includes:
- severity
- line and column
- message
- hint

## How to Fix Common Problems
- Remove trailing whitespace at the end of lines
- Use only spaces or only tabs based on configuration
- Match indentation to the configured indent size
- Rename your file to snake_case (e.g., my_module.py)
- Use CamelCase for class names and snake_case for function names

## Summary
Using the StyleChecker is straightforward: run the analysis, open the report, and fix any issues.
It keeps your code clean, readable, and consistent with minimal effort.

## ---TECHNICAL DOCUMENTATION---
## Description
The StyleChecker plugin analyzes Python source code and checks for simple style issues.
It verifies line length, trailing whitespace, indentation rules, and filename naming
conventions. The goal is to keep source code clean and readable across the project.

## 1. Purpose
The plugin helps developers follow basic style guidelines by detecting common formatting
mistakes. It improves consistency and makes the code easier to understand and maintain.

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

### Attributes
- `max_line_length`: maximum characters allowed per line
- `check_whitespace`: enable/disable whitespace checks
- `indent_style`: expected indentation ("spaces" or "tabs")
- `indent_size`: number of spaces per indentation level
- `allow_mixed_indentation`: whether mixing tabs and spaces is allowed
- `check_naming`: enables checks for class and function naming conventions (CamelCase for classes, snake_case for functions)

### Important Methods
- `configure(config)`: loads rule settings from the toolkit configuration
- `get_metadata()`: returns plugin name, version, and description
- `analyze(source_code, file_path)`: runs all style checks and returns results
- `_check_trailing_whitespace(lines)`: finds trailing spaces or tabs
- `_check_indentation(lines)`: checks indentation style and width

## 4. Output Format
The plugin returns a dictionary with:
{
   "results": [... list of issues ...],
   "summary": {
      "issues_found": X,
      "status": "completed"
   }
}

## 5. Example Issue Codes
- `LINE_LENGTH`: line too long
- `TRAILING_WHITESPACE`: spaces/tabs at end of line
- `INDENT_MIXED`: mixing spaces and tabs
- `INDENT_TABS_NOT_ALLOWED`: tabs not allowed
- `INDENT_SPACES_NOT_ALLOWED`: spaces not allowed
- `INDENT_WIDTH`: indentation not matching indent_size
- `FILENAME_STYLE`: filename not in snake_case
- `CLASS_NAMING`: class name is not in CamelCase
- `FUNC_NAMING`: function name is not in snake_case

## 6. Conclusion
The StyleChecker plugin is a simple but effective tool for maintaining style consistency
in Python projects. It helps improve readability and keeps the codebase clean.