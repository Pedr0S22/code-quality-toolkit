import pytest

# Se o "radon" não estiver instalado (caso do job test_coverage),
# estes testes são marcados como "skipped" em vez de falharem na importação.
pytest.importorskip("radon")

from textwrap import dedent

from toolkit.plugins.basic_metrics.plugin import Plugin
from toolkit.utils.config import ToolkitConfig


# Código de exemplo para testar as métricas
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
    """
    Executa o plugin de basic_metrics sobre o código dado
    e devolve apenas o dicionário de métricas.

    Ajusta esta função se no teu plugin o caminho das métricas
    no relatório for diferente.
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    report = plugin.analyze(source, "test_file.py")

    # Em todos os plugins o contrato é:
    #   report: {"results": [...], "summary": {...}}
    summary = report["summary"]

    # Se no teu plugin as métricas estiverem aninhadas (ex.: summary["metrics"]),
    # elas são usadas; se não existirem, usamos o próprio summary como "metrics".
    metrics = summary.get("metrics", summary)

    return metrics

def test_number_of_lines() -> None:
    """
    Test number of lines (total de linhas do ficheiro).
    """
    metrics = _run_metrics(SAMPLE_CODE)

    # Ajusta "total_lines" se no teu plugin tiver outro nome (ex.: "loc")
    assert metrics["total_lines"] == 9

def test_blank_lines() -> None:
    """
    Test blank lines (linhas em branco).
    """
    metrics = _run_metrics(SAMPLE_CODE)

    # Ajusta "blank_lines" se o teu plugin usar outro nome.
    assert metrics["blank_lines"] == 3

def test_comment_lines() -> None:
    """
    Test comment lines (linhas de comentário).
    """
    metrics = _run_metrics(SAMPLE_CODE)
    

    # Ajusta "comment_lines" se necessário.
    assert metrics["comment_lines"] == 2

def test_docstring_lines() -> None:
    """
    Test docstring lines (linhas pertencentes a docstrings).
    """
    metrics = _run_metrics(SAMPLE_CODE)

    # Ajusta "docstring_lines" se usares outro nome ou lógica.
    assert metrics["docstring_lines"] == 2

def test_lines_of_code() -> None:
    """
    Test lines of code (LOC) – linhas de código "real".
    """
    metrics = _run_metrics(SAMPLE_CODE)
    print(metrics)

    # Ajusta "code_lines" se no teu plugin tiver outro nome (ex.: "sloc").
    assert metrics["logical_lines"] == 5

def test_metrics_on_empty_source() -> None:
    """
    Caso base: ficheiro vazio.
    Todas as métricas devem ser zero.
    """
    metrics = _run_metrics("")

    assert metrics["total_lines"] == 0
    assert metrics["blank_lines"] == 0
    assert metrics["comment_lines"] == 0
    assert metrics["docstring_lines"] == 0
    assert metrics["logical_lines"] == 0
