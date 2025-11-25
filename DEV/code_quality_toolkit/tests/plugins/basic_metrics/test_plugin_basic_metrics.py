import pytest
from textwrap import dedent

# Se não houver radon instalado, estes testes são "skipped" (para o job test_coverage)
pytest.importorskip("radon")

from toolkit.plugins.basic_metrics.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


SAMPLE_CODE = dedent(
    '''
    """Module docstring"""

    # Comment 1

    def foo():
        """Function docstring"""
        x = 1  # inline comment

        return x
    '''
).lstrip("\n")


def _run_metrics(source: str) -> dict:
    """Ajuda: corre o plugin e devolve só o dicionário de métricas."""
    plugin = Plugin()
    plugin.configure(ToolkitConfig())
    report = plugin.analyze(source, "test_file.py")

    summary = report["summary"]

    # ajusta esta linha se no teu plugin o nome da chave for outro
    metrics = summary.get("metrics", {})
    return metrics


def test_number_of_lines() -> None:
    """Test number of lines."""
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["total_lines"] == 9


def test_blank_lines() -> None:
    """Test blank lines."""
    metrics = _run_metrics(SAMPLE_CODE)
    assert metrics["blank_lines"] == 3  # linhas 2, 4 e 8


def test_comment_lines() -> None:
    """Test comment lines."""
    metrics = _run_metrics(SAMPLE_CODE)
    # comentário em linha inteira + comentário inline
    assert metrics["comment_lines"] == 2


def test_docstring_lines() -> None:
    """Test docstrings."""
    metrics = _run_metrics(SAMPLE_CODE)
    # 1 linha do docstring do módulo, 1 da função
    assert metrics["docstring_lines"] == 2


def test_lines_of_code() -> None:
    """Test lines of code (LOC)."""
    metrics = _run_metrics(SAMPLE_CODE)
    # def foo, linha com x = 1, linha do return
    assert metrics["code_lines"] == 3


def test_metrics_on_empty_source() -> None:
    """Caso base: ficheiro vazio -> tudo a zero."""
    metrics = _run_metrics("")
    assert metrics["total_lines"] == 0
    assert metrics["blank_lines"] == 0
    assert metrics["comment_lines"] == 0
    assert metrics["docstring_lines"] == 0
    assert metrics["code_lines"] == 0
