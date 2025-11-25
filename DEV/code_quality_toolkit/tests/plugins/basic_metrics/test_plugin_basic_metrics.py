from textwrap import dedent

from toolkit.plugins.basic_metrics.plugin import (
    count_blank_lines,
    count_code_lines,
    count_comment_lines,
    count_docstring_lines,
    count_total_lines,
)


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


def test_number_of_lines() -> None:
    assert count_total_lines(SAMPLE_CODE) == 9


def test_blank_lines() -> None:
    assert count_blank_lines(SAMPLE_CODE) == 3  # linhas 2, 4 e 8


def test_comment_lines() -> None:
    assert count_comment_lines(SAMPLE_CODE) == 2  # linha 3 + inline na 7


def test_docstring_lines() -> None:
    assert count_docstring_lines(SAMPLE_CODE) == 2  # módulo + função


def test_lines_of_code() -> None:
    assert count_code_lines(SAMPLE_CODE) == 3  # def, x = 1, return


def test_metrics_on_empty_source() -> None:
    empty_source = ""
    assert count_total_lines(empty_source) == 0
    assert count_blank_lines(empty_source) == 0
    assert count_comment_lines(empty_source) == 0
    assert count_docstring_lines(empty_source) == 0
    assert count_code_lines(empty_source) == 0
