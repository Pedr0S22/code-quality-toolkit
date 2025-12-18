# User Documentation - Code Quality Toolkit Web UI

## USER GUIDE

The Code Quality Toolkit Web UI (Client application) provides a simple, fast, and accessible way for any user to execute code quality analyses without resorting to complex Command Line Interface (CLI) commands.

The application streamlines the entire analysis flow, from source code selection to final report visualization.

## How to Launch the Application

To start the graphical user interface (the Client) the server must be Running since the Web UI relies on a running FastAPI backend server.

- **Start the Client**: Run client.py using the command:

    ```txt
    make run_client
    ```

    The application will open a graphical interface that allows you to execute the entire analysis workflow.

## Analysis Workflow and Navigation

The user interface follows a straightforward, step-by-step process:

### 1. Initial Screen (UI Overview)

The initial screen presents the list of available plugins and the current operational status of the application.

### 2. Select Directory to Analyze

You must first select the source code to be analyzed. Use the file selection feature to choose the target file or folder that will be packaged and sent to the server.

### 3. Configure Plugins

The Client allows granular control over the analysis. You can:

Enable/Disable: Toggle the active status of each plugin.

Configure Settings: Adjust plugin-specific rules and thresholds before running the analysis.

### 4. Execute the Analysis

Once the directory is selected and plugins are configured, initiate the process:

- The Client automatically bundles the source code into a ZIP file.

- This package is securely transmitted to the backend server.

- The Client then waits for the results, which are returned as a results ZIP file.

- The Client extracts the results and automatically opens the final report.

### 5. Export the report

After the analysis, you can export the report using the export button. It will download a report.md file.

### 6. Report and Dashboards - Interpretation

After a successful analysis, the file report.html is automatically displayed in your app. To accesse the plugins dashboars, click on the eye icon. These interactive dashboards provides comprehensive results, including:

- **Global Metrics**: Summary statistics like the total number of files analyzed and the overall issue status (e.g., completed, partial, failed).

- **Severity Breakdown**: Visualizations showing the distribution of issues across severity levels (Info, Low, Medium, High).

- **Issues by Plugin**: Charts detailing how many problems each specific plugin detected.

- **Top Offenders**: A list highlighting the files that contain the highest number of detected issues.

- **Complete Issues Table**: A searchable and filterable table that lists every detected issue, allowing filtering by severity, plugin, and file path.

### Why Use This Interface?

The Web UI was developed to significantly improve the user experience for code analysis:

- **Simplification**: It removes the need to deal with complex command-line arguments and configuration files.

- **Efficiency**: It facilitates quick, repeatable analyses for rapid testing and iteration.

- **Clarity**: It provides a clear, visual report (the dashboard) for easy interpretation of complex code metrics.

- **Consistency**: It helps ensure consistent analysis execution across the entire development team.

## Common Issues and Troubleshooting

If you encounter problems, check the following:

- **Server Connection**: Ensure that the Toolkit's backend server is running and accessible before launching the Client UI.

- **File Permissions**: If report.html fails to open, check your local machine's file permissions, browser security settings, or antivirus software, which may block the automatic opening of local files.

## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21

#### Disclaimer: This web application component was build using AI.