# Code Quality Toolkit

## Project Overview & Goals
The Code Quality Toolkit is a modular software framework designed to perform python code quality checks on the given files. Operating as a Minimum Viable Product (MVP), it is a plugin-based analysis engine capable of producing unified code quality reports in JSON format. These reports can be consumed by both a Command Line Interface and a lightweight Web User Interface.

The primary goal of this project is to practice modular software design and interface-driven development and understanding the standards of software and team planning and management. The system emphasizes a robust software architecture that allows developers to add new plugins seamlessly without modifying the core system.

## Table of Contents
- [Project Structure](#project-structure)
- [Repository]()
- [Architecture](#architecture)
- [Plugin Lifecycle](#plugin-lifecycle)
- [Installation](#installation)
- [Usage & User Guide](#usage--user-guide)
- [Additional Documentation](#additional-documentation)
- [License](#license)
- [Authors](#authors)

## Project Structure

The toolkit is organized into three main directories to separate the implementation of the backend, the frontend (UI)  and the tests. Consider the folder `DEV/` or `DEP/`.

- `code_quality_toolkit/src/`: Backend of the system.
- `code_quality_toolkit/web/`: Interface of the system.
- `code_quality_toolkit/tests/`: unit and integration tests of the system.

The backend has 3 other sub-directories that distiguishes the core engine from external plugins and shared utilities:

- `code_quality_toolkit/src/toolkit/core/`: Engine infrastructure and CLI.
- `code_quality_toolkit/src/toolkit/plugins/`: Dynamically discover plugins to add to the system.
- `code_quality_toolkit/src/toolkit/utils/`: Shared utilities like configuration and file system helpers.

## Repository & CI/CD

This project originally was made and maintained in GitLab. This is the last snapshot of the project with additional Documentation. It was used a `GitLab CI/CD` and, of course, it can't be used here in GitHub. The `CI` pipeline tested the unit and integration tests coverage (> 70%), the quality of the code - the lint and the cyclomatic complexity - and the security.

## Architecture

The system is divided into a **Core System** (responsible for orchestrating execution, managing plugins, and aggregating results) and independent **Plugins** (each implementing a discrete analysis).

The toolkit features a robust error-handling architecture designed for resilience:
- **CLI Layer (`cli.py`):** Acts as the external defense line, managing expected operational errors (terminating with exit code `1`) and intercepting unexpected crashes (terminating with exit code `2`).
- **Analysis Engine Layer (`engine.py`):** Isolates plugin execution using `try...except` blocks. If a plugin fails, the engine logs the error, flags the plugin as `"partial"`, generates a synthetic error report, and safely continues executing the remaining plugins and files.

After the plugins analysis, the system generate a `unified report` containing a global summary alongside detailed results per file and per plugin and, using the app, it is possible to download the report as a `report.md` file. Also, while using the app, the user have acess to plugins report summarized in unique `dashboards` to make analysis easier for the user.

> For a deep dive into the architecture and core interactions, please see our [Architecture Documentation](ARCH/README.md).


## Plugins

### Plugins Available

The plugins of this toolkit that are available at the moment are:
- Basic Metrics
- Comment Density
- Cyclomatic Complexity
- Dead Code Detector
- Dependency Graph
- Duplication Checker
- Linter Wrapper
- Security Checker
- Style Checker

For further plugin availability, visit the plugins documentantation [here].

### Plugin Lifecycle

The core system handles plugins through a standardized lifecycle:

1. **Discovery:** The core dynamically scans the `src/toolkit/plugins` directory to identify plugin modules.
2. **Loading:** Modules are imported dynamically and validated against the `BasePlugin` metadata contract (interface).
3. **Execution:** The engine configures and runs the `analyze()` function for each discovered file.
4. **Aggregation:** Results are consolidated into a unified report, calculating metrics and identifying top offenders.
5. **CLI Integration:** The CLI/backend orchestrates this flow to output the final statistics and JSON file and the dashboards for the app.


## Installation

To set up the project quickly, run:

```bash
make setup
```

This command creates a `.venv` virtual environment and installs all required dependencies.

## Usage & User Guide

This guide describes how to use the Code Quality Toolkit to analyze python projects, configure options, and interpret the results.

### 1. Running an Analysis via CLI

You can quickly run the default analysis using:
```bash
make run
```

Or, to start an analysis manually, use the `analyze` command via the CLI in the root folder `code_quality_toolkit`:

```bash
python -m toolkit.core.cli analyze <path_to_analyze> [options]
```

Then, after the analysis is complete, there will be a report.json to be analysed. See section [HERE]() to know how this report is structured.

### 1.1. CLI Options

You can customize the execution using the following arguments:

| Option | Description | Example |
| :--- | :--- | :--- |
| `--plugins` | Defines which plugins to execute (comma-separated). Default is `all`. | `--plugins StyleChecker,CyclomaticComplexity` |
| `--out` | Defines the output path for the JSON report. | `--out results.json` |
| `--include-glob` | File pattern to include. Can be repeated. | `--include-glob "**/*.py"` |
| `--exclude-glob` | File pattern to ignore (e.g., tests). Can be repeated. | `--exclude-glob "tests/**"` |
| `--fail-on-severity` | Defines a severity level that will cause the tool to fail (exit code > 0). | `--fail-on-severity high` |
| `--log-level` | Defines log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `--log-level DEBUG` |
| `-v, --verbose` | Shortcut to activate debug logs (equivalent to `--log-level DEBUG`). | `-v` |

### 1.2. Integration Testing (CLI Failure Modes)

The CLI executable is designed to fail gracefully from a user's perspective. Automated tests ensure the CLI exits with the correct, non-zero error codes (e.g., `EXIT_MANAGED_ERROR`) when a plugin fails to load or run. The final `report.json` will still be generated successfully, displaying a `"partial"` status to indicate the interrupted plugin, ensuring no overall data loss.

### 2. Running Analysis Using the Web App

To use the Web App interface, both the backend server and the frontend client must be running. At the root folder `code_quality_toolkit`:

1. **Run the Server:** Start `server.py` using:
   ```bash
   make run_server
   ```
2. **Run the Client App:** Start `client.py` using:
   ```bash
   make run_client
   ```

A GUI will open, allowing you to select desired plugins and settings. Simply insert the file or folder to be analyzed and click **"Run analysis"**. Once the backend processes the data, you will immediately receive the report. The app will display interactive dashboards showcasing the errors, tips, and metrics exclusively for the plugins you selected.

### 3. Interpreting the Report & Dashboards

Reports are saved by default as `report.json`, containing a global summary alongside detailed results per file and per plugin and, using the app, it is possible to download the report as a `report.md` file.

While using the app, beside the `report`, the user can ..

The final report is a JSON file divided into three main sections:

- **`analysis_metadata`:** Information about the execution (date, version, executed plugins).
  - *Note on `partial` status:* If the `status` field is `"partial"`, it means **one or more plugins failed**, but the analysis continued for the remaining ones. Check the details section for specific errors.
- **`summary`:** Global statistics (total issues found, issue count by severity).
- **`details`:** A detailed list of all findings, grouped by file and plugin.

## Additional Documentation and Informations

See more Documentation (User and Developer) in the following folders:
- > Check the [User Documentation](PROD/README.md) for further details of the app, plugins and report analysis.
- > For a deep dive into the architecture and core interactions, please see our [Architecture Documentation](ARCH/README.md).
- > Verify the [`Specifications`](DEP/code_quality_toolkit/web/SPEC.md) of the Web interface consuming the `report.json`.
- > See how the developer can build a [New Plugin](DEP/code_quality_toolkit/src/toolkit/plugins/README.md) and how it can be discovered by the core system.
- > Also, see how the developer can build a [New Dashboard](DEP/code_quality_toolkit/src/toolkit/plugins/DASHBOARD.md) for a new plugin.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors
- Pedro Silva - *Project Lead / Maintainer*
- Mathias Welz - *Project Lead / Maintainer*
- ES 2025 TEAM
- See the other members [HERE](PM/profiles/)