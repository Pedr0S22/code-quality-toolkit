# HOWTO – Using the StyleChecker Plugin

## What This Plugin Does
The StyleChecker plugin checks Python files for basic style issues such as long lines,
trailing whitespace, incorrect indentation, and non-snake_case filenames.

It helps you write cleaner and more consistent code.

## How to Enable the Plugin
The StyleChecker is enabled automatically by default.
To configure it, edit your toolkit configuration file (usually `rules` inside the TOML file).

Example:
[rules]
max_line_length = 100
check_whitespace = true
indent_style = "spaces"
indent_size = 4
allow_mixed_indentation = false

## How to Use It
1. Run the main toolkit CLI command (example command depends on your project).
2. The StyleChecker will automatically analyze each file.
3. All issues found will appear in the generated `report.json`.

## Example of Issues You May See
- "LINE_LENGTH": the line is longer than allowed
- "TRAILING_WHITESPACE": the line ends with unnecessary spaces
- "INDENT_MIXED": indentation mixes tabs and spaces
- "FILENAME_STYLE": filename does not follow snake_case

Each issue includes:
- severity
- line and column
- a message explaining the problem
- a hint suggesting how to fix it

## How to Fix Common Problems
- Remove any spaces at the end of lines.
- Use only spaces (or only tabs) for indentation.
- Make sure indentation uses multiples of the configured indent size.
- Rename your file to something like `my_module.py`.

## Summary
Using the StyleChecker plugin is straightforward: run the analysis, read the report,
and fix any style issues listed. The plugin helps keep your code clean and consistent
with minimal effort.