# Dashboard Generation Documentation

### DEVELOPER GUIDE

This guide explains how to implement the mandatory dashboard for each plugin in the Toolkit. By following these guidelines, we ensure that every plugin provides independent, consistent, and high-quality visualizations integrated into the final report.

## Dashboard Standards

Each plugin must generate its own dashboard using the D3.js framework. This ensures dynamic and interactive visualizations consistent across the entire toolkit.

## Mandatory Specifications

- **Framework**: D3.js (Version 7+ recommended)

- **Dimensions**: Strictly max `1066 x 628` px

- **Filename Format**: `<plugin_name>_dashboard.html` (**NOTE that plugin_name must be in snake_case**)

- **Output Location**: `src/toolkit/plugins/<plugin_name>/`

## TECHNICAL IMPLEMENTATION

### Description

The dashboard generation process must occur during the plugin's analysis phase. The plugin is responsible for compiling its results and injecting them into a structured HTML file.

### 1. Integration Workflow

The generation logic should be triggered inside the main `analyze()` method of your plugin class.

**Analyze**: Perform the static analysis of the source code.

**Collect Data**: Gather results (issues, metrics).

**Generate**: Call the helper function to create the HTML file.

```python
def analyze(self, source_code, file_path):
    # ... analysis logic ...
    
    # Generate the dashboard at the end of analysis
    self.generate_dashboard(results, output_dir)
```


### 2. Required Data

To create a useful dashboard, your plugin must pass the following data dictionary to the frontend (HTML):

- Total number of issues

- Severity counts (e.g., High, Medium, Low)

- Affected files list

- Plugin-specific metrics

### 3. Recommended Helper Function

It is strongly suggested to implement a helper function generate_dashboard() within your plugin class to handle the file writing and HTML generation.

```python
def generate_dashboard(self, results, output_dir):
    """
    Generates the D3.js dashboard HTML file.
    """
    dashboard_file = output_dir / f"{self.name}_dashboard.html"
    
    # In a real scenario, use a template engine or formatted string
    html_content = self.build_html(results)
    
    dashboard_file.write_text(html_content, encoding="utf-8")
```

### 4. HTML & D3.js Structure

Below is the standard boilerplate for the dashboard. It includes the D3.js library and sets up the SVG canvas with the mandatory dimensions.

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="[https://d3js.org/d3.v7.min.js](https://d3js.org/d3.v7.min.js)"></script>
    <title>Plugin Dashboard</title>
    <style>
        body { font-family: sans-serif; margin: 0; padding: 20px; }
        .chart-container { width: 1066px; height: 628px; border: 1px solid #ddd; }
    </style>
</head>
<body>

<!-- Main App Container -->
<div id="app" class="chart-container"></div>

<script>
    // Data injected from Python
    const data = {{DATA_JSON}};

    // Initialize SVG with mandatory dimensions
    const svg = d3.select("#app")
        .append("svg")
        .attr("width", 1066)
        .attr("height", 628);

    // Example: Simple Bar Chart for Severities
    // This is just a placeholder logic
    if (data.severity_counts) {
        svg.selectAll("rect")
            .data(data.severity_counts)
            .enter()
            .append("rect")
            .attr("x", (d, i) => i * 100 + 50)
            .attr("y", d => 600 - d.count * 10)
            .attr("width", 80)
            .attr("height", d => d.count * 10)
            .attr("fill", "steelblue");
    }
</script>

</body>
</html>
```

### 5. UML-Based Dashboard Example

Below are the dashboard examples from SPEC.md. It's recommended to read this documentation in as a complement to this document.

```txt
+-----------------------------------------------------------+
| Dashboard                                                 |
+-------------------+------------------+--------------------+
| Total Files: 10   | Total Issues: 24 | Status: completed  |
+-------------------+------------------+--------------------+
| Severity Counts: info=5 low=10 medium=6 high=3            |
| Plugin Issues: StyleChecker=14 Cyclomatic=10              |
+-----------------------------------------------------------+
| Top Offenders                                            |
| 1. src/app.py (6)                                        |
| 2. src/utils.py (4)                                      |
+-----------------------------------------------------------+

+-----------------------------------------------------------+
| Issues Table                                              |
+-----------------------------------------------------------+
| Filters: [Plugin v] [Severity v] [Search ____]            |
|-----------------------------------------------------------|
| File           | Plugin     | Sev | Code     | Line | Msg |
|-----------------------------------------------------------|
| src/app.py     | StyleCheck | low | LINE_LEN |  45  | ... |
| src/utils.py   | Cyclomatic | med | HIGH_C   |  22  | ... |
+-----------------------------------------------------------+
```

## Authors
Pedro Silva, 2023235452, @Pedr0S22

André Silva, 2023212648, @andresilva219

Oleksandra Grymalyuk, 2023218767, @my3007sunshine

Rabia Saygin, 2024187186, @rferyals

Isaque Capra, 2023221892, @Isaque_capra

Tiago Alves, 2023207875, @tiagoalves.21
