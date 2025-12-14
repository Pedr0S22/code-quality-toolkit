"""Tests unitarios para el dashboard de duplicación."""

import unittest
from unittest.mock import mock_open, patch

from duplication_dashboard import DuplicationDashboard


class TestDuplicationDashboard(unittest.TestCase):
    """Batería de pruebas para la clase DuplicationDashboard."""

    def setUp(self):
        """Configuración inicial de los tests."""
        self.dashboard = DuplicationDashboard()
        # Simulamos datos que cumplen con la estructura de 'contracts.py'
        self.sample_data = [
            {
                "file": "main.py",
                "plugins": [
                    {
                        "plugin": "DuplicationPlugin",
                        "summary": {"issues_found": 1, "status": "completed"},
                        "results": [
                            {
                                "severity": "medium",
                                "code": "DUP001",
                                "message": "Bloque duplicado detectado",
                                "line": 15,
                                "col": 0,
                            }
                        ],
                    }
                ],
            }
        ]

    def test_render_html_provides_expected_html(self):
        """Prueba que render_html genera el HTML con los datos correctos."""
        html = self.dashboard.render_html(self.sample_data)

        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("main.py", html)  # Verifica que aparece el nombre del archivo
        self.assertIn(":15", html)  # Verifica que aparece la línea
        self.assertIn("Bloque duplicado", html)  # Verifica el mensaje

    @patch("builtins.open", new_callable=mock_open)
    def test_gen_dashboard_creates_appropriate_file(self, mock_file):
        """Prueba que gen_dashboard intenta escribir en el archivo correcto."""
        filename = "reporte.html"

        self.dashboard.gen_dashboard(self.sample_data, filename)

        # Verifica que se abrió el archivo en modo escritura ('w')
        mock_file.assert_called_once_with(filename, "w", encoding="utf-8")
        # Verifica que se escribió algo
        mock_file().write.assert_called()


if __name__ == "__main__":
    unittest.main()