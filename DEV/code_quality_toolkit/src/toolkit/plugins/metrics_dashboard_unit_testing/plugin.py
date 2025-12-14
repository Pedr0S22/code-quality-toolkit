from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader

JINJA_ENV = Environment(
    loader=PackageLoader("toolkit.plugins.basic_metrics", "templates")
)


class Plugin:
    def __init__(self):
        self.name = "metrics_dashboard_unit_testing"

    def get_metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": "1.0.0",
            "description": "Plugin for unit testing metrics dashboard"
            + "creation based on templates.",
            "dependencies": [],
        }

    def configure(self, config: dict[str, Any]) -> None:
        pass

    def render_html(self, results: dict[str, Any]) -> str:
        template = JINJA_ENV.get_template("dashboard.html")
        return template.render(results=results)

    def generate_dashboard(self, results: dict[str, Any], output_dir: str) -> None:
        html_content = self.render_html(results)
        output_path = Path(output_dir) / f"{self.name}_dashboard.html"
        output_path.write_text(html_content)

    def analyze(self, codebase_path: str, config: dict[str, Any]) -> dict[str, Any]:
        return {}
