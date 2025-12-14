"""Módulo para generar el dashboard de duplicación."""


class DuplicationDashboard:
    """Clase encargada de renderizar reportes de duplicación."""

    def render_html(self, files_report):
        """
        Genera un reporte HTML simple a partir de los datos de duplicación.
        Recibe una lista de reportes de archivo (FileReport).
        """
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head><title>Reporte de Duplicación</title></head>",
            "<body>",
            "<h1>Resultados de Duplicación</h1>",
            "<ul>",
        ]

        # Recorremos cada archivo analizado
        for file_entry in files_report:
            file_name = file_entry.get("file", "Desconocido")

            # Buscamos los resultados de los plugins dentro de este archivo
            plugins = file_entry.get("plugins", [])
            for plugin_result in plugins:
                # Opcional: Filtramos para procesar solo nuestro plugin
                # if plugin_result.get("plugin") != "DuplicationPlugin": continue

                issues = plugin_result.get("results", [])
                for issue in issues:
                    severity = issue.get("severity", "info")
                    message = issue.get("message", "")
                    line = issue.get("line", "?")

                    # Creamos el elemento de lista para el HTML
                    html_lines.append(
                        f"<li class='{severity}'>[{file_name}:{line}] {message}</li>"
                    )

        html_lines.append("</ul>")
        html_lines.append("</body>")
        html_lines.append("</html>")

        return "\n".join(html_lines)

    def gen_dashboard(self, data, output_filename):
        """Genera el HTML y lo guarda en el archivo especificado."""
        html_content = self.render_html(data)
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_content)