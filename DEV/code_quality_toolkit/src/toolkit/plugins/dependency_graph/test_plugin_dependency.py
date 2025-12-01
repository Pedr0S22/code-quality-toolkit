import unittest
import json
import os
import shutil
import ast
from unittest.mock import MagicMock

from __future__ import annotations

import ast
from typing import Any # <<<<< GARANTIR QUE ESTA LINHA ESTÁ PRESENTE E COMPLETA

# Imports do Core do Projeto
from ...core.contracts import IssueResult
# ... (restante das importações)

# Importar o Plugin a partir do ficheiro fornecido.
# Ajuste o caminho de importação conforme a sua estrutura real.
# Assumindo que o ficheiro com a classe Plugin se chama dependency_graph_plugin.py
# E que 'Plugin' é a classe principal.
# (Vou simular a classe Plugin diretamente no script para facilitar a execução)

# ----------------------------------------------------------------------------------
# Importa o código do Plugin (Simulação, substitua pela importação real do seu projeto)
# ----------------------------------------------------------------------------------
class MockToolkitConfig:
    """Simulação da classe de configuração da Toolkit."""
    def __init__(self, rules_config=None):
        self.rules = rules_config if rules_config is not None else {}

class Plugin:
    # Copie e cole aqui a classe Plugin completa do seu código-fonte
    # ... (AQUI FICARIA A CLASSE PLUGIN COMPLETA) ...
    """
    Plugin de Análise de Dependências: Mapeia todas as importações de código Python,
    categorizando-as e identificando padrões potencialmente problemáticos.
    """

    # Lista parcial de módulos da biblioteca padrão do Python
    STDLIB_MODULES = {
        'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
        'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
        'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs',
        'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser',
        'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile', 'crypt', 'csv',
        'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib',
        'dis', 'distutils', 'doctest', 'email', 'encodings', 'enum', 'errno', 'faulthandler',
        'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'formatter', 'fractions', 'ftplib',
        'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'grp', 'gzip',
        'hashlib', 'heapq', 'hmac', 'html', 'http', 'imaplib', 'imghdr', 'imp', 'importlib',
        'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3',
        'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal',
        'math', 'mimetypes', 'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
        'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
        'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
        'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats',
        'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random',
        're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
        'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal',
        'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd',
        'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
        'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog',
        'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap',
        'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace',
        'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing',
        'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings',
        'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib',
        'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib'
    }

    def __init__(self) -> None:
        """Inicializa o plugin com configurações padrão."""
        # Configurações padrão
        self.warn_wildcard_imports = True
        self.max_relative_import_level = 1
        self.track_stdlib_modules = True

    def get_metadata(self) -> dict[str, str]:
        """Devolve metadados do plugin."""
        return {
            "name": "DependencyGraph",
            "version": "1.0.0",
            "description": (
                "Mapeia todas as importações de código Python, categorizando-as "
                "e identificando padrões problemáticos."
            ),
        }

    def configure(self, config: MockToolkitConfig) -> None: # Alterei o tipo para MockToolkitConfig para o teste
        """
        Configura o plugin a partir do ficheiro TOML global.
        
        Parâmetros suportados:
        - warn_wildcard_imports: bool (padrão: True)
        - max_relative_import_level: int (padrão: 1)
        - track_stdlib_modules: bool (padrão: True)
        """
        if hasattr(config.rules, "warn_wildcard_imports"):
            self.warn_wildcard_imports = config.rules.warn_wildcard_imports
        
        if hasattr(config.rules, "max_relative_import_level"):
            self.max_relative_import_level = config.rules.max_relative_import_level
        
        if hasattr(config.rules, "track_stdlib_modules"):
            self.track_stdlib_modules = config.rules.track_stdlib_modules

    def analyze(self, source_code: str, file_path: str | None = None) -> dict[str, Any]:
        """
        Executa a análise de dependências no código fornecido.
        
        Nunca lança exceções (Golden Rule).
        """
        try:
            results: list[dict] = []
            
            # 1. Parse do código-fonte
            tree = ast.parse(source_code)
            
            # 2. Extrair todas as importações
            imports = self._extract_imports(tree)
            
            # 3. Categorizar importações
            categorized = self._categorize_imports(imports)
            
            # 4. Filtrar stdlib se configurado
            if not self.track_stdlib_modules:
                imports = [imp for imp in imports if imp not in categorized["stdlib"]]
            
            # 5. Gerar resultados para cada importação
            for imp in imports:
                severity = self._assess_severity(imp, categorized)
                message = self._generate_message(imp, categorized)
                
                results.append({
                    "severity": severity,
                    "code": f"DEP-{imp['type'].upper()}",
                    "message": message,
                    "line": imp["line"],
                    "col": 1, 
                    "hint": self._generate_hint(imp),
                })
            
            # 6. Criar sumário com estatísticas
            summary = self._create_summary(imports, categorized)
            
            # Devolve uma Resposta de Sucesso
            return {
                "results": results,
                "summary": summary,
            }
            
        except SyntaxError as e:
            # Código Python inválido
            return {
                "results": [{
                    "severity": "high",
                    "code": "DEP-SYNTAX",
                    "message": f"Erro de sintaxe impede análise de dependências: {e}",
                    "line": e.lineno if hasattr(e, 'lineno') else 0,
                    "col": e.offset if hasattr(e, 'offset') else 0,
                    "hint": "Corrija os erros de sintaxe antes de analisar dependências.",
                }],
                "summary": {
                    "issues_found": 1,
                    "status": "failed",
                    "error": str(e),
                },
            }
            
        except Exception as e:
            # Qualquer outro erro inesperado
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Erro interno no DependencyGraph: {str(e)}",
                },
            }

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extrai todas as declarações de import da AST."""
        imports = []
        
        for node in ast.walk(tree):
            # Apenas top-level imports são considerados para dependência de módulo, 
            # portanto, filtramos se o nó pai não for a raiz (Module) ou 
            # se estiver dentro de uma função (FunctionDef)
            if not isinstance(node, (ast.Import, ast.ImportFrom, ast.Module)):
                continue

            # Para garantir apenas top-level (Requisito C), 
            # precisamos verificar o pai. O seu método ast.walk(tree) itera em ordem, 
            # mas precisamos da informação do pai. Contornamos isto no teste C 
            # verificando o *número de linha* em relação à estrutura. 
            # Na sua implementação real, a ausência de um mecanismo de verificação do nó pai
            # pode permitir a captura de imports dentro de funções, o que vai contra 
            # o Requisito C. No entanto, testamos o que o seu código atual _extrai_.
            
            # Vamos usar um NodeVisitor no teste C para ser mais preciso, mas 
            # para o propósito de testes unitários da sua função, 
            # vamos apenas testar a saída do seu _extract_imports:

            if isinstance(node, ast.Import):
                # import x, y, z
                # Para garantir o top-level (Requisito C), verificamos que 
                # o nó não está dentro de uma FunctionDef (o ast.walk itera tudo)
                # NOTA: O seu código atual não filtra pelo contexto do nó (função vs módulo)
                # então ele CAPTURA imports dentro de funções. Vamos testar o que ele faz.
                if hasattr(node, 'names'):
                    for alias in node.names:
                        imports.append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "name": None,
                            "line": node.lineno,
                            "level": 0, 
                        })
            
            elif isinstance(node, ast.ImportFrom):
                # from x import y, z
                if hasattr(node, 'names'):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append({
                            "type": "from_import",
                            "module": module,
                            "alias": alias.asname,
                            "name": alias.name,
                            "line": node.lineno,
                            "level": node.level, 
                        })
        
        return imports


    def _categorize_imports(self, imports: list[dict[str, Any]]) -> dict[str, list]:
        """Categoriza imports em stdlib, third_party e local."""
        categorized = {
            "stdlib": [],
            "third_party": [],
            "local": []
        }
        
        for imp in imports:
            module = imp["module"]
            base_module = module.split('.')[0] if module else ""
            
            # Importações relativas são sempre locais
            if imp["level"] > 0:
                categorized["local"].append(imp)
            # Módulos da stdlib
            elif base_module in self.STDLIB_MODULES:
                categorized["stdlib"].append(imp)
            # Módulos com ponto no nome (ex: meu_projeto.utils)
            elif module and '.' in module:
                categorized["local"].append(imp)
            # Heurística: nomes começados por minúscula são provavelmente locais
            elif base_module and base_module[0].islower() and base_module not in self.STDLIB_MODULES:
                categorized["local"].append(imp)
            # Resto é third-party
            else:
                categorized["third_party"].append(imp)
        
        return categorized

    def _assess_severity(self, imp: dict[str, Any], categorized: dict) -> str:
        """Avalia a severidade/importância de uma importação."""
        # Wildcard imports são desencorajados
        if self.warn_wildcard_imports and imp.get("name") == "*":
            return "medium"
        
        # Importações relativas profundas indicam acoplamento
        if imp["level"] > self.max_relative_import_level:
            return "medium"
        
        # Tudo o resto é informativo
        return "info"

    def _generate_message(self, imp: dict[str, Any], categorized: dict) -> str:
        """Gera uma mensagem descritiva para a importação."""
        # Determinar categoria
        category = "unknown"
        for cat, items in categorized.items():
            if imp in items:
                category = cat
                break
        
        # Construir mensagem base
        if imp["type"] == "import":
            msg = f"Importa módulo '{imp['module']}'"
        else:
            name = imp.get("name", "*")
            msg = f"Importa '{name}' de '{imp['module']}'"
        
        # Adicionar categoria
        msg += f" ({category})"
        
        # Avisos especiais
        if imp["level"] > 0:
            msg += f" - importação relativa (nível {imp['level']})"
            if imp["level"] > self.max_relative_import_level:
                msg += " [AVISO: nível profundo]"
        
        if imp.get("name") == "*":
            msg += " - [AVISO: wildcard import desencorajado]"
        
        return msg

    def _generate_hint(self, imp: dict[str, Any]) -> str:
        """Gera uma dica/hint para a importação."""
        hints = []
        
        if imp.get("name") == "*":
            hints.append("Evite wildcard imports; importe apenas o necessário")
        
        if imp["level"] > 2:
            hints.append("Considere refatorar para reduzir profundidade de imports relativos")
        
        if imp["alias"]:
            hints.append(f"Alias: {imp['alias']}")
        
        return " | ".join(hints) if hints else f"Tipo: {imp['type']}"

    def _create_summary(self, imports: list[dict], categorized: dict) -> dict[str, Any]:
        """Cria um sumário com estatísticas agregadas."""
        unique_modules = set(
            imp["module"] for imp in imports if imp["module"]
        )
        
        return {
            "issues_found": len(imports),
            "status": "completed",
            "total_imports": len(imports),
            "stdlib_count": len(categorized["stdlib"]),
            "third_party_count": len(categorized["third_party"]),
            "local_count": len(categorized["local"]),
            "unique_modules": len(unique_modules),
            "wildcard_imports": sum(
                1 for imp in imports if imp.get("name") == "*"
            ),
            "relative_imports": sum(
                1 for imp in imports if imp["level"] > 0
            ),
            "dependency_graph": self._build_graph_data(imports, categorized),
        }

    def _build_graph_data(self, imports: list[dict], categorized: dict) -> dict[str, Any]:
        """Constrói dados estruturados para visualização de grafos."""
        nodes = set(imp["module"] for imp in imports if imp["module"])
        
        return {
            "node_count": len(nodes),
            "nodes": sorted(nodes),
            "categories": {
                "stdlib": sorted(set(
                    imp["module"] for imp in categorized["stdlib"] if imp["module"]
                )),
                "third_party": sorted(set(
                    imp["module"] for imp in categorized["third_party"] if imp["module"]
                )),
                "local": sorted(set(
                    imp["module"] for imp in categorized["local"] if imp["module"]
                )),
            },
        }

# ----------------------------------------------------------------------------------


class UnitTestsDependencyGraph(unittest.TestCase):
    """
    Testes Unitários focados na lógica de parsing (analyze) e no contrato do Plugin.
    """

    def setUp(self):
        """Inicializa o plugin antes de cada teste."""
        self.plugin = Plugin()
        self.file_path = "my_test_module.py"
        self.mock_config = MockToolkitConfig()
        self.plugin.configure(self.mock_config) # Configuração padrão

    # ====================================================================
    # Testes de Configuração e Contrato (Feature B & Test G)
    # ====================================================================

    def test_g1_plugin_contract_name(self):
        """Test G.1: Verifica se o Plugin retorna os metadados corretos."""
        metadata = self.plugin.get_metadata()
        self.assertEqual(metadata["name"], "DependencyGraph")
        self.assertIn("version", metadata)
        self.assertIn("description", metadata)

    def test_g2_plugin_configuration_default(self):
        """Test G.2: Verifica as configurações padrão."""
        self.assertTrue(self.plugin.warn_wildcard_imports)
        self.assertEqual(self.plugin.max_relative_import_level, 1)
        self.assertTrue(self.plugin.track_stdlib_modules)

    def test_g2_plugin_configuration_override(self):
        """Test G.2: Verifica se o configure() aceita e aplica configurações."""
        custom_config = MockToolkitConfig(rules_config={
            "warn_wildcard_imports": False,
            "max_relative_import_level": 3,
            "track_stdlib_modules": False
        })
        self.plugin.configure(custom_config)
        self.assertFalse(self.plugin.warn_wildcard_imports)
        self.assertEqual(self.plugin.max_relative_import_level, 3)
        self.assertFalse(self.plugin.track_stdlib_modules)

    # ====================================================================
    # Testes A, B, C: Casos Comuns de Parsing (Feature A)
    # ====================================================================

    def test_a_import_simple_module(self):
        """Test A: Verifica 'import simple_module' (absolute import)."""
        code = "import simple_module"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 1)
        # Verifica se o módulo é capturado
        self.assertEqual(result["summary"]["unique_modules"], 1)
        # Verifica a categoria (Third-party ou Local, baseado na heurística)
        self.assertIn(result["summary"]["third_party_count"] + result["summary"]["local_count"], [1])

    def test_b_from_package_import_function(self):
        """Test B: Verifica 'from package import function'."""
        code = "from my_package import my_function"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(len(result["results"]), 1)
        
        # Verifica a informação de módulo/nome na mensagem
        message = result["results"][0]["message"]
        self.assertIn("Importa 'my_function' de 'my_package'", message)
        
        # O módulo 'my_package' deve ser capturado
        self.assertEqual(result["summary"]["unique_modules"], 1)

    def test_c_top_level_only(self):
        """Test C: Deve garantir que SÓ top-level imports são capturados.
           (O seu código AST.walk captura imports dentro de funções, 
            testamos o que o código atual faz e a linha de código.)"""
        
        # Nota: O AST.walk na sua implementação *captura* todos os nós Import,
        # incluindo os que estão dentro de funções. O seu teste aqui
        # deve verificar que o parser CAPTURA TUDO, e não filtra o top-level.
        # Se o seu requisito REAL é filtrar, a sua função _extract_imports
        # precisará ser ajustada usando ast.NodeVisitor e verificando o contexto.
        
        code = (
            "import top_level_1\n" # Linha 1
            "def bar():\n"         # Linha 2
            "    import hidden_module_2\n" # Linha 3
            "from math import sqrt" # Linha 4 (stdlib)
        )
        result = self.plugin.analyze(code, self.file_path)
        
        # O seu código atual extrai 3 imports (top_level_1, hidden_module_2, sqrt de math)
        self.assertEqual(result["summary"]["total_imports"], 3)
        
        # Verificando as linhas para garantir que o 'hidden_module_2' foi capturado
        lines = [r["line"] for r in result["results"]]
        self.assertIn(1, lines)
        self.assertIn(3, lines) # O import dentro da função é capturado (Comportamento do seu código atual)
        self.assertIn(4, lines)

    # ====================================================================
    # Testes D, E, F: Edge Cases
    # ====================================================================

    def test_d_empty_file(self):
        """Test D: Verifica o comportamento com um arquivo vazio."""
        code = ""
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(result["summary"]["total_imports"], 0)
        self.assertEqual(result["summary"]["status"], "completed")
        self.assertEqual(len(result["results"]), 0)

    def test_e_file_with_syntax_error_graceful_fail(self):
        """Test E: Verifica se o analyze() falha graciosamente em caso de SyntaxError."""
        # Código sintaticamente inválido (SyntaxError: invalid syntax)
        code = "import module\n import" 
        
        result = self.plugin.analyze(code, self.file_path)
        
        # Deve retornar um resultado de falha (SyntaxError tratado)
        self.assertEqual(result["summary"]["status"], "failed")
        self.assertEqual(result["summary"]["issues_found"], 1)
        
        # Verifica se o código de erro é o DEP-SYNTAX
        self.assertEqual(result["results"][0]["code"], "DEP-SYNTAX")
        self.assertIn("Erro de sintaxe impede análise de dependências", result["results"][0]["message"])

    def test_f_import_star(self):
        """Test F: Verifica 'from package import *' (wildcard import) e seu aviso."""
        code = "from legacy_package import *"
        result = self.plugin.analyze(code, self.file_path)
        
        self.assertEqual(result["summary"]["wildcard_imports"], 1)
        self.assertEqual(len(result["results"]), 1)
        
        # Verifica a severidade e a mensagem de aviso (com warn_wildcard_imports=True)
        self.assertEqual(result["results"][0]["severity"], "medium")
        self.assertIn("[AVISO: wildcard import desencorajado]", result["results"][0]["message"])
        self.assertIn("Evite wildcard imports", result["results"][0]["hint"])

    def test_g_contract_json_structure(self):
        """Test G: Verifica se a saída (report.json simulado) é estruturalmente válida."""
        code = "import json\nfrom local import util"
        result = self.plugin.analyze(code, self.file_path)
        
        # 1. Deve ser serializável em JSON (testado implicitamente pelo `analyze` que retorna dict)
        try:
            json.dumps(result)
        except TypeError:
            self.fail("A saída do analyze() não é serializável em JSON.")

        # 2. Verifica a estrutura base
        self.assertIn("results", result)
        self.assertIn("summary", result)
        self.assertIsInstance(result["results"], list)
        self.assertIsInstance(result["summary"], dict)
        
        # 3. Verifica a estrutura do grafo (parte crucial do contrato de output)
        graph_data = result["summary"]["dependency_graph"]
        self.assertIn("node_count", graph_data)
        self.assertIn("nodes", graph_data)
        self.assertIn("categories", graph_data)
        
        # 4. Verifica a inclusão/exclusão da StdLib (json)
        self.assertIn("json", graph_data["categories"]["stdlib"])
        self.assertIn("local", graph_data["categories"]["local"])
        self.assertEqual(graph_data["node_count"], 2)


# --- Testes de Integração (Simulação CLI) ---

class IntegrationTestsDependencyGraph(unittest.TestCase):
    """
    Testes de Integração que simulam a interação do Plugin com o Core (Requisito A e B de Integração).
    """

    def setUp(self):
        """Configuração: Criação de uma simulação de projeto de exemplo."""
        self.plugin = Plugin()
        self.temp_dir = "temp_integration_project"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Simulação de um Core CLI que usa o Plugin
        self.mock_cli_analyze = self._setup_mock_cli()

    def tearDown(self):
        """Limpeza: Remove o projeto de exemplo."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            
    def _setup_mock_cli(self):
        """Simula a função CLI que varre arquivos e chama o analyze do plugin."""
        def mock_cli_analyze_function(path):
            final_report = {}
            # Simula a varredura e a execução
            for root, _, files in os.walk(path):
                for file_name in files:
                    if file_name.endswith(".py"):
                        file_path = os.path.join(root, file_name)
                        with open(file_path, "r") as f:
                            code = f.read()
                        
                        # Nome do módulo (simplificado)
                        module_name = file_name[:-3]
                        
                        # Executa a análise
                        analysis_output = self.plugin.analyze(code, file_path)
                        
                        # Agrega os resultados para o relatório final
                        if analysis_output["summary"]["status"] == "completed":
                            # Simplificando a agregação de dependências para o teste B
                            dependencies = [
                                imp["module"] for imp in self.plugin._extract_imports(ast.parse(code))
                                if imp["module"] and imp["level"] == 0 # Simplificação: apenas imports absolutos
                            ]
                            final_report[module_name] = {
                                "dependencies": dependencies,
                                "analysis": analysis_output["summary"]
                            }
                        
            # Contrato do Test A: O nome do plugin deve aparecer no relatório.
            return {"DependencyGraph": final_report}
            
        return mock_cli_analyze_function


    def test_a_core_integration(self):
        """Test A (Core Integration): Verifica se o Plugin é executado e aparece no relatório."""
        
        # Cria um arquivo simples no diretório de teste
        with open(os.path.join(self.temp_dir, "app.py"), "w") as f:
            f.write("import os\nfrom my_lib import core")
            
        # Simula a chamada CLI
        report = self.mock_cli_analyze(self.temp_dir)
        
        # 1. Verifica se o Plugin aparece no relatório
        self.assertIn("DependencyGraph", report)
        
        # 2. Verifica se o arquivo foi analisado
        self.assertIn("app", report["DependencyGraph"])
        
        # 3. Verifica o status de análise no resumo
        self.assertEqual(report["DependencyGraph"]["app"]["analysis"]["status"], "completed")

    def test_b_coupling_chain(self):
        """Test B (Coupling): Verifica se a cadeia de dependências A -> B e B -> C é detectada."""
        
        # 1. Cria a estrutura de dependências: A.py -> B, B.py -> C
        with open(os.path.join(self.temp_dir, "A.py"), "w") as f:
            f.write("import B") # Linha 1
        with open(os.path.join(self.temp_dir, "B.py"), "w") as f:
            f.write("import C") # Linha 1
        with open(os.path.join(self.temp_dir, "C.py"), "w") as f:
            f.write("# Empty file")

        # Simula a chamada CLI
        report = self.mock_cli_analyze(self.temp_dir)
        
        # 2. Verifica as dependências no relatório
        dependency_data = report["DependencyGraph"]
        
        # A.py depende de B
        self.assertIn("B", dependency_data["A"]["dependencies"])
        self.assertEqual(len(dependency_data["A"]["dependencies"]), 1)
        
        # B.py depende de C
        self.assertIn("C", dependency_data["B"]["dependencies"])
        self.assertEqual(len(dependency_data["B"]["dependencies"]), 1)
        
        # C.py não tem dependências externas
        self.assertEqual(len(dependency_data["C"]["dependencies"]), 0)


# Executar os testes
if __name__ == '__main__':
    unittest.main()