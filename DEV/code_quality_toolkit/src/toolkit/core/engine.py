"""Execution engine that runs plugins over target files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from ..plugins.base import BasePlugin
from ..utils import fs
from ..utils.config import ToolkitConfig
from . import logging
from .contracts import FileReport, validate_plugin_report

'''
This function is the core engine of the Code Quality Toolkit.
It orchestrates the process of file discovery, configuration setup, iterating through files, executing
all enabled plugins on each file's source code, handling errors during plugin execution,
and aggregating the final results.
'''
def run_analysis( root: str | Path, plugins: Dict[str, BasePlugin], config: ToolkitConfig,
) -> Tuple[List[FileReport], Dict[str, str]]:
    """Execute all plugins over files discovered under root."""

    # Iterate over all loaded plugins looking for a configuration setup
    for plugin in plugins.values():
        # If a plugin exposes a configure method (checked via hasattr),
        # that method is called, passing the global config object. This allows plugins to adjust their behavior
        # based on user settings (e.g., setting their internal max_line_length threshold).
        if hasattr(plugin, "configure"):
            plugin.configure(config)  # type: ignore[call-arg]

    # plugin_status is initialized: It's a dictionary used to track whether each plugin executed successfully
    # across all files. It defaults to "completed" for every plugin.
    plugin_status: Dict[str, str] = {name: "completed" for name in plugins}
    
    # initialize 'files' as an empty list that will store the detailed analysis results for every file scanned.
    files: List[FileReport] = []

    # == File discovery ==

    # Calls a utility (fs.discover_files) to locate all files that need analysis.
    # It starts searching from the root path and uses the include and exclude glob patterns 
    # defined in config.analyze to filter the file list.
    file_paths = fs.discover_files(root, config.analyze.include, config.analyze.exclude)
    logging.log("engine.files_discovered", count=len(file_paths)) # The total number of files found is logged.

    # == Main Analysis Loop (File Iteration) ==

    for file_path in file_paths:
        # For each file in the current file_path, the entire content is read into the source variable as a single string.
        # This is the code that will be passed to the plugins.
        source = file_path.read_text(encoding="utf-8")
        # plugin_reports is initialized to hold the results from every plugin for this specific file.
        plugin_reports = []

        # === Plugin Execution and Error Handling ===

        # This internal loop executes every loaded plugin on the current file's source code.
        for plugin_name, plugin in plugins.items():
            # Inside a try...except block, each plugin's main method (plugin.analyze) is called.
            try:
                report = plugin.analyze(source, str(file_path))
                # ensures the report structure returned by the plugin is correct
                # (e.g., contains the required keys and data types).
                validate_plugin_report(report)

            # If any exception occurs during the plugin's analysis:
            # - The failure is logged with the plugin name and file path.
            # - The plugin_status is set to "partial" for the failing plugin.
            # - A synthetic error report is created.
            except Exception as exc:  # noqa: BLE001 - convert to structured error
                logging.log("plugin.failure", plugin=plugin_name, file=str(file_path), error=str(exc))
                plugin_status[plugin_name] = "partial" # indicates it did not complete successfully for all files.
                report = {
                    # assign a high severity and a standardized PLUGIN_ERROR code. This ensures that 
                    # even a crashing plugin generates a structured report entry, preventing downstream 
                    # aggregation tools from failing, and informing the user of the crash within the final report.   
                    "results": [
                        {
                            "severity": "high",
                            "code": "PLUGIN_ERROR",
                            "message": f"Erro ao executar plugin: {exc}",
                            "line": 0,
                            "col": 0,
                            "hint": "Consulte os logs para detalhes.",
                        }
                    ],
                    "summary": {
                        "issues_found": 1,
                        "status": "failed",
                    },
                }
            
            # === Aggregation of results (per file) ===    
            plugin_reports.append(
                # per file: Each plugin's report (whether successful or synthetic error) is appended
                # to the plugin_reports list for the current file.
                {
                    "plugin": plugin_name,
                    "results": report["results"],
                    "summary": report["summary"],
                }
            )
        # After all plugins have run on a file, the entire list of plugin reports is wrapped with the file path
        # and added to the main files list.    
        files.append({"file": str(file_path), "plugins": plugin_reports})

    # analysis complete (all files x all plugins)

    # This function returns two distinct pieces of information:
    # - files: A detailed list of reports, structured by file.
    # - plugin_status: A dictionary summarizing the overall success status of each plugin.    
    return files, plugin_status


# TODO(alunos): suportar execução paralela de plugins ou cache incremental de resultados.
