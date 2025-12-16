from pathlib import Path
from textwrap import dedent

import pytest

# Importa as classes que precisamos testar e simular
from toolkit.plugins.comment_density.plugin import Plugin
from toolkit.utils.config import RulesConfig, ToolkitConfig


# --- Critério 8: Teste da API (Metadados) ---
def test_plugin_metadata():
    """Verifica se os metadados do plugin estão corretos."""
    plugin = Plugin()
    metadata = plugin.get_metadata()
    assert metadata["name"] == "CommentDensity"
    assert "description" in metadata


# --- Critérios 6 e 11: Teste da Configuração (RESTORED) ---
def test_plugin_configuration():
    """
    Verifica se o plugin lê corretamente a configuração personalizada
    do objeto ToolkitConfig.
    """
    plugin = Plugin()

    # Cria uma configuração simulada com as novas regras que adicionaste ao config.py
    custom_rules = RulesConfig(min_density=0.25, max_density=0.75)
    custom_config = ToolkitConfig(rules=custom_rules)

    # Configura o plugin
    plugin.configure(custom_config)

    # Verifica se os valores internos do plugin foram atualizados
    assert plugin.min_density == 0.25
    assert plugin.max_density == 0.75


# --- Critérios 1, 2, 3: Testes de Contagem de Linhas (Lógica Pura) ---
@pytest.mark.parametrize(
    "code_sample, expected_code_lines, expected_comment_lines",
    [
        # Cenário 1: Apenas código
        ("print('hello')\nvar = 1", 2, 0),
        # Cenário 2: Apenas comentários
        ("# Linha 1\n# Linha 2", 0, 2),
        # Cenário 3: Código com comentários inline
        ("x = 1 # Isto é um comentário inline", 1, 1),
        # Cenário 4: Apenas comentários (mas o # está no meio)
        ("    # Um comentário indentado", 0, 1),
        # Cenário 5: Linhas em branco (devem ser ignoradas)
        ("code1\n\n\ncode2\n\n# comment", 2, 1),
        # Cenário 6: Comentário multi-linha (docstring)
        (
            dedent(
                """
        \"\"\"
        Isto é uma docstring.
        \"\"\"
        print('hello')
    """
            ),
            1,
            3,
        ),
        # Cenário 7: Comentário multi-linha numa linha
        ('"""docstring de uma linha"""', 0, 1),
    ],
)
def test_count_lines_logic(code_sample, expected_code_lines, expected_comment_lines):
    """
    Testa a lógica interna _count_lines com diferentes cenários.
    """
    plugin = Plugin()
    code_lines, comment_lines = plugin._count_lines(code_sample)

    assert code_lines == expected_code_lines
    assert comment_lines == expected_comment_lines


# --- Critérios 4, 5, 7: Testes de Análise e Thresholds ---
def test_analyze_density_good():
    """
    Testa um ficheiro com densidade "boa" (dentro dos limites).
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())  # Usa a config padrão (10%-50%)

    code = dedent(
        """
        # Plugin de densidade
        # Teste
        print(1)
        print(2)
        print(3)
        print(4)
        print(5)
        print(6)
        print(7)
        print(8)
    """
    )
    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0
    # 2 linhas comment / 10 total = 0.20
    assert report["summary"]["metrics"]["comment_density"] == 0.20


def test_analyze_density_too_low():
    """
    Testa um ficheiro com densidade baixa (abaixo de 10%).
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    # 1 linha comentário, 10 linhas código -> ~9%
    code = "# Só um comentário\n" + "\n".join(["print(i)" for i in range(10)])
    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 1
    assert report["results"][0]["code"] == "LOW_COMMENT_DENSITY"
    assert "Low comment density" in report["results"][0]["message"]


def test_analyze_density_too_high():
    """
    Testa um ficheiro com densidade alta (acima de 50%).
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    # 6 linhas comentário, 4 linhas código -> 60%
    code = "# c1\n# c2\n# c3\n# c4\n# c5\n# c6\ncode1\ncode2\ncode3\ncode4"
    report = plugin.analyze(code, "test.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 1
    assert report["results"][0]["code"] == "HIGH_COMMENT_DENSITY"
    assert "High comment density" in report["results"][0]["message"]


# --- Critério 12: Teste de Tratamento de Erros ---
def test_analyze_syntax_error():
    """
    Testa se o plugin segue a "Golden Rule" e trata erros de sintaxe.
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

 
    broken_code = """
def bad_syntax(:
    print("linha 2 para encher linguiça")
    print("linha 3 para encher linguiça")
    print("linha 4 para encher linguiça")
    print("linha 5 para encher linguiça")
    print("linha 6 para encher linguiça")
    """

    report = plugin.analyze(broken_code, "test.py")

    # CORREÇÃO: Agora o plugin retorna "failed" quando há exceção, não "partial"
    assert report["summary"]["status"] == "failed"
    
    # Verifica se a mensagem de erro foi capturada
    assert report["summary"]["error"] is not None

# --- NOVOS TESTES DE ANÁLISE (LIMITE E COBERTURA) ---

def test_analyze_too_few_lines_skip():
    """
    Testa a lógica de 'early exit' quando há menos de 5 linhas não vazias.
    Cobre: if len(non_empty_lines) < 5.
    """
    plugin = Plugin()
    plugin.configure(ToolkitConfig())

    # 4 linhas não vazias (deve pular a análise de densidade)
    code = "# c1\ncode1\ncode2\ncode3"
    report = plugin.analyze(code, "small.py")

    assert report["summary"]["status"] == "completed"
    assert report["summary"]["issues_found"] == 0
    assert report["summary"]["metrics"]["total_lines"] == 4
    assert report["summary"]["metrics"]["comment_density"] == 0.0


def test_analyze_density_exactly_min():
    """
    Testa a densidade exatamente no limite mínimo (0.10, 10%).
    Deve passar sem issue.
    """
    plugin = Plugin()
    # Usando o default: min_density = 0.1
    plugin.configure(ToolkitConfig()) 

    # 1 comentário / 10 linhas totais -> 0.10
    code = "# C\n" + "\n".join([f"print({i})" for i in range(9)])
    report = plugin.analyze(code, "min_exact.py")

    assert report["summary"]["issues_found"] == 0
    assert f"{report['summary']['metrics']['comment_density']:.2f}" == "0.10"

# --- NOVOS TESTES DE AGREGAÇÃO (DASHBOARD) ---

def test_aggregate_dashboard_file_type_priority():
    """
    Verifica a agregação, garantindo que a regra de HIGH (HIGH_COMMENT_DENSITY)
    sobrescreva LOW (LOW_COMMENT_DENSITY) no contador de top_files.
    Cobre: files_counter update logic.
    """
    plugin = Plugin()
    aggregated_results = [
        {
            "file": "file_mixed.py",
            "plugins": [{
                "plugin": "CommentDensity",
                "results": [
                    # A: Low Density
                    {
                        "code": "LOW_COMMENT_DENSITY", 
                        "file": "file_mixed.py"
                    }, 
                    # B: High Density (DEVE SOBRESCREVER A)
                    {
                        "code": "HIGH_COMMENT_DENSITY", 
                        "file": "file_mixed.py"
                    },
                ]
            }]
        },
    ]

    dashboard_data = plugin._aggregate_data_for_dashboard(aggregated_results)

    # Verifica métricas
    assert dashboard_data["metrics"]["total_issues"] == 2
    assert dashboard_data["metrics"]["total_files"] == 1
    
    # Verifica o top_files: O tipo deve ser HIGH, não LOW
    top_file = dashboard_data["top_files"][0]
    assert top_file["file"] == "file_mixed.py"
    assert top_file["count"] == 2
    assert top_file["type"] == "HIGH_COMMENT_DENSITY" # Prioridade do HIGH

# --- TESTES DE EXCEÇÃO (COBERTURA DO EXCEPT) ---



def test_generate_dashboard_exception_handling(tmp_path: Path):
    """
    Cobre o bloco 'except Exception as e' no método generate_dashboard,
    forçando uma falha de I/O ao tentar escrever em um diretório.
    """
    plugin = Plugin()

    # Simulação mínima de resultados
    aggregated_results = [{
        "file": "f.py", 
        "plugins": [{
            "plugin": "CommentDensity", 
            "results": [
                {"code": "LOW_COMMENT_DENSITY", "file": "f.py"}
            ]
        }]
    }]

    # Usamos o caminho de um diretório (tmp_path), o que forçará o erro
    output_path = plugin.generate_dashboard(aggregated_results, str(tmp_path))

    # A função deve capturar a exceção e retornar uma string vazia
    assert output_path == ""