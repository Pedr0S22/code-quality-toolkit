## Core – Technical Documentation
## Component Name
core

## Version
0.1.0

## Authors
Alfonso Pintado Gracia 2025175710 @alfooonsoo17
Carlos Lomelín Valdés 2025154763 @carloslomelinv
Miguel Pedro Rodrigues Carvalho 2023216436 @parzival3301
Samuel Gomes Esteban 2025178876 @samuugomes
Mathias Gustavo Welz 2025167903 @mathiasgwelz

## ---USER GUIDE---
## What the Core Does
The core module is the heart of the Code Quality Toolkit. It coordinates everything required to analyze a project:

- Loads and validates plugins
- Discovers files to analyze
- Runs all plugins safely
- Aggregates results into a unified report
- Applies severity-based exit logic
- Produces structured logs
- Ensures fault isolation and predictable CLI behavior

The system is designed so that no plugin crash or internal error can stop the analysis.

## How Users Interact With It
Users interact with the core exclusively through the command line:

toolkit analyze <path> [options]

The core will:

1. Load configuration (default or custom toolkit.toml)
2. Discover and load the requested plugins
3. Discover files based on include/exclude patterns
4. Run the engine to analyze each file with each plugin
5. Aggregate results and generate report.json
6. Apply severity-based exit checks
7. Return a meaningful exit code

## Key CLI Options
- --plugins name1,name2 — Select specific plugins
- --include-glob / --exclude-glob — File filtering
- --config — Use a custom configuration file
- --fail-on-severity — Fail on issues of a given severity or higher
- --log-level / --verbose — Control structured logging output
- --out — Choose the output JSON file path

## What You’ll See When Running the Core
- Predictable exit codes
- JSON-based logs
- A complete report.json with all aggregated plugin results
- Synthetic PLUGIN_ERROR entries when a plugin crashes
- No Python traceback unless an unmanaged internal failure occurs

## Summary
The core manages the complete plugin lifecycle, file discovery, analysis execution, logging, error handling, report generation, and CLI behavior.
Users only run the CLI; the core handles everything else reliably.

## ---TECHNICAL DOCUMENTATION---
## Description
The core module provides the infrastructure required to perform static analysis using dynamically loaded plugins.
It ensures robustness using strict validation, structured exceptions, and controlled plugin execution.

The module includes:
- cli.py — CLI command parsing and main entry point
- loader.py — Plugin discovery, import, validation, and instantiation
- engine.py — File discovery, plugin execution, and safe error capture
- aggregator.py — Unified report building
- contracts.py — Data definitions and runtime report validation
- logging.py — Structured JSON logging
- errors.py — Exception classes

## 1. Core Responsibilities
The core performs:
1. CLI parsing
2. Configuration loading
3. Plugin discovery and loading
4. File discovery
5. Plugin execution (safe and isolated)
6. Error capture and synthetic report generation
7. Aggregation of all results
8. Report creation and validation
9. Exit code decision

No plugin or unexpected error is allowed to crash the system.

## 2. Architecture Overview
Execution Pipeline:

CLI → Load Config → Load Plugins → Discover Files → Engine (run plugins) → Aggregator → report.json → Exit Code Decision → Exit

Fault Isolation Rules:
- Each plugin is executed inside a try/except block
- Crashes produce PLUGIN_ERROR entries
- plugin_status is tracked (completed, partial, failed)
- Unified report is always valid

## 3. Module Breakdown

### 3.1. cli.py – Command Line Interface
Responsibilities:
- Argument parsing (argparse)
- Resolving requested plugins
- Configuring logging
- Running the engine
- Generating report.json
- Applying severity threshold logic
- Mapping errors to proper exit codes

Exit Codes:
- 0  -> Success
- 1  -> Managed error (config error, plugin load error…)
- 2  -> Unexpected internal error
- 3  -> Severity threshold violated

### 3.2. loader.py – Plugin Discovery & Validation
Handles:

Discovery:
Plugins must follow the structure:

toolkit/plugins/<package_name>/plugin.py

Importing:
Uses importlib to load modules dynamically.
Execution failures raise PluginLoadError.

Instantiation & Validation:
- Plugin must provide a Plugin attribute
- May be a class (instantiated) or an already-created object
- Plugin must implement:
  - get_metadata()
  - analyze()

Metadata Requirements:
name, version, description must be:
- present
- non-empty

Duplicates cause PluginValidationError.

### 3.3. engine.py – Execution Engine
Workflow:
1. Configure plugins (plugin.configure(config))
2. Discover files using include/exclude patterns
3. For each file:
   - read its source
   - run each plugin within try/except
   - on crash:
     - log plugin.failure
     - mark plugin partial
     - create synthetic PLUGIN_ERROR result

4. Build per-file FileReport entries
5. Return (files, plugin_status)

Ensures no plugin crash stops analysis.

### 3.4. aggregator.py – Building the Unified Report
Produces the final UnifiedReport:

- Metadata (timestamp, version, status, plugins executed)
- Summary statistics:
  - total files
  - total issues
  - issues by severity
  - issues by plugin
  - top offenders

Status derivation:
- completed
- partial
- failed

Validated with validate_unified_report().

### 3.5. contracts.py – Types & Validation
Defines schemas:
- PluginMetadata
- IssueResult
- PluginExecutionResult
- FileReport
- UnifiedSummary
- UnifiedMetadata
- UnifiedReport

Includes validation:
- validate_plugin_report()
- validate_unified_report()

### 3.6. errors.py – Exception Hierarchy
Defines:
- ToolkitError (base)
- PluginLoadError
- PluginValidationError
- ConfigurationError
- AnalysisExecutionError

### 3.7. logging.py – Structured JSON Logging
Provides:
- set_log_level(level_name)
- log(event, level, **payload)

Output example:
{"event": "plugin.loaded", "plugin": "StyleChecker", "module": "..."}

## 4. Data Flow Summary
1. Plugins discovered and validated
2. Files discovered
3. Plugins executed sequentially
4. Errors converted into PLUGIN_ERROR
5. Aggregator consolidates statistics
6. Unified report validated
7. CLI writes output JSON
8. Exit code resolved

## 5. Conclusion
The core module is a robust, fault-tolerant analysis engine designed to support dynamically loaded plugins safely.
It guarantees consistent reporting, stable behavior under failures, strict contract validation, clean logs, and predictable results.