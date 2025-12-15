# Dependency Graph Plugin - Analyzes imports and creates dependency maps
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

# Imports do Core do Projeto
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


class Plugin:
    """
    Plugin de Análise de Dependências: Mapeia todas as importações de código Python,
    categorizando-as e identificando padrões potencialmente problemáticos.
    Também gera um dashboard visual (HTML).
    """

    # Lista parcial de módulos da biblioteca padrão do Python
    STDLIB_MODULES = {
        "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
        "asyncore", "atexit", "audioop", "base64", "bdb", "binascii", "binhex",
        "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb", "chunk",
        "cmath", "cmd", "code", "codecs", "codeop", "collections", "colorsys",
        "compileall", "concurrent", "configparser", "contextlib", "contextvars",
        "copy", "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses",
        "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
        "distutils", "doctest", "email", "encodings", "enum", "errno",
        "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch",
        "formatter", "fractions", "ftplib", "functools", "gc", "getopt",
        "getpass", "gettext", "glob", "grp", "gzip", "hashlib", "heapq",
        "hmac", "html", "http", "imaplib", "imghdr", "imp", "importlib",
        "inspect", "io", "ipaddress", "itertools", "json", "keyword",
        "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox",
        "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder",
        "multiprocessing", "netrc", "nis", "nntplib", "numbers", "operator",
        "optparse", "os", "ossaudiodev", "parser", "pathlib", "pdb", "pickle",
        "pickletools", "pipes", "pkgutil", "platform", "plistlib", "poplib",
        "posix", "posixpath", "pprint", "profile", "pstats", "pty", "pwd",
        "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random", "re",
        "readline", "reprlib", "resource", "rlcompleter", "runpy", "sched",
        "secrets", "select", "selectors", "shelve", "shlex", "shutil",
        "signal", "site", "smtpd", "smtplib", "sndhdr", "socket",
        "socketserver", "spwd", "sqlite3", "ssl", "stat", "statistics",
        "string", "stringprep", "struct", "subprocess", "sunau", "symbol",
        "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile",
        "telnetlib", "tempfile", "termios", "test", "textwrap", "threading",
        "time", "timeit", "tkinter", "token", "tokenize", "trace",
        "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
        "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv",
        "warnings", "wave", "weakref", "webbrowser", "winreg", "winsound",
        "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp", "zipfile",
        "zipimport", "zlib",
    }

    def __init__(self) -> None:
        """Inicializa o plugin com configurações padrão."""
        # Configurações de Análise
        self.warn_wildcard_imports = True
        self.max_relative_import_level = 1
        self.track_stdlib_modules = True
        
        # Configurações de Dashboard
        self.dashboard_output_format = "html"
        self.dashboard_show_stdlib = True
        self.dashboard_color_by_category = True

    def get_metadata(self) -> dict[str, str]:
        """Devolve metadados do plugin."""
        return {
            "name": "DependencyGraph",
            "version": "1.0.0",
            "description": (
                "Mapeia importações, deteta problemas e gera visualizações."
            ),
        }

    def configure(self, config: ToolkitConfig) -> None:
        """
        Configura o plugin a partir do ficheiro TOML global.
        """
        # Regras de Análise
        if hasattr(config.rules, "warn_wildcard_imports"):
            self.warn_wildcard_imports = config.rules.warn_wildcard_imports

        if hasattr(config.rules, "max_relative_import_level"):
            self.max_relative_import_level = config.rules.max_relative_import_level

        if hasattr(config.rules, "track_stdlib_modules"):
            self.track_stdlib_modules = config.rules.track_stdlib_modules

        # Regras de Dashboard (Opcionais)
        if hasattr(config.rules, "dashboard_output_format"):
            self.dashboard_output_format = config.rules.dashboard_output_format
        if hasattr(config.rules, "dashboard_show_stdlib"):
            self.dashboard_show_stdlib = config.rules.dashboard_show_stdlib

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        Executa a análise de dependências no código fornecido.
        """
        try:
            results: list[IssueResult] = []

            # 1. Parse do código-fonte
            tree = ast.parse(source_code)

            # 2. Extrair todas as importações
            imports = self._extract_imports(tree)

            # 3. Categorizar importações
            categorized = self._categorize_imports(imports)

            # 4. Filtrar stdlib se configurado (apenas para issues, não para grafo)
            filtered_imports = imports
            if not self.track_stdlib_modules:
                filtered_imports = [
                    imp for imp in imports if imp not in categorized["stdlib"]
                ]

            # 5. Gerar resultados para cada importação
            for imp in filtered_imports:
                severity = self._assess_severity(imp, categorized)
                message = self._generate_message(imp, categorized)

                results.append(
                    {
                        "severity": severity,
                        "code": f"DEP-{imp['type'].upper()}",
                        "message": message,
                        "line": imp["line"],
                        "col": 1,
                        "hint": self._generate_hint(imp),
                    }
                )

            # 6. Criar sumário com estatísticas
            summary = self._create_summary(imports, categorized)

            return {
                "results": results,
                "summary": summary,
            }

        except SyntaxError as e:
            return {
                "results": [
                    {
                        "severity": "high",
                        "code": "DEP-SYNTAX",
                        "message": f"Erro de sintaxe: {e}",
                        "line": e.lineno if hasattr(e, "lineno") else 0,
                        "col": e.offset if hasattr(e, "offset") else 0,
                        "hint": "Corrija a sintaxe.",
                    }
                ],
                "summary": {
                    "issues_found": 1,
                    "status": "failed",
                    "error": str(e),
                },
            }

        except Exception as e:
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Erro interno: {str(e)}",
                },
            }

    # ==========================================================================
    # LÓGICA DE DASHBOARD (HTML GENERATION)
    # ==========================================================================

    def generate_dashboard(
        self,
        aggregated_results: list[dict],
        output_path: str = "dependency_graph_dashboard.html",
        dependency_data: dict[str, Any] = None
    ) -> str:
        """
        Gera um dashboard HTML interativo a partir dos dados de dependências.
        """
        # 1. AGREGAÇÃO DE DADOS
        # Se não vierem dados prontos, processamos a lista de resultados acumulados
        if dependency_data is None:
            if aggregated_results:
                dependency_data = self._aggregate_results(aggregated_results)
            else:
                # Fallback: cria estrutura vazia para não quebrar o HTML
                dependency_data = {
                    "summary": {
                        "total_imports": 0, "unique_modules": 0, 
                        "stdlib_count": 0, "third_party_count": 0,
                        "dependency_graph": {"categories": {"stdlib": [], "third_party": [], "local": []}}
                    }
                }

        summary = dependency_data.get("summary", {})
        graph_data = summary.get("dependency_graph", {})

        try:
            # 2. GERAÇÃO DO HTML (Com CSS ajustado)
            html_content = self._generate_html(graph_data, summary)
            
            # 3. SALVAMENTO DO ARQUIVO (Correção de Path)
            target_path = Path(output_path)

            if not target_path.is_absolute():
                output_dir = Path(__file__).parent
                output_file = output_dir / target_path
            else:
                output_file = target_path

            # Garante que o diretório pai existe
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            output_file.write_text(html_content, encoding="utf-8")
            return str(output_file.absolute())

        except Exception as e:
            print(f"Erro ao gerar dashboard: {e}")
            return ""

    def _aggregate_results(self, results: list[dict]) -> dict[str, Any]:
        """
        Método Auxiliar: Combina os resultados de vários arquivos num único sumário.
        """
        total_imports = 0
        all_stdlib = set()
        all_third_party = set()
        all_local = set()
        all_unique_modules = set()

        for result in results:
            summary = result.get("summary", {})
            graph = summary.get("dependency_graph", {}).get("categories", {})
            
            # Soma contadores simples
            total_imports += summary.get("total_imports", 0)

            # Combina as listas de módulos (usando set e get seguro)
            all_stdlib.update(graph.get("stdlib") or [])
            all_third_party.update(graph.get("third_party") or [])
            all_local.update(graph.get("local") or [])
            
            # Coleta módulos únicos
            nodes = summary.get("dependency_graph", {}).get("nodes", [])
            all_unique_modules.update(nodes)

        return {
            "summary": {
                "total_imports": total_imports,
                "unique_modules": len(all_unique_modules),
                "stdlib_count": len(all_stdlib),
                "third_party_count": len(all_third_party),
                "dependency_graph": {
                    "categories": {
                        "stdlib": sorted(list(all_stdlib)),
                        "third_party": sorted(list(all_third_party)),
                        "local": sorted(list(all_local)),
                    }
                }
            }
        }

    
    def _generate_html(self, graph_data: dict, summary: dict) -> str:
        """Gera o conteúdo HTML do dashboard com CSS ajustado."""
        stats = self._generate_stats_html(summary)
        categories = graph_data.get("categories", {})

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Dependency Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            /* AJUSTE DE TAMANHO DA JANELA */
            width: 95%;
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #2d3748; border-bottom: 2px solid #edf2f7; padding-bottom: 15px; margin-top: 0; }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: white;
            border: 1px solid #e2e8f0;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }}
        .stat-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 15px rgba(0,0,0,0.1); border-color: #cbd5e0; }}
        .stat-value {{ font-size: 42px; font-weight: 700; color: #2b6cb0; line-height: 1.2; }}
        .stat-label {{ font-size: 13px; color: #718096; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; margin-top: 5px; }}
        
        .modules-section {{ margin-top: 50px; }}
        .modules-section h2 {{ color: #4a5568; margin-bottom: 20px; }}
        
        .category-container {{ 
            margin-bottom: 30px; 
            background: #fff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            overflow: hidden;
        }}
        .category-header {{
            padding: 15px 25px;
            background: #f7fafc;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #edf2f7;
        }}
        .module-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
            padding: 25px;
        }}
        .module-chip {{
            padding: 8px 16px;
            background: #f7fafc;
            border: 1px solid #edf2f7;
            border-radius: 6px;
            font-size: 14px;
            color: #4a5568;
            display: flex;
            align-items: center;
            transition: background 0.2s;
        }}
        .module-chip:hover {{ background: #edf2f7; border-color: #cbd5e0; }}
        .module-chip:before {{
            content: "📦";
            margin-right: 10px;
            font-size: 16px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Dependency Analysis Dashboard</h1>
        
        <div class="stats">
            {stats}
        </div>

        <div class="modules-section">
            <h2>📦 Module Breakdown</h2>
            {self._generate_categories_html(categories)}
        </div>
    </div>
</body>
</html>"""

    def _generate_stats_html(self, summary: dict) -> str:
        """Gera os cartões de estatística."""
        metrics = [
            ("Total Imports", summary.get('total_imports', 0)),
            ("Unique Modules", summary.get('unique_modules', 0)),
            ("StdLib Uses", summary.get('stdlib_count', 0)),
            ("3rd Party Uses", summary.get('third_party_count', 0))
        ]
        
        html = ""
        for label, value in metrics:
            html += f"""
            <div class="stat-card">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """
        return html

    def _generate_categories_html(self, categories: dict) -> str:
        """Gera a lista de módulos por categoria."""
        html = ""
        
        cat_meta = {
            "stdlib": {"color": "#48bb78", "label": "Standard Library"},
            "third_party": {"color": "#4299e1", "label": "Third Party"},
            "local": {"color": "#ed8936", "label": "Local / Internal"}
        }

        for cat_key, modules in categories.items():
            if not modules:
                continue
                
            meta = cat_meta.get(cat_key, {"color": "#666", "label": cat_key.title()})
            color = meta["color"]
            label = meta["label"]
            
            module_chips = "".join(
                f'<div class="module-chip">{m}</div>' for m in sorted(modules)
            )
            
            html += f"""
            <div class="category-container">
                <div class="category-header" style="border-left: 5px solid {color}">
                    <span>{label}</span>
                    <span style="background:{color}; color:white; padding:2px 8px; border-radius:12px; font-size:12px;">
                        {len(modules)}
                    </span>
                </div>
                <div class="module-grid">
                    {module_chips}
                </div>
            </div>
            """
        return html
    def _generate_stats_html(self, summary: dict) -> str:
        """Gera os cartões de estatística."""
        metrics = [
            ("Total Imports", summary.get('total_imports', 0)),
            ("Unique Modules", summary.get('unique_modules', 0)),
            ("StdLib Uses", summary.get('stdlib_count', 0)),
            ("3rd Party Uses", summary.get('third_party_count', 0))
        ]
        
        html = ""
        for label, value in metrics:
            html += f"""
            <div class="stat-card">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """
        return html

    def _generate_categories_html(self, categories: dict) -> str:
        """Gera a lista de módulos por categoria."""
        html = ""
        
        # Mapeamento de cores e ícones para cada categoria
        cat_meta = {
            "stdlib": {"color": "#48bb78", "label": "Standard Library"},
            "third_party": {"color": "#4299e1", "label": "Third Party"},
            "local": {"color": "#ed8936", "label": "Local / Internal"}
        }

        for cat_key, modules in categories.items():
            if not modules:
                continue
                
            meta = cat_meta.get(cat_key, {"color": "#666", "label": cat_key.title()})
            color = meta["color"]
            label = meta["label"]
            
            # Gerar chips para cada módulo
            module_chips = "".join(
                f'<div class="module-chip">{m}</div>' for m in sorted(modules)
            )
            
            html += f"""
            <div class="category-container">
                <div class="category-header" style="border-left: 5px solid {color}">
                    <span>{label}</span>
                    <span style="background:{color}; color:white; padding:2px 8px; border-radius:12px; font-size:12px;">
                        {len(modules)}
                    </span>
                </div>
                <div class="module-grid">
                    {module_chips}
                </div>
            </div>
            """
        return html

    # ==========================================================================
    # LÓGICA DE ANÁLISE (AST PARSING)
    # ==========================================================================

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Extrai todas as declarações de import da AST."""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
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
        categorized = {"stdlib": [], "third_party": [], "local": []}

        for imp in imports:
            module = imp["module"]
            base_module = module.split(".")[0] if module else ""

            if imp["level"] > 0:
                categorized["local"].append(imp)
            elif base_module in self.STDLIB_MODULES:
                categorized["stdlib"].append(imp)
            elif module and "." in module:
                categorized["local"].append(imp)
            elif (base_module and base_module[0].islower()
                  and base_module not in self.STDLIB_MODULES):
                categorized["local"].append(imp)
            else:
                categorized["third_party"].append(imp)

        return categorized

    def _assess_severity(self, imp: dict[str, Any], categorized: dict) -> str:
        """Avalia a severidade/importância de uma importação."""
        if self.warn_wildcard_imports and imp.get("name") == "*":
            return "medium"
        if imp["level"] > self.max_relative_import_level:
            return "medium"
        return "info"

    def _generate_message(self, imp: dict[str, Any], categorized: dict) -> str:
        """Gera uma mensagem descritiva."""
        category = "unknown"
        for cat, items in categorized.items():
            if imp in items:
                category = cat
                break

        if imp["type"] == "import":
            msg = f"Importa módulo '{imp['module']}'"
        else:
            name = imp.get("name", "*")
            msg = f"Importa '{name}' de '{imp['module']}'"

        msg += f" ({category})"

        if imp["level"] > 0:
            msg += f" - relativa (nível {imp['level']})"
        if imp.get("name") == "*":
            msg += " [AVISO: wildcard]"

        return msg

    def _generate_hint(self, imp: dict[str, Any]) -> str:
        """Gera uma dica/hint."""
        hints = []
        if imp.get("name") == "*":
            hints.append("Evite wildcard imports.")
        if imp["level"] > 2:
            hints.append("Reduza profundidade de imports relativos.")
        
        return " | ".join(hints) if hints else ""

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
        """Constrói dados estruturados para visualização."""
        nodes = set(imp["module"] for imp in imports if imp["module"])

        return {
            "node_count": len(nodes),
            "nodes": sorted(nodes),
            "categories": {
                "stdlib": sorted(set(imp["module"] for imp in categorized["stdlib"] if imp["module"])),
                "third_party": sorted(set(imp["module"] for imp in categorized["third_party"] if imp["module"])),
                "local": sorted(set(imp["module"] for imp in categorized["local"] if imp["module"])),
            },
        }