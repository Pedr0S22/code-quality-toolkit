# Dependency Graph Plugin - Analyzes imports and creates dependency maps
from __future__ import annotations

import ast
from typing import Any

# Imports do Core do Projeto
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


class Plugin:
    """
    Plugin de Análise de Dependências: Mapeia todas as importações de código Python,
    categorizando-as e identificando padrões potencialmente problemáticos.
    """

    # Lista parcial de módulos da biblioteca padrão do Python
    STDLIB_MODULES = {
        "abc",
        "aifc",
        "argparse",
        "array",
        "ast",
        "asynchat",
        "asyncio",
        "asyncore",
        "atexit",
        "audioop",
        "base64",
        "bdb",
        "binascii",
        "binhex",
        "bisect",
        "builtins",
        "bz2",
        "calendar",
        "cgi",
        "cgitb",
        "chunk",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "codeop",
        "collections",
        "colorsys",
        "compileall",
        "concurrent",
        "configparser",
        "contextlib",
        "contextvars",
        "copy",
        "copyreg",
        "cProfile",
        "crypt",
        "csv",
        "ctypes",
        "curses",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "distutils",
        "doctest",
        "email",
        "encodings",
        "enum",
        "errno",
        "faulthandler",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "formatter",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "grp",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "imaplib",
        "imghdr",
        "imp",
        "importlib",
        "inspect",
        "io",
        "ipaddress",
        "itertools",
        "json",
        "keyword",
        "lib2to3",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "mailcap",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "modulefinder",
        "multiprocessing",
        "netrc",
        "nis",
        "nntplib",
        "numbers",
        "operator",
        "optparse",
        "os",
        "ossaudiodev",
        "parser",
        "pathlib",
        "pdb",
        "pickle",
        "pickletools",
        "pipes",
        "pkgutil",
        "platform",
        "plistlib",
        "poplib",
        "posix",
        "posixpath",
        "pprint",
        "profile",
        "pstats",
        "pty",
        "pwd",
        "py_compile",
        "pyclbr",
        "pydoc",
        "queue",
        "quopri",
        "random",
        "re",
        "readline",
        "reprlib",
        "resource",
        "rlcompleter",
        "runpy",
        "sched",
        "secrets",
        "select",
        "selectors",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtpd",
        "smtplib",
        "sndhdr",
        "socket",
        "socketserver",
        "spwd",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "stringprep",
        "struct",
        "subprocess",
        "sunau",
        "symbol",
        "symtable",
        "sys",
        "sysconfig",
        "syslog",
        "tabnanny",
        "tarfile",
        "telnetlib",
        "tempfile",
        "termios",
        "test",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "tracemalloc",
        "tty",
        "turtle",
        "turtledemo",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uu",
        "uuid",
        "venv",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "winreg",
        "winsound",
        "wsgiref",
        "xdrlib",
        "xml",
        "xmlrpc",
        "zipapp",
        "zipfile",
        "zipimport",
        "zlib",
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

    def configure(self, config: ToolkitConfig) -> None:
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

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Executa a análise de dependências no código fornecido.

        Nunca lança exceções (Golden Rule).
        """
        try:
            results: list[IssueResult] = []

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

                results.append(
                    {
                        "severity": severity,
                        "code": f"DEP-{imp['type'].upper()}",
                        "message": message,
                        "line": imp["line"],
                        "col": 1,  # AST não fornece coluna para imports
                        "hint": self._generate_hint(imp),
                    }
                )

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
                "results": [
                    {
                        "severity": "high",
                        "code": "DEP-SYNTAX",
                        "message": "Erro de sintaxe impede análise de"
                        + f"dependências: {e}",
                        "line": e.lineno if hasattr(e, "lineno") else 0,
                        "col": e.offset if hasattr(e, "offset") else 0,
                        "hint": (
                            "Corrija os erros de sintaxe antes de analisar"
                            + "dependências."
                        ),
                    }
                ],
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
            if isinstance(node, ast.Import):
                # import x, y, z
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "name": None,
                            "line": node.lineno,
                            "level": 0,  # Sempre absoluto
                        }
                    )

            elif isinstance(node, ast.ImportFrom):
                # from x import y, z
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "alias": alias.asname,
                            "name": alias.name,
                            "line": node.lineno,
                            "level": node.level,  # 0 = absoluto, >0 = relativo
                        }
                    )

        return imports

    def _categorize_imports(self, imports: list[dict[str, Any]]) -> dict[str, list]:
        """Categoriza imports em stdlib, third_party e local."""
        categorized = {"stdlib": [], "third_party": [], "local": []}

        for imp in imports:
            module = imp["module"]
            base_module = module.split(".")[0] if module else ""

            # Importações relativas são sempre locais
            if imp["level"] > 0:
                categorized["local"].append(imp)
            # Módulos da stdlib
            elif base_module in self.STDLIB_MODULES:
                categorized["stdlib"].append(imp)
            # Módulos com ponto no nome (ex: meu_projeto.utils)
            elif module and "." in module:
                categorized["local"].append(imp)
            # Heurística: nomes começados por minúscula são provavelmente locais
            elif (
                base_module
                and base_module[0].islower()
                and base_module not in self.STDLIB_MODULES
            ):
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
            hints.append(
                "Considere refatorar para reduzir profundidade de imports relativos"
            )
        if imp["alias"]:
            hints.append(f"Alias: {imp['alias']}")

        return " | ".join(hints) if hints else f"Tipo: {imp['type']}"

    def _create_summary(self, imports: list[dict], categorized: dict) -> dict[str, Any]:
        """Cria um sumário com estatísticas agregadas."""
        unique_modules = set(imp["module"] for imp in imports if imp["module"])

        return {
            "issues_found": len(imports),
            "status": "completed",
            "total_imports": len(imports),
            "stdlib_count": len(categorized["stdlib"]),
            "third_party_count": len(categorized["third_party"]),
            "local_count": len(categorized["local"]),
            "unique_modules": len(unique_modules),
            "wildcard_imports": sum(1 for imp in imports if imp.get("name") == "*"),
            "relative_imports": sum(1 for imp in imports if imp["level"] > 0),
            "dependency_graph": self._build_graph_data(imports, categorized),
        }

    def _build_graph_data(
        self, imports: list[dict], categorized: dict
    ) -> dict[str, Any]:
        """Constrói dados estruturados para visualização de grafos."""
        nodes = set(imp["module"] for imp in imports if imp["module"])

        return {
            "node_count": len(nodes),
            "nodes": sorted(nodes),
            "categories": {
                "stdlib": sorted(
                    set(imp["module"] for imp in categorized["stdlib"] if imp["module"])
                ),
                "third_party": sorted(
                    set(
                        imp["module"]
                        for imp in categorized["third_party"]
                        if imp["module"]
                    )
                ),
                "local": sorted(
                    set(imp["module"] for imp in categorized["local"] if imp["module"])
                ),
            },
        }
