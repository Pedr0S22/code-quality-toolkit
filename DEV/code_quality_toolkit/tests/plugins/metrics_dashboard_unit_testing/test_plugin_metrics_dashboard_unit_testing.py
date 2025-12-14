from toolkit.plugins.metrics_dashboard_unit_testing.plugin import Plugin


def test_render_html():
    plugin = Plugin()
    results = {"test": "value"}
    html_output = plugin.render_html(results)
    assert isinstance(html_output, str)
    assert "test" in html_output


def test_generate_dashboard(tmp_path):
    plugin = Plugin()
    results = {"test": "value"}
    output_dir = str(tmp_path)
    plugin.generate_dashboard(results, output_dir)
    dashboard_file = tmp_path / "metrics_dashboard_unit_testing_dashboard.html"
    assert dashboard_file.exists()
    content = dashboard_file.read_text()
    assert "test" in content
