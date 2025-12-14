# Dashboard Plugin - Visualizes dependency graphs
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Plugin:
    """
    Dashboard de Visualização de Dependências: Gera visualizações HTML
    interativas dos grafos de dependências.
    """

    def __init__(self) -> None:
        """Inicializa o plugin com configurações padrão."""
        self.output_format = "html"
        self.show_stdlib = True
        self.color_by_category = True

    def get_metadata(self) -> dict[str, str]:
        """Devolve metadados do plugin."""
        return {
            "name": "DependencyDashboard",
            "version": "1.0.0",
            "description": (
                "Gera visualizações HTML interativas de grafos de dependências"
            ),
        }

    def configure(self, config) -> None:
        """Configura o plugin."""
        if hasattr(config, "rules"):
            if hasattr(config.rules, "dashboard_output_format"):
                self.output_format = config.rules.dashboard_output_format
            if hasattr(config.rules, "dashboard_show_stdlib"):
                self.show_stdlib = config.rules.dashboard_show_stdlib
            if hasattr(config.rules, "dashboard_color_by_category"):
                self.color_by_category = config.rules.dashboard_color_by_category

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Este plugin não analisa código diretamente.
        Use generate_dashboard() com dados do DependencyGraph.
        """
        return {
            "results": [],
            "summary": {
                "status": "completed",
                "message": "Use generate_dashboard() com dados do DependencyGraph",
            },
        }

    def generate_dashboard(
        self,
        dependency_data: dict[str, Any],
        output_path: str = "dependency_dashboard.html",
    ) -> str:
        """
        Gera um dashboard HTML interativo a partir dos dados de dependências.

        Args:
            dependency_data: Output do DependencyGraph plugin
            output_path: Caminho para salvar o HTML

        Returns:
            Caminho do ficheiro gerado
        """
        try:
            graph_data = dependency_data.get("summary", {}).get(
                "dependency_graph", {}
            )
            summary = dependency_data.get("summary", {})

            html_content = self._generate_html(graph_data, summary)

            output_file = Path(output_path)
            output_file.write_text(html_content, encoding="utf-8")

            return str(output_file.absolute())

        except Exception as e:
            raise RuntimeError(f"Erro ao gerar dashboard: {str(e)}") from e

    def _generate_html(self, graph_data: dict, summary: dict) -> str:
        """Gera o conteúdo HTML do dashboard."""
        stats = self._generate_stats_html(summary)
        categories = graph_data.get("categories", {})

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dependency Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
        }}
        h1 {{ color: #333; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
        }}
        .stat-value {{ font-size: 32px; font-weight: bold; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .modules-list {{ margin-top: 30px; }}
        .category {{ margin-bottom: 20px; }}
        .category-title {{
            font-weight: bold;
            padding: 10px;
            background: #eee;
            border-radius: 5px;
        }}
        .module-item {{
            padding: 8px;
            margin: 5px 0;
            background: #f9f9f9;
            border-left: 3px solid #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Dependency Graph Dashboard</h1>
        <div class="stats">{stats}</div>
        <div class="modules-list">
            <h2>Módulos por Categoria</h2>
            {self._generate_categories_html(categories)}
        </div>
    </div>
</body>
</html>"""

    def _get_node_category(self, node: str, categories: dict) -> str:
        """Determina a categoria de um nó."""
        for cat, modules in categories.items():
            if node in modules:
                return cat
        return "unknown"

    def _generate_stats_html(self, summary: dict) -> str:
        """Gera HTML das estatísticas."""
        return f"""
            <div class="stat-card">
                <div class="stat-label">Total Imports</div>
                <div class="stat-value">{summary.get('total_imports', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Módulos Únicos</div>
                <div class="stat-value">{summary.get('unique_modules', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Wildcard Imports</div>
                <div class="stat-value">{summary.get('wildcard_imports', 0)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Relative Imports</div>
                <div class="stat-value">{summary.get('relative_imports', 0)}</div>
            </div>
        """

    def _generate_categories_html(self, categories: dict) -> str:
        """Gera HTML das categorias."""
        html = ""
        colors = {
            "stdlib": "#48bb78",
            "third_party": "#4299e1",
            "local": "#ed8936",
        }

        for cat, modules in categories.items():
            color = colors.get(cat, "#666")
            module_items = "".join(
                f'<div class="module-item">{m}</div>' for m in sorted(modules)
            )
            html += f"""
            <div class="category">
                <div class="category-title" style="border-left: 4px solid {color};">
                    {cat.upper()} ({len(modules)} módulos)
                </div>
                <div>
                    {module_items}
                </div>
            </div>
            """

        return html