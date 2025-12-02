"""Command line interface for the Code Quality Toolkit (entry point)."""

from __future__ import annotations

# Each of the following import statements brings functionality from the Python’s
# standard library:
import argparse  # Helps parsing command-line arguments → see 'build_parser()'
import json  # This module is used to read and write JSON data (the analysis results)
import sys  # provides access to system-level information and functions, such as

# command line arguments (sys.argv), program exit codes (sys.exit)
# and standard input/output streams (sys.stdin, sys.stdout)
from pathlib import (
    Path,
)  # This module provides a way to handle filesystem paths instead of using strings.

# These are imports from our own application:
# → note the relative paths notation (.. and . ), as we are dealing with Python modules
from ..utils.config import ToolkitConfig, load_config
from . import logging
from .aggregator import aggregate
from .engine import run_analysis
from .errors import AnalysisExecutionError, ConfigurationError, PluginLoadError
from .loader import load_plugins

# Our classification of severity, the final verdict after the analysis performed
SEVERITY_ORDER = ["info", "low", "medium", "high"]

# Exit status codes
EXIT_SUCCESS = 0
EXIT_MANAGED_ERROR = 1
EXIT_UNEXPECTED_ERROR = 2
EXIT_SEVERITY_ERROR = 3


def _build_parser() -> argparse.ArgumentParser:
    """
    This function contains the blueprint that dictates the command-line syntax
    and behavior for the Code Quality Toolkit, using /argparse/

    It's responsibility is to define the main command (analyze) and all its
    arguments, options, and flags that the user can pass when running the
    'cli' script from a terminal.
    """

    # This statement creates the main 'parser' object.
    # The description is the text that appears when the user runs the script
    # with the -h or --help flag.
    parser = argparse.ArgumentParser(description="Code Quality Toolkit CLI")

    # This is how you set up this program to use multiple, distinct (sub)
    # commands that deal themselves with their own (sub) command-line arguments
    # (like git, which has git clone xx, git commit yy , etc.).
    # → Remember that each plugin most likely will require additional
    # distinct arguments.
    subparsers = parser.add_subparsers(dest="command", required=True)

    # *** Below we (only) manage the command line options related to the 'analyze'
    # functionality ***

    # This creates a new sub-parser specifically for the command "analyze".
    # The help text explains what this command does when the user asks for help.
    analyze = subparsers.add_parser("analyze", help="Run analysis on a path")

    # Consider additional commands...
    # discard = subparsers.add_parser("discard", help="Discard everything and exit")

    # This code block adds the mandatory and optional parameters specific to the
    # 'analyze' command.

    ## Defines a required positional argument named 'path'. This is the directory
    ## or file the user wants to analyze.
    analyze.add_argument(
        "path", type=str, help="Folder or file to be subject to analysis"
    )

    ## Defines an optional flag (--plugins).
    ## It accepts a string (a comma-separated list of plugins or the literal word
    ## "all") and defaults to "all".
    analyze.add_argument(
        "--plugins",
        type=str,
        default="all",
        help="Comma separated plugin list | or 'all'",
    )

    # Defines an (optional) output file path; default is 'report.json'.
    analyze.add_argument(
        "--out", type=str, default="report.json", help="output report JSON file"
    )

    # Defines an optional flag for inclusion patterns. This collects a list of glob
    # patterns to *include* certain files/directories in the analysis.
    # action="append" allows the user to specify this option multiple times
    # (e.g., --include-glob "*.py" and --include-glob "*.js"), and all values
    # are collected into a list that defaults to empty [].
    analyze.add_argument(
        "--include-glob", action="append", default=[], help="inclusion glob patterns"
    )

    # The same as for the inclusion patterns, but allows for the collects a list of
    # glob patterns to *exclude* certain files/directories from the analysis.
    analyze.add_argument(
        "--exclude-glob", action="append", default=[], help="exclusion glob patterns"
    )

    # Defines an optional path to a custom configuration file, defaulting to None.
    analyze.add_argument(
        "--config", type=str, default=None, help="Ficheiro toolkit.toml"
    )

    # Defines a flag to control the exit behavior.
    # choices=SEVERITY_ORDER[1:]:Restricts the user's input to a predefined list
    # of severity levels (loaded from the global variable SEVERITY_ORDER).
    # This application will exit with a failure code if any issue found has
    # a severity equal to or higher than the level the user specifies
    # (e.g., fail on "low", "medium", "high").
    analyze.add_argument(
        "--fail-on-severity",
        type=str,
        choices=SEVERITY_ORDER[1:],
        default=None,
        help="Fail if finds error >= stated severity level",
    )

    # Defines the verbosity/log-level of the application.
    # type=str.upper ensures case-insensitivity at the parsing level.
    analyze.add_argument(
        "--log-level",
        type=str.upper,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set the logging verbosity level",
    )

    # A shortcut flag for setting the log level to DEBUG.
    analyze.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (equivalent to --log-level DEBUG)",
    )
    # returns the fully configured parser object.
    return parser

def _resolve_requested_plugins(option: str, config: ToolkitConfig) -> list[str] | None:
    """
    Determines the final list of analysis plugins to be loaded and run by reconciling
    the user's command-line input with the default plugins specified in the
    configuration file. If the input is empty or invalid, it gracefully falls back
    to the default plugins defined in the configuration.
    """

    if (
        option.lower() == "all"
    ):  # first, check if the user explicitly requested all plugins
        return (
            config.enabled_plugins
        )  # If so, it returns the full list of plugins defined
        # as enabled in the ToolkitConfig object
        # This is the easiest way for a user to run the default suite.
    # Parses the custom 'option' plugins list:
    # 'item.strip()' removes any leading or trailing whitespace
    # 'if item.strip()' filters out any empty strings that might result from
    # extra commas
    plugins = [
        item.strip() for item in option.split(",") if item.strip()
    ]  # returns an expunged list of requested plugin names

    # The list of valid 'plugins' is returned, otherwise (if empty)
    # falls back to the default config
    return plugins or config.enabled_plugins


def _should_fail(report: dict, threshold: str) -> bool:
    """
    This function determines whether the program should return a non-zero exit code
    (i.e., "fail") based on whether the total number of issues found at or above
    a specified severity threshold is greater than zero.

    i.e. "If you find even one issue that is at least as severe as the user's
    specified threshold, fail!"

    It takes two arguments:
    - report: The complete analysis report dictionary, which contains the
    summary of issues.
    - threshold: A string representing the minimum severity level that triggers
    a failure (e.g., "medium" or "high").
    """

    # Looks up the numerical position (index) of the specified failure threshold
    # within the SEVERITY_ORDER list and converts the human-readable severity name
    # (low, medium, high) into a numeric value.
    severity_index = SEVERITY_ORDER.index(threshold)

    # extracts the dictionary from the report summary that holds the number of
    # issues per severity level
    # (e.g., {"info": 35, "low": 12, "medium": 1, "high": 0}).
    issues_by_severity = report["summary"]["issues_by_severity"]

    # SEVERITY_ORDER[severity_index:] creates a sliced list containing the
    # threshold severity and all severities that are ranked higher (more severe).
    # Example: If threshold is "medium", and its index is 2, the slice is
    # ["medium", "high"].
    # The code loops through this sliced list (the failure range)
    for severity in SEVERITY_ORDER[severity_index:]:
        # checks the issue count for the current severity level.
        # (if the severity level isn't even in the report dictionary,
        # it defaults to 0.)
        if issues_by_severity.get(severity, 0) > 0:
            # if the count for the current severity (or any higher severity)
            # is greater than zero, the function immediately returns True,
            # indicating the program should fail.
            return True

    # otherwise, if the loop completes without finding any issues at or above
    # the threshold, the function returns False (success).
    return False


def main(
    argv: list[str] | None = None,
) -> int:  # receives command-line arguments, returns status code as integer.
    """This is the main CLI entry point"""

    # Command line argument parsing
    parser = (
        _build_parser()
    )  # setup and configuring of the command-line interface (CLI) structure
    args = parser.parse_args(
        argv
    )  # Parses the command-line arguments (argv). The results are stored
    # in the args object, where arguments are accessible as attributes
    # (e.g., args.command -> see below).

    # this code segment is enclosed in a 'try' block to enable error handling
    try:
        # executes the "run_analyze" code if the first command line argument is
        # "analyze"
        if args.command == "analyze":
            return _run_analyze(args)  # exit code is returned by _run_analyze

        # you can put here the code that deals with other command
        # (must be specified in 'build_parser()')
        if args.command == "discard":
            print("hello discard")
            return EXIT_UNEXPECTED_ERROR

    # This block catches known, expected exceptions specific to the application:
    # a bad configuration file, failure to load a plugin, and an issue during the
    # analysis run.
    except (ConfigurationError, PluginLoadError, AnalysisExecutionError) as exc:
        logging.log(
            "cli.error",
            level="ERROR",
            error=str(exc)
        )  # records the error internally for debugging purposes.
        print(
            f"Error: {exc}", file=sys.stderr
        )  # displays an error message to the standard error stream (sys.stderr)
        return EXIT_MANAGED_ERROR  # a specific exception was properly managed.

    # This block acts as a safety net by catching any other unexpected exceptions
    # that might occur.
    except Exception as exc:  # noqa: BLE001
        # → This 'noqa' comment is a directive to a linter like Bandit to ignore
        # its rule BLE001, which typically warns against broad except Exception:
        # clauses. It has been added here because the intent is to catch all
        #  remaining exceptions to prevent an unhandled crash.
        logging.log(
            "cli.error",
            level="ERROR",
            error=str(exc))
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return EXIT_UNEXPECTED_ERROR

    return EXIT_SUCCESS  # if no exception occurs


def _run_analyze(args: argparse.Namespace) -> int:
    """This function contains the core logic of the 'analyze' command.

    It performs the sequence of steps necessary to configure the analysis,
    load plugins, run the file scan, generate a report, save the report, and
    determine the appropriate program exit code.
    """

    # == Logging Configuration ==
    # Check for verbose flag first (shortcut for DEBUG), otherwise use the
    # value provided in --log-level.
    target_log_level = "DEBUG" if args.verbose else args.log_level
    logging.set_log_level(target_log_level)

    # == Configuration and Overrides ==

    # loads the base configuration: it either uses the file path provided by
    # the user via --config or loads a default configuration (from toolkit.toml)
    config = load_config(args.config)

    # Retrieves any glob patterns passed via the --include-glob flag
    # (which is a list due to action="append").
    include_globs = args.include_glob or []

    # Checks if the user provided any patterns on the command line. If so,
    # they override the include/exclude patterns defined in the configuration file.
    if include_globs:
        config.analyze.include = include_globs
    exclude_globs = args.exclude_glob or []
    if exclude_globs:
        config.analyze.exclude = exclude_globs

    # == Plugin Management ==

    # Takes the value from the --plugins flag (args.plugins) and the configuration
    # object. It determines the final, definitive list of plugin names to be
    # loaded, resolving "all" to the full list, or combining CLI requests with
    # config defaults.
    requested_plugins = _resolve_requested_plugins(args.plugins, config)

    # imports the necessary Python modules and instantiates the code analysis
    # logic for each requested plugin.
    plugins = load_plugins(requested_plugins)

    # == Analysis Execution ==

    # Executes the core function of the tool:
    # - scans the directory/file specified by args.path.
    # - applies the loaded plugins to the files it finds.
    # - uses the config to guide how the analysis is performed.
    #
    # Returns the raw results, a list of analyzed files and the status/issues
    # found by each plugin.
    files, plugin_status = run_analysis(args.path, plugins, config)

    # Gets the raw results and formats them into a structured, final report format
    # (a JSON structure that summarizes issues, file counts, and severities).
    report = aggregate(files, plugin_status)

    # == Report Output ==

    # Set the output path (from pathlib) according to the file path specified by
    # the --out argument.
    output_path = Path(args.out)
    # serializes the final report dictionary into a JSON string and writes it to
    # the output file.
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # records that the report was successfully written, including the path and
    # the total number of issues found.
    logging.log(
        "cli.report_written",
        level="INFO",
        path=str(output_path),
        issues=report["summary"]["total_issues"],
    )

    # == Exit Code Determination ==

    # Check Failure Condition: The if statement checks two things:
    # - If the user set the flag (i.e., they want the script to fail if a
    # high-severity issue is found). If any issues of the specified
    # severity level (e.g., "medium") or higher were found.
    if args.fail_on_severity and _should_fail(report, args.fail_on_severity):
        print("Failed on severity")
        return EXIT_SEVERITY_ERROR
    
    loaded_plugin_names = set(plugins.keys())
    requested_plugins_names = set(requested_plugins)
    if  requested_plugins_names != loaded_plugin_names:
        missing = requested_plugins_names - loaded_plugin_names
        raise PluginLoadError(f"Requested plugins not found: {', '.join(missing)}")
    
    return EXIT_SUCCESS  # success exit


if __name__ == "__main__":  # pragma: no cover
    # this 'pragma' dorective instructs the coverage tool to exclude
    # the entire block of code under this line from the coverage report. It prevents
    # this boilerplate code from artificially lowering the code coverage percentage.
    sys.exit(
        main()
    )  # Executes main (the CLI entry point) and exits with a status code (0 is ok,
    # otherwise is an error code).
