"""Aggregation utilities to build the unified report."""

from __future__ import annotations

import datetime as _dt

from .. import __version__
from .contracts import (
    FileReport,
    Severity,
    UnifiedReport,
    validate_plugin_report,
    validate_unified_report,
)

# the ordered hierarchy of severity levels used throughout this Code Quality Toolkit
SEVERITIES: list[Severity] = ["info", "low", "medium", "high"]


def _compute_top_offenders(files: list[FileReport]) -> list[dict[str, int | str]]:
    """
    This function analyzes the results of the code analysis to
    identify the files with the highest number of issues.
    It returns a list of the top MAX_NUMBER_OF_TOP_OFFENDERS "offending" files,
    ranked by issue count.

    MAX_NUMBER_OF_TOP_OFFENDERS is a magic number.
    """
    MAX_NUMBER_OF_TOP_OFFENDERS = 5

    offenders: list[tuple[str, int]] = []
    # loop through every file_report in the input list
    for file_report in files:
        # For each file, it calculates the total number of issues found across
        # all plugins using a generator expression inside the sum() function.
        # This accumulates all issues reported by individual plugins for that
        # specific file.
        issues = sum(p["summary"]["issues_found"] for p in file_report["plugins"])
        # A list of tuples (offenders) is built, where each tuple contains
        # the file path (file_report["file"]) and the total issue count.
        offenders.append((file_report["file"], issues))

    # The offenders list is sorted by issue count (item[1])
    # and then file path (item[0]). By using the negative of item[1],
    # the sort is performed in descending order (the most issues come first).
    offenders.sort(key=lambda item: (-item[1], item[0]))

    # convert the sorted list of tuples back into a list of dictionaries
    # with clear keys ("file" and "issues").
    # 'if count > 0' ensures that *only* files that have at least one issue
    # are included in the final results.
    # [:N] slices the resulting list to return only the top N files
    # with the highest issue counts.
    return [{"file": file, "issues": count} for file, count in offenders if count > 0][
        :MAX_NUMBER_OF_TOP_OFFENDERS
    ]


def _derive_status(plugin_status: dict[str, str]) -> str:
    """
    This function determines the overall success status of the entire analysis
    run based on the execution results of all individual plugins.
    It prioritizes failure states to give the most conservative assessment.

    The function takes the plugin_status dictionary (where keys are plugin names
    and values are their status, e.g., "completed", "partial", or "failed") and
    returns a single string representing the overall analysis status.
    """

    # First check if the plugin_status dictionary is empty, which means that
    # no plugins were loaded or run. This is considered an internal
    # failure of the analysis engine, so the function returns "failed".
    if not plugin_status:
        return "failed"

    # the plugin_status values are collected into a set (removes duplicates)
    statuses = set(plugin_status.values())

    # If the set contains "failed" (meaning at least one plugin crashed or
    # explicitly signaled failure), the overall status is immediately set to "failed".
    if "failed" in statuses:
        return "failed"

    # otherwise, if the set contains "partial" (meaning at least one plugin encountered
    # errors on some files but kept running, the overall status is "partial".
    # This signals to the user that the results may be incomplete.
    if "partial" in statuses:
        return "partial"

    # otherwise, all plugins have returned "completed"
    return "completed"


def aggregate(
    files: list[FileReport],
    plugin_status: dict[str, str],
) -> UnifiedReport:
    """
    This function is the final step in the analysis, responsible for consolidating
    the detailed per-file results and plugin execution statuses into a single,
    comprehensive Unified Report (a structured dictionary). It computes various
    summaries, totals, and metadata required for presenting the
    final analysis results.
    """

    # == Summary Initialization ==

    # Initializes a dictionary (issues_by_severity) to count the total number
    # of issues found for each severity level. It starts all counts at 0 using
    # a list of known severities.
    issues_by_severity: dict[Severity, int] = {severity: 0 for severity in SEVERITIES}
    # Initializes a dictionary to count the total number of issues found by each plugin,
    # starting with all known plugins from the input 'splugin_status'.
    issues_by_plugin: dict[str, int] = {name: 0 for name in plugin_status}
    # 'total_issues' is initialized to track the cumulative count of all issues found.
    total_issues = 0

    # == Iterating and Counting Results ==

    # This section iterates through the nested structure of the input files list to
    # accumulate all counts:
    # i.    ensures the report structure is valid before processing
    # (validate_plugin_report)
    # ii.   The number of issues found by the plugin in that file (plugin_total)
    # is added to the total_issues grand count and to the specific plugin's count
    # in issues_by_plugin.
    # iii.  The innermost loop iterates through the detailed results
    # (individual issues) and increments the count for the corresponding severity
    # in the issues_by_severity dictionary.
    for file_report in files:
        for plugin_report in file_report["plugins"]:
            validate_plugin_report(plugin_report)  # again??
            plugin_name = plugin_report["plugin"]
            plugin_total = plugin_report["summary"]["issues_found"]
            total_issues += plugin_total
            issues_by_plugin.setdefault(plugin_name, 0)
            issues_by_plugin[plugin_name] += plugin_total
            for issue in plugin_report["results"]:
                severity = issue["severity"]
                issues_by_severity[severity] += 1

    # == Final Summary Computations ==

    # analyze the files data and generate a list of files or modules
    # with the highest concentration of issues.
    top_offenders = _compute_top_offenders(files)

    # analyze the files data and generate a list of files or modules
    # with the highest concentration of issues.
    overall_status = _derive_status(plugin_status)

    # == Building the Unified Report ==

    # Construct the final UnifiedReport dictionary, which is structured into
    # three main sections:
    # i.    analysis metadata: contextual information about the run.
    # ii.   summary: all the aggregated counts and calculated metrics.
    # iii.  details: contains the complete, raw list of per-file
    # analysis results (files).
    unified: UnifiedReport = {
        "analysis_metadata": {
            "timestamp": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "tool_version": __version__,
            "plugins_executed": list(plugin_status),
            "status": overall_status,
        },
        "summary": {
            "total_files": len(files),
            "total_issues": total_issues,
            "issues_by_severity": issues_by_severity,
            "issues_by_plugin": issues_by_plugin,
            "top_offenders": top_offenders,
        },
        "details": files,
    }
    # performs a final check on the complete report structure before it is returned.
    validate_unified_report(unified)

    # returns the consolidated analysis report
    return unified
