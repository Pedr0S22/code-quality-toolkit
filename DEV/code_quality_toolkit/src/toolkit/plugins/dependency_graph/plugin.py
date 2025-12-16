from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


class Plugin:
    """
    Plugin de Análise de Dependências.
    Mapeia importações e gera dashboard HTML (Molde Robusto D3.js).
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
        self.warn_wildcard_imports = True
        self.max_relative_import_level = 1
        self.track_stdlib_modules = True

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "DependencyGraph",
            "version": "1.0.0",
            "description": "Mapeia importações e deteta problemas.",
        }

    def configure(self, config: ToolkitConfig) -> None:
        if hasattr(config.rules, "warn_wildcard_imports"):
            self.warn_wildcard_imports = config.rules.warn_wildcard_imports
        if hasattr(config.rules, "max_relative_import_level"):
            self.max_relative_import_level = config.rules.max_relative_import_level
        if hasattr(config.rules, "track_stdlib_modules"):
            self.track_stdlib_modules = config.rules.track_stdlib_modules

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """Executa a análise de dependências."""
        try:
            results: list[IssueResult] = []
            tree = ast.parse(source_code)
            imports = self._extract_imports(tree)
            categorized = self._categorize_imports(imports)

            # Filtragem opcional para issues
            filtered_imports = imports
            if not self.track_stdlib_modules:
                filtered_imports = [
                    imp for imp in imports if imp not in categorized["stdlib"]
                ]

            for imp in filtered_imports:
                severity = self._assess_severity(imp)
                message = self._generate_message(imp, categorized)

                results.append(
                    {
                        "severity": severity,
                        "code": f"DEP-{imp['type'].upper()}",
                        "message": message,
                        "line": imp["line"],
                        "col": 1,
                        "hint": self._generate_hint(imp),
                        "file": file_path or "unknown",
                        "module": imp["module"],
                        "category": self._get_category(imp, categorized),
                    }
                )

            summary = self._create_summary(imports, categorized)

            return {
                "results": results,
                "summary": summary,
            }

        except SyntaxError as e:
            # FIX: Retorna o erro na lista 'results' para o teste passar
            return {
                "results": [
                    {
                        "severity": "high",
                        "code": "DEP-SYNTAX",
                        "message": f"Erro de sintaxe: {e}",
                        "line": getattr(e, "lineno", 1) or 1,
                        "col": getattr(e, "offset", 1) or 1,
                        "hint": "Corrija a sintaxe.",
                        "file": file_path or "unknown",
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
                    "error": str(e),
                },
            }

    # ==========================================================================
    # DASHBOARD GENERATION (Molde Robusto D3.js)
    # ==========================================================================

    def generate_dashboard(
        self,
        aggregated_results: list[dict],
        output_path: str = "dependency_graph_dashboard.html",
        dependency_data: dict = None,
    ) -> str:
        """Gera o dashboard HTML agregando dados."""

        # 1. Agregação Robusta
        dashboard_data = self._aggregate_data_for_dashboard(aggregated_results)

        # print(
        #     f"[DependencyGraph] Dashboard: "
        #     f"{dashboard_data['metrics']['total_imports']} imports processados."
        # )

        # 2. Geração do HTML
        data_json = json.dumps(dashboard_data)
        html_content = self._get_html_template(data_json)

        # 3. Salvamento
        try:
            target_path = Path(output_path)
            if not target_path.is_absolute():
                output_dir = Path(__file__).parent
                output_file = output_dir / target_path
            else:
                output_file = target_path

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_content, encoding="utf-8")
            return str(output_file.absolute())

        except Exception:
            # print(f"[DependencyGraph] Erro ao salvar dashboard: {e}")
            return ""

    def _aggregate_data_for_dashboard(self, results: list[dict]) -> dict:
        """
        Normaliza os dados para o D3.js.
        """
        flattened_imports = []

        # Normalização: Extrair todos os imports/issues
        for entry in results:
            if "plugins" in entry:
                file_path = entry.get("file", "unknown")
                plugins_list = entry.get("plugins", [])

                plugin_res = next(
                    (p for p in plugins_list if p["plugin"] == "DependencyGraph"), None
                )
                if plugin_res:
                    issues = plugin_res.get("results", [])
                    for issue in issues:
                        if "file" not in issue:
                            issue["file"] = file_path
                        flattened_imports.append(issue)

            elif "code" in entry or "severity" in entry:
                flattened_imports.append(entry)

        # Contagem
        category_counts = {"stdlib": 0, "third_party": 0, "local": 0}
        module_counts = {}
        files_counter = {}

        for item in flattened_imports:
            # Categoria
            cat = item.get("category", "unknown")
            if cat in category_counts:
                category_counts[cat] += 1

            # Módulo (Top External Libs)
            mod = item.get("module", "unknown").split(".")[0]  # Pega o root module
            module_counts[mod] = module_counts.get(mod, 0) + 1

            # Arquivo (Top Consumers)
            fname = item.get("file", "unknown")
            files_counter[fname] = files_counter.get(fname, 0) + 1

        # Formatação para D3
        cat_data = [
            {"category": k, "count": v} for k, v in category_counts.items() if v > 0
        ]

        mod_data = [{"module": k, "count": v} for k, v in module_counts.items()]
        mod_data.sort(key=lambda x: x["count"], reverse=True)

        top_files = [{"file": k, "count": v} for k, v in files_counter.items()]
        top_files.sort(key=lambda x: x["count"], reverse=True)

        unique_modules_count = len(module_counts)

        return {
            "metrics": {
                "total_files": len(files_counter),
                "total_imports": len(flattened_imports),
                "unique_modules": unique_modules_count,
            },
            "category_counts": cat_data,
            "top_modules": mod_data[:10],
            "top_files": top_files[:10],
        }

    def _get_html_template(self, data_json: str) -> str:
        """Template D3.js (Tema Roxo) Responsivo."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dependency Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            margin: 0; padding: 20px;
            background-color: #f4f4f4;
            display: flex; justify-content: center;
        }}
        .chart-container {{
            width: 100%;
            max-width: 1066px;
            aspect-ratio: 1066 / 628;
            background: white; border: 1px solid #ccc;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            box-sizing: border-box;
        }}
    </style>
</head>
<body>

<div id="app" class="chart-container"></div>

<script>
    const data = {data_json};
    const width = 1066; const height = 628;
    
    // SVG Setup Responsivo
    const svg = d3.select("#app").append("svg")
        .attr("viewBox", `0 0 ${{width}} ${{height}}`)
        .attr("preserveAspectRatio", "xMidYMid meet")
        .style("width", "100%")
        .style("height", "100%")
        .style("background-color", "#fff");

    // HEADER (Roxo)
    svg.append("rect")
        .attr("x", 0).attr("y", 0).attr("width", width)
        .attr("height", 70).attr("fill", "#6f42c1");
    svg.append("text").attr("x", 20).attr("y", 45).attr("fill", "white")
        .style("font-size", "24px").style("font-weight", "bold")
        .text("Dependency Graph Analysis");

    // METRICS
    const mGroup = svg.append("g").attr("transform", "translate(700, 20)");
    
    mGroup.append("rect")
        .attr("x", 0).attr("width", 140).attr("height", 30)
        .attr("rx", 5).attr("fill", "rgba(255,255,255,0.2)");
    mGroup.append("text").attr("x", 70).attr("y", 20)
        .attr("text-anchor", "middle").attr("fill", "white")
        .style("font-weight", "bold")
        .text(`Imports: ${{data.metrics.total_imports}}`);
    
    mGroup.append("rect")
        .attr("x", 150).attr("width", 160).attr("height", 30)
        .attr("rx", 5).attr("fill", "rgba(255,255,255,0.2)");
    mGroup.append("text").attr("x", 230).attr("y", 20)
        .attr("text-anchor", "middle").attr("fill", "white")
        .style("font-weight", "bold")
        .text(`Unique Libs: ${{data.metrics.unique_modules}}`);

    const col1X = 50; const col2X = 550; const contentY = 120;

    // CHART 1: CATEGORIES
    svg.append("text").attr("x", col1X).attr("y", contentY - 10)
        .style("font-size", "18px").style("font-weight", "bold")
        .text("Imports by Category");
    const catWidth = 450; const catHeight = 200;
    const catGroup = svg.append("g")
        .attr("transform", `translate(${{col1X}}, ${{contentY}})`);
    
    const catData = data.category_counts || [];
    if (catData.length > 0) {{
        const xCat = d3.scaleBand()
            .domain(catData.map(d => d.category))
            .range([0, catWidth]).padding(0.3);
        const maxVal = d3.max(catData, d => d.count);
        const yCat = d3.scaleLinear()
            .domain([0, maxVal * 1.2]).range([catHeight, 0]);
        
        catGroup.append("g").attr("transform", `translate(0,${{catHeight}})`).call(d3.axisBottom(xCat));
        catGroup.append("g").call(d3.axisLeft(yCat).ticks(5));
        
        const colorMap = {{ "stdlib": "#48bb78", "third_party": "#4299e1", "local": "#ed8936", "unknown": "#999" }};
        
        catGroup.selectAll("rect").data(catData).enter().append("rect")
            .attr("x", d => xCat(d.category)).attr("y", d => yCat(d.count))
            .attr("width", xCat.bandwidth())
            .attr("height", d => catHeight - yCat(d.count))
            .attr("fill", d => colorMap[d.category] || "#666");
            
        catGroup.selectAll(".label").data(catData).enter().append("text")
            .attr("x", d => xCat(d.category) + xCat.bandwidth()/2)
            .attr("y", d => yCat(d.count) - 5).attr("text-anchor", "middle")
            .style("font-size", "12px").style("font-weight", "bold")
            .text(d => d.count);
    }} else {{
         catGroup.append("text").attr("y", 100).text("No imports found");
    }}

    // CHART 2: TOP MODULES
    const modsY = contentY + catHeight + 60;
    svg.append("text").attr("x", col1X).attr("y", modsY - 10)
        .style("font-size", "18px").style("font-weight", "bold")
        .text("Most Used Libraries");
    
    const textPadding = 100;
    const modGroup = svg.append("g")
        .attr("transform", `translate(${{col1X + textPadding}}, ${{modsY}})`);
    const modData = (data.top_modules || []).slice(0, 5);
    
    if(modData.length > 0) {{
        const maxCount = d3.max(modData, d => d.count);
        const xMod = d3.scaleLinear()
            .domain([0, maxCount * 1.2]).range([0, catWidth - textPadding]);
        const yMod = d3.scaleBand()
            .domain(modData.map(d => d.module)).range([0, 150]).padding(0.2);
        
        modGroup.append("g").call(d3.axisLeft(yMod));
        modGroup.selectAll("rect").data(modData).enter().append("rect")
            .attr("x", 1).attr("y", d => yMod(d.module))
            .attr("width", d => xMod(d.count))
            .attr("height", yMod.bandwidth()).attr("fill", "#6f42c1");
            
        modGroup.selectAll("text.val").data(modData).enter().append("text")
            .attr("x", d => xMod(d.count) + 5)
            .attr("y", d => yMod(d.module) + yMod.bandwidth()/2 + 4)
            .style("font-size", "11px").style("font-weight", "bold")
            .text(d => d.count);
    }} else {{
        svg.append("text").attr("x", col1X).attr("y", modsY + 50)
            .text("No data available");
    }}

    // LIST: TOP FILES
    svg.append("text").attr("x", col2X).attr("y", contentY - 10)
        .style("font-size", "18px").style("font-weight", "bold")
        .text("Files with Most Imports");
    const listGroup = svg.append("g")
        .attr("transform", `translate(${{col2X}}, ${{contentY}})`);
    listGroup.append("rect")
        .attr("width", 450).attr("height", 420)
        .attr("fill", "#fafafa").attr("stroke", "#eee");

    const files = data.top_files || [];
    
    if (files.length > 0) {{
        files.forEach((file, i) => {{
            const yPos = 30 + (i * 40);
            if (i > 0) listGroup.append("line")
                .attr("x1", 10).attr("y1", yPos - 25).attr("x2", 440)
                .attr("y2", yPos - 25).attr("stroke", "#eee");
            
            let fileName = file.file;
            if (fileName.length > 50) fileName = "..." + fileName.slice(-47);
            
            listGroup.append("text").attr("x", 15).attr("y", yPos)
                .style("font-family", "monospace").style("font-size", "12px")
                .text(`${{i+1}}. ${{fileName}}`);
            listGroup.append("rect").attr("x", 400).attr("y", yPos - 12)
                .attr("width", 30).attr("height", 18).attr("rx", 4)
                .attr("fill", "#6f42c1");
            listGroup.append("text").attr("x", 415).attr("y", yPos + 1)
                .attr("text-anchor", "middle").attr("fill", "white")
                .style("font-size", "11px").style("font-weight", "bold")
                .text(file.count);
        }});
    }} else {{
        listGroup.append("text").attr("x", 225).attr("y", 210)
            .attr("text-anchor", "middle").attr("fill", "#666")
            .text("No files analyzed");
    }}
</script>
</body>
</html>"""  # noqa: E501

    # ==========================================================================
    # LÓGICA DE ANÁLISE (AST)
    # ==========================================================================

    def _extract_imports(self, tree: ast.AST) -> list[dict[str, Any]]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        {
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,  # Mantido para testes
                            "name": None,
                            "line": node.lineno,
                            "level": 0,
                        }
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(
                        {
                            "type": "from_import",
                            "module": module,
                            "alias": alias.asname,  # Mantido para testes
                            "name": alias.name,
                            "line": node.lineno,
                            "level": node.level,
                        }
                    )
        return imports

    def _categorize_imports(self, imports: list[dict]) -> dict[str, list]:
        categorized = {"stdlib": [], "third_party": [], "local": []}
        for imp in imports:
            module = imp["module"]
            base = module.split(".")[0] if module else ""

            if imp["level"] > 0:
                categorized["local"].append(imp)
            elif base in self.STDLIB_MODULES:
                categorized["stdlib"].append(imp)
            elif module and "." in module:
                categorized["local"].append(imp)
            elif base and base[0].islower() and base not in self.STDLIB_MODULES:
                categorized["local"].append(imp)
            else:
                categorized["third_party"].append(imp)
        return categorized

    def _assess_severity(self, imp: dict) -> str:
        if self.warn_wildcard_imports and imp.get("name") == "*":
            return "medium"
        if imp["level"] > self.max_relative_import_level:
            return "medium"
        return "info"

    def _generate_message(self, imp: dict, categorized: dict) -> str:
        cat = self._get_category(imp, categorized)
        name = imp.get("name")

        if imp["type"] == "import":
            msg = f"Import: {imp['module']} ({cat})"
        else:
            target = name if name else "*"
            msg = f"Import: {imp['module']} {target} ({cat})"

        if imp.get("name") == "*":
            msg += " [WILDCARD]"
        return msg

    def _generate_hint(self, imp: dict) -> str:
        hints = []
        if imp.get("name") == "*":
            hints.append("Evite wildcard imports (*).")

        if imp.get("alias"):
            hints.append(f"Alias: {imp['alias']}")

        return " | ".join(hints)

    def _get_category(self, imp: dict, categorized: dict) -> str:
        """Helper para retornar a categoria do import."""
        for c, items in categorized.items():
            if imp in items:
                return c
        return "unknown"

    def _create_summary(self, imports: list, categorized: dict) -> dict:
        unique = set(imp["module"] for imp in imports if imp["module"])
        nodes = list(unique)  # Lista para serialização JSON

        wildcard_count = sum(1 for imp in imports if imp.get("name") == "*")
        relative_count = sum(1 for imp in imports if imp["level"] > 0)

        return {
            # FIX: Adicionada a chave issues_found e status
            "issues_found": len(imports),
            "status": "completed",
            "total_imports": len(imports),
            "wildcard_imports": wildcard_count,
            "relative_imports": relative_count,
            "stdlib_count": len(categorized["stdlib"]),
            "third_party_count": len(categorized["third_party"]),
            "local_count": len(categorized["local"]),
            "unique_modules": len(unique),
            "dependency_graph": {
                "nodes": nodes,
                "node_count": len(nodes),
                "categories": categorized,
            },
        }
