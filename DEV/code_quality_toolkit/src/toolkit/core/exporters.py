"""Export utilities for the Unified Report."""

from __future__ import annotations

import html
from .contracts import UnifiedReport

def generate_html(report: UnifiedReport) -> str:
    """
    Gera um HTML estrutural mostrando TODOS os plugins executados.
    """
    
    metadata = report["analysis_metadata"]
    summary = report["summary"]
    details = report["details"]

    # Início do HTML
    output = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Code Quality Report</title>
</head>
<body>
    <h1>Code Quality Toolkit Report</h1>
"""

    # --- 1. Metadata ---
    output += """
    <h2>Analysis Metadata</h2>
    <ul>
    """
    output += f"<li><strong>Timestamp:</strong> {metadata['timestamp']}</li>"
    output += f"<li><strong>Tool Version:</strong> {metadata['tool_version']}</li>"
    output += f"<li><strong>Status:</strong> {metadata['status']}</li>"
    output += f"<li><strong>Plugins Executed:</strong> {', '.join(metadata['plugins_executed'])}</li>"
    output += "</ul>"
    output += "<hr>"

    # --- 2. Summary ---
    output += """
    <h2>Summary</h2>
    
    <h3>Totals</h3>
    <ul>
    """
    output += f"<li><strong>Total Files:</strong> {summary['total_files']}</li>"
    output += f"<li><strong>Total Issues:</strong> {summary['total_issues']}</li>"
    output += "</ul>"

    output += "<h3>Issues by Severity</h3><ul>"
    for sev, count in summary['issues_by_severity'].items():
        output += f"<li>{sev}: {count}</li>"
    output += "</ul>"

    output += "<h3>Issues by Plugin</h3><ul>"
    for plugin, count in summary['issues_by_plugin'].items():
        output += f"<li>{plugin}: {count}</li>"
    output += "</ul>"

    # Top Offenders
    output += "<h3>Top Offenders</h3>"
    if not summary['top_offenders']:
        output += "<p>None</p>"
    else:
        output += "<ul>"
        for offender in summary['top_offenders']:
            output += f"<li><strong>{offender['file']}</strong>: {offender['issues']} issues</li>"
        output += "</ul>"
    
    output += "<hr>"

    # --- 3. Details ---
    output += """
    <h2>Details</h2>
    """
    
    if not details:
        output += "<p>No details available.</p>"

    for file_report in details:
        output += f"<h3>File: {file_report['file']}</h3>"
        
        # AGORA: Mostra sempre todos os plugins, sem filtrar
        for plugin_run in file_report['plugins']:
            plugin_name = plugin_run['plugin']
            p_summary = plugin_run['summary']
            results = plugin_run['results']
            
            output += f"<h4>Plugin: {plugin_name}</h4>"
            
            # Dados do plugin
            output += "<ul>"
            output += f"<li>Status: {p_summary['status']}</li>"
            output += f"<li>Issues Found: {p_summary['issues_found']}</li>"
            
            # Métricas (se existirem)
            if 'metrics' in p_summary and p_summary['metrics']:
                metrics_str = ", ".join([f"{k}={v}" for k, v in p_summary['metrics'].items()])
                output += f"<li>Metrics: {metrics_str}</li>"
            
            # Erros de execução
            if 'error' in p_summary:
                output += f"<li>Error: {p_summary['error']}</li>"
            output += "</ul>"

            # Lista de Problemas
            if results:
                output += "<ul>"
                for issue in results:
                    sev = issue.get('severity', '')
                    code = issue.get('code', '')
                    msg = html.escape(issue.get('message', ''))
                    line = issue.get('line', '?')
                    col = issue.get('col', '?')
                    hint = html.escape(issue.get('hint', ''))

                    output += f"""
                    <li>
                        <strong>[{sev.upper()}]</strong> [{code}] {msg} 
                        (Line {line}, Col {col}) 
                        <br><em>Hint: {hint}</em>
                    </li>
                    """
                output += "</ul>"
            else:
                # Mensagem explícita quando não há problemas
                output += "<p><em>No issues found.</em></p>"

        output += "<hr>"

    output += """
</body>
</html>
"""
    return output