Plugin Name: StyleChecker
Version: 0.1.3
Description: Validates basic Python code style rules, including line length, filename conventions, trailing whitespace, and indentation consistency.

---

General Description:
The StyleChecker plugin performs static code analysis to ensure that Python source files follow basic style conventions.
It helps maintain a clean, readable, and consistent codebase by identifying issues such as excessive line length, unnecessary trailing spaces, incorrect indentation, or filenames that do not follow snake_case format.

---

Objective:
To automatically detect and report common style issues in Python files, promoting consistent formatting and readability across the project.

---

How It Works:

1. Splits the source code into individual lines.
2. Checks each line for maximum allowed length.
3. Detects spaces or tab characters at the end of lines.
4. Validates indentation rules based on configured preferences (spaces or tabs).
5. Verifies that the filename follows the snake_case naming convention.
6. Returns a list of results (issues) and a summary of findings.

---

Class: Plugin

Attributes:

* max_line_length (int): Maximum number of characters allowed per line (default 88).
* check_whitespace (bool): Enables or disables trailing whitespace detection.
* indent_style (str): Defines the indentation type, either "spaces" or "tabs".
* indent_size (int): Number of spaces per indentation level (default 4).
* allow_mixed_indentation (bool): Allows or forbids mixing tabs and spaces.

---

Main Methods:

*init*(self):
Initializes default configuration for line length, whitespace checking, indentation style, and file naming rules.

configure(self, config: ToolkitConfig):
Loads style settings from the toolkit’s configuration file, overriding default values when available.

get_metadata(self):
Returns plugin metadata, including its name, version, and short description.

_check_trailing_whitespace(self, lines):
Scans all lines for trailing spaces or tabs.
If found, returns an issue with code “TRAILING_WHITESPACE” and a hint to remove them.

_check_indentation(self, lines):
Validates the indentation of each line.
Detects:

* Mixed indentation (tabs and spaces combined).
* Tabs used when spaces are required (or vice versa).
* Incorrect indentation width (not a multiple of indent_size).
  Returns issues such as INDENT_MIXED, INDENT_TABS_NOT_ALLOWED, INDENT_SPACES_NOT_ALLOWED, or INDENT_WIDTH.

analyze(self, source_code, file_path):
Main method that runs all checks on the provided source code.
Performs:

* Line length validation.
* Whitespace and indentation checks.
* Filename convention verification.
  Returns a dictionary containing:

  * "results": list of detected issues.
  * "summary": number of issues found and the analysis status.

---

Regular Expressions Used:

* SNAKE_CASE_RE: ^[a-z0-9]+.py$ (checks snake_case filenames)
* _TRAILING_WS_RE: [ \t]+$ (detects trailing whitespace)
* _LEADING_WS_RE: ^([ \t]+) (matches indentation at the beginning of a line)

---

Example of Use:
plugin = Plugin()
code = "\tprint('Hello')  "
report = plugin.analyze(code, "ExampleFile.py")
print(report["results"])

Example Output:
[
{ "code": "TRAILING_WHITESPACE", "line": 1, "message": "Spaces or tabs at end of line." },
{ "code": "INDENT_TABS_NOT_ALLOWED", "line": 1, "message": "Tabs are not allowed; use spaces instead." },
{ "code": "FILENAME_STYLE", "line": 1, "message": "Filename does not follow snake_case convention." }
]

---

Possible Issue Codes:

Code: LINE_LENGTH
Severity: low
Description: Line exceeds maximum number of characters.
Suggestion: Split the line or reduce length.

Code: TRAILING_WHITESPACE
Severity: low
Description: Line ends with extra spaces or tabs.
Suggestion: Remove trailing whitespace.

Code: INDENT_MIXED
Severity: low
Description: Mixed spaces and tabs used for indentation.
Suggestion: Use only one indentation type.

Code: INDENT_TABS_NOT_ALLOWED
Severity: low
Description: Tabs used instead of spaces.
Suggestion: Convert tabs to spaces.

Code: INDENT_SPACES_NOT_ALLOWED
Severity: low
Description: Spaces used instead of tabs.
Suggestion: Convert spaces to tabs.

Code: INDENT_WIDTH
Severity: low
Description: Indentation width is not a multiple of indent_size.
Suggestion: Adjust indentation to match configured size.

Code: FILENAME_STYLE
Severity: info
Description: Filename does not follow snake_case format.
Suggestion: Rename file using lowercase letters and underscores.

---

Conclusion:
The StyleChecker plugin is a simple but effective tool to ensure Python source files follow consistent style guidelines.
By automatically detecting common formatting problems, it helps developers maintain cleaner, more professional code and improves team collaboration in shared projects.

---