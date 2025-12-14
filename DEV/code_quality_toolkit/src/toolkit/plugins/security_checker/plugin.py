# Security checker to see any malicious intent that might be present on any file
from __future__ import annotations

import json
from pathlib import Path

import os
import tempfile
from typing import Any

# Imports do Bandit (a ferramenta que faz o trabalho)
try:
    from bandit.core.config import BanditConfig
    from bandit.core.constants import HIGH, LOW, MEDIUM
    from bandit.core.manager import BanditManager

except ImportError:
    # Se o Bandit não estiver instalado, estas classes não existem.
    # O plugin vai falhar, mas o nosso 'except' no 'analyze' vai pegar.
    BanditConfig = None
    BanditManager = None
    LOW, MEDIUM, HIGH = None, None, None

# 2. Imports do Core do Projeto
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


# --- TAREFA 9: Implementação da API  ---
class Plugin:
    """
    Plugin de Segurança: Um "wrapper" (adaptador) que executa o Bandit
    e traduz os seus resultados para o formato do Toolkit.

    """
   
    def generate_dashboard(self, aggregated_results: list[dict]) -> None:
        """
        Gera o dashboard D3.js.
        PROCESSA A LISTA PLANA DE ERROS (FLAT LIST).
        """
        
        # 1. Localização
        output_dir = Path(__file__).parent 

        # 2. Inicializar Contadores
        total_issues = len(aggregated_results)
        severity_counts = {"high": 0, "medium": 0, "low": 0, "info": 0}
        rule_counts = {} 
        
        # O Engine removeu a chave 'file', então deixamos a lista vazia
        top_files = [] 

        # 3. LOOP CORRIGIDO (Itera direto no erro)
        for issue in aggregated_results:
            
            # --- DEBUG (Opcional, pode remover depois) ---
            # print(f"Processando erro: {issue.get('code')}")
            
            # 1. Contar Severidade
            # O seu dado mostra 'medium', então .lower() garante que bate com a chave
            sev = issue.get("severity", "info").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
            
            # 2. Contar Regra (B307, B608, etc.)
            code = issue.get("code", "UNKNOWN")
            rule_counts[code] = rule_counts.get(code, 0) + 1

        # 4. Formatar para o JSON do Dashboard
        sev_data = [{"severity": k, "count": v} for k, v in severity_counts.items() if v > 0]
        
        rule_data = [{"code": k, "count": v} for k, v in rule_counts.items()]
        rule_data.sort(key=lambda x: x["count"], reverse=True)

        dashboard_data = {
            "metrics": {
                "total_files": "Unknown", 
                "total_issues": total_issues
            },
            "severity_counts": sev_data,
            "rule_counts": rule_data,
            "top_files": top_files # Vazio para não crashar o JS
        }

        # 5. Gravar
        import json
        data_json = json.dumps(dashboard_data)
        html_content = self._get_html_template(data_json)

        filename = "security_checker_dashboard.html"
        output_path = output_dir / filename
        
        try:
            output_path.write_text(html_content, encoding="utf-8")
            print(f"✅ Dashboard salvo com {total_issues} issues!")
        except Exception as e:
            print(f"Erro ao salvar dashboard: {e}")

    def _get_html_template(self, data_json: str) -> str:
                """
                Retorna o template HTML/D3 cumprindo estritamente a SPEC.md:
                - Dimensões: 1066x628 px
                - Framework: D3.js v7
                - Dados: Injetados via JSON
                """
                return f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SecurityChecker Dashboard</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f4f4f4;
                    display: static;
                    justify-content: center;
                }}
                
                /* MANDATORY DIMENSIONS: 1066px x 628px */
                .chart-container {{ 
                    width: 1066px; 
                    height: 628px; 
                    background: white; 
                    border: 1px solid #ccc; 
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    position: static; /* Para posicionamento absoluto interno se necessário */
                    box-sizing: border-box; /* Garante que padding não aumenta o tamanho total */
                }}

                /* Estilos auxiliares para tooltips ou textos */
                .tooltip {{
                    position: absolute;
                    text-align: center;
                    padding: 6px;
                    font: 12px sans-serif;
                    background: #000;
                    color: #000;
                    border-radius: 4px;
                    pointer-events: none;
                    opacity: 0;
                }}
            </style>
        </head>
        <body>

        <div id="app" class="chart-container"></div>

        <script>
            // DADOS INJETADOS PELO PYTHON
            // A estrutura esperada vem do generate_dashboard:
            // {{ metrics: {{...}}, severity_counts: [...], rule_counts: [...], top_files: [...] }}
            const data = {data_json};

            // Configurações de Dimensão (Obrigatórias)
            const width = 1066;
            const height = 628;
            const margin = {{top: 80, right: 30, bottom: 40, left: 60}};

            // Criar o Canvas SVG
            const svg = d3.select("#app")
                .append("svg")
                .attr("width", width)
                .attr("height", height)
                .style("background-color", "#fff");

            // ---------------------------------------------------------
            // 1. HEADER (Cabeçalho com Métricas)
            // ---------------------------------------------------------
            
            // Fundo do Header (Vermelho Security)
            svg.append("rect")
                .attr("x", 0).attr("y", 0)
                .attr("width", width).attr("height", 70)
                .attr("fill", "#dc3545"); // Bootstrap Danger Red

            // Título do Plugin
            svg.append("text")
                .attr("x", 20).attr("y", 45)
                .attr("fill", "white")
                .style("font-size", "24px").style("font-weight", "bold")
                .text("SecurityChecker Analysis");

            // Métricas no Header
            const metricsGroup = svg.append("g").attr("transform", "translate(750, 20)");
            
            // Box 1: Total Files
            metricsGroup.append("rect").attr("x", 0).attr("y", 0).attr("width", 140).attr("height", 30).attr("rx", 5).attr("fill", "rgba(255,255,255,0.2)");
            metricsGroup.append("text").attr("x", 70).attr("y", 20).attr("text-anchor", "middle").attr("fill", "white").style("font-size", "14px").style("font-weight", "bold")
                .text(`Files: ${{data.metrics.total_files}}`);

            // Box 2: Total Issues
            metricsGroup.append("rect").attr("x", 150).attr("y", 0).attr("width", 140).attr("height", 30).attr("rx", 5).attr("fill", "rgba(255,255,255,0.2)");
            metricsGroup.append("text").attr("x", 220).attr("y", 20).attr("text-anchor", "middle").attr("fill", "white").style("font-size", "14px").style("font-weight", "bold")
                .text(`Issues: ${{data.metrics.total_issues}}`);

            // ---------------------------------------------------------
            // 2. LAYOUT GRID
            // ---------------------------------------------------------
            
            // Definir áreas
            const col1X = 50;  // Esquerda (Gráfico Severidade)
            const col2X = 550; // Direita (Top Offenders)
            const contentY = 120;

            // ---------------------------------------------------------
            // 3. CHART 1: SEVERITY COUNTS (Bar Chart)
            // ---------------------------------------------------------
            
            svg.append("text")
                .attr("x", col1X).attr("y", contentY - 10)
                .style("font-size", "18px").style("font-weight", "bold").attr("fill", "#333")
                .text("Issues by Severity");

            const sevWidth = 450;
            const sevHeight = 200;
            const sevGroup = svg.append("g").attr("transform", `translate(${{col1X}}, ${{contentY}})`);

            // Preparar dados para D3 (Array de objetos)
            const sevData = data.severity_counts || [];
            
            // Escalas
            const xSev = d3.scaleBand()
                .domain(sevData.map(d => d.severity))
                .range([0, sevWidth])
                .padding(0.3);

            const ySev = d3.scaleLinear()
                .domain([0, d3.max(sevData, d => d.count) || 10]) // fallback para evitar domain [0,0]
                .nice()
                .range([sevHeight, 0]);

            // Eixos
            sevGroup.append("g")
                .attr("transform", `translate(0,${{sevHeight}})`)
                .call(d3.axisBottom(xSev))
                .selectAll("text").style("font-size", "12px").style("text-transform", "capitalize");
            
            sevGroup.append("g").call(d3.axisLeft(ySev).ticks(5));

            // Barras
            const colorMap = {{ "high": "#dc3545", "medium": "#ffc107", "low": "#17a2b8", "info": "#6c757d" }};

            sevGroup.selectAll(".bar")
                .data(sevData)
                .enter().append("rect")
                .attr("class", "bar")
                .attr("x", d => xSev(d.severity))
                .attr("y", d => ySev(d.count))
                .attr("width", xSev.bandwidth())
                .attr("height", d => sevHeight - ySev(d.count))
                .attr("fill", d => colorMap[d.severity] || "steelblue");

            // Labels nas barras
            sevGroup.selectAll(".label")
                .data(sevData)
                .enter().append("text")
                .attr("x", d => xSev(d.severity) + xSev.bandwidth()/2)
                .attr("y", d => ySev(d.count) - 5)
                .attr("text-anchor", "middle")
                .style("font-size", "12px").style("font-weight", "bold")
                .text(d => d.count);


            // ---------------------------------------------------------
            // 4. CHART 2: TOP RULES / VULNERABILITIES (Horizontal Bar)
            // ---------------------------------------------------------
            
            const rulesY = contentY + sevHeight + 60;
            
            svg.append("text")
                .attr("x", col1X).attr("y", rulesY - 10)
                .style("font-size", "18px").style("font-weight", "bold").attr("fill", "#333")
                .text("Top Vulnerabilities Found");

            const ruleGroup = svg.append("g").attr("transform", `translate(${{col1X}}, ${{rulesY}})`);
            const ruleData = (data.rule_counts || []).slice(0, 5); // Top 5 apenas

            const xRule = d3.scaleLinear()
                .domain([0, d3.max(ruleData, d => d.count) || 5])
                .range([0, sevWidth - 50]); // Deixa espaço para labels

            const yRule = d3.scaleBand()
                .domain(ruleData.map(d => d.code))
                .range([0, 150])
                .padding(0.2);

            // Eixo Y (Códigos)
            ruleGroup.append("g").call(d3.axisLeft(yRule));

            // Barras Horizontais
            ruleGroup.selectAll(".rule-bar")
                .data(ruleData)
                .enter().append("rect")
                .attr("x", 1)
                .attr("y", d => yRule(d.code))
                .attr("width", d => xRule(d.count))
                .attr("height", yRule.bandwidth())
                .attr("fill", "#6610f2"); // Roxo para diferenciar

            // Labels de contagem à direita das barras
            ruleGroup.selectAll(".rule-label")
                .data(ruleData)
                .enter().append("text")
                .attr("x", d => xRule(d.count) + 5)
                .attr("y", d => yRule(d.code) + yRule.bandwidth()/2 + 4)
                .style("font-size", "11px").style("font-weight", "bold")
                .text(d => d.count);


            // ---------------------------------------------------------
            // 5. LIST: TOP OFFENDERS (Lista de Texto)
            // ---------------------------------------------------------
            
            svg.append("text")
                .attr("x", col2X).attr("y", contentY - 10)
                .style("font-size", "18px").style("font-weight", "bold").attr("fill", "#333")
                .text("Top Risky Files");

            const listGroup = svg.append("g").attr("transform", `translate(${{col2X}}, ${{contentY}})`);
            
            // Fundo da lista
            listGroup.append("rect")
                .attr("width", 450).attr("height", 420)
                .attr("fill", "#fafafa").attr("stroke", "#eee");

            const offenders = data.top_files || [];

            if (offenders.length === 0) {{
                listGroup.append("text")
                    .attr("x", 225).attr("y", 210)
                    .attr("text-anchor", "middle")
                    .attr("fill", "#28a745")
                    .style("font-size", "16px")
                    .text("✅ No vulnerabilities found!");
            }} else {{
                offenders.forEach((file, i) => {{
                    const yPos = 30 + (i * 40);
                    
                    // Linha separadora
                    if (i > 0) {{
                        listGroup.append("line")
                            .attr("x1", 10).attr("y1", yPos - 25)
                            .attr("x2", 440).attr("y2", yPos - 25)
                            .attr("stroke", "#eee");
                    }}

                    // Nome do Ficheiro (truncado se necessário)
                    let fileName = file.file;
                    if (fileName.length > 50) fileName = "..." + fileName.slice(-47);

                    listGroup.append("text")
                        .attr("x", 15).attr("y", yPos)
                        .style("font-family", "monospace").style("font-size", "12px")
                        .text(`${{i+1}}. ${{fileName}}`);

                    // Badge de contagem
                    listGroup.append("rect")
                        .attr("x", 400).attr("y", yPos - 12)
                        .attr("width", 30).attr("height", 18).attr("rx", 4)
                        .attr("fill", "#dc3545");
                    
                    listGroup.append("text")
                        .attr("x", 415).attr("y", yPos + 1)
                        .attr("text-anchor", "middle")
                        .attr("fill", "white").style("font-size", "11px").style("font-weight", "bold")
                        .text(file.count);
                }});
            }}

        </script>

        </body>
        </html>"""
   

    def __init__(self) -> None:
        """Inicializa o plugin."""
        # Verifica se o import do Bandit funcionou
        # Só avisar se efectivamente não temos o Bandit disponível
        if BanditManager is None:
            print(
                "AVISO: Dependência 'bandit' não instalada. "
                "O SecurityChecker não vai funcionar. Usando verificação fallback."
            )
        # TAREFA 7: Configuração (TOML)
        # O Bandit usa o seu próprio ficheiro, mas podemos definir o nível
        # de severidade que queremos reportar.
        self.report_severity_level = "LOW"  # Reporta Low, Medium, e High

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "SecurityChecker",
            "version": "1.0.0",
            "description": (
                "Deteta vulnerabilidades (eval, pickle, SQLi, etc.) usando o Bandit."
            ),
        }

    def configure(self, config: ToolkitConfig) -> None:
        """
        TAREFA 7: Configura o plugin a partir do ficheiro TOML global.

        """

        # Como não podemos mudar o config.py, temos de verificar se o atributo
        # 'security_report_level' existe ANTES de tentar ler.
        # Se não existir, ele simplesmente ignora e usa o valor 'default' ('LOW')
        # definido no __init__.
        if hasattr(config.rules, "security_report_level"):
            self.report_severity_level = config.rules.security_report_level

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        TAREFA 8: Corre a análise no ficheiro e devolve um Relatório JSON.
        Isto NUNCA DEVE levantar uma exceção (seguindo a Golden Rule).
        """

        try:
            results: list[IssueResult] = []

            # --- Fallback scanner se Bandit não estiver disponível ---
            if BanditManager is None:
                src = source_code or ""
                lines = src.splitlines()

                def find_lineno(substr: str) -> int:
                    for idx, line in enumerate(lines, start=1):
                        if substr in line:
                            return idx
                    return 1

                # Heurísticas simples
                if "eval(" in src:
                    results.append(
                        {
                            "severity": "high",
                            "code": "B307",
                            "message": "Uso de eval() detectado.",
                            "line": find_lineno("eval("),
                            "col": 1,
                            "hint": "Evite usar eval() em código não confiável.",
                        }
                    )

                if "exec(" in src:
                    results.append(
                        {
                            "severity": "high",
                            "code": "B307",
                            "message": "Uso de exec() detectado.",
                            "line": find_lineno("exec("),
                            "col": 1,
                            "hint": "Evite usar exec() em código não confiável.",
                        }
                    )

                if "import pickle" in src or "pickle.load" in src:
                    results.append(
                        {
                            "severity": "medium",
                            "code": "B301",
                            "message": "Uso de pickle detectado.",
                            "line": find_lineno("pickle"),
                            "col": 1,
                            "hint": "Evite usar pickle para dados não confiáveis.",
                        }
                    )

                if "hashlib.md5" in src or ".md5(" in src:
                    results.append(
                        {
                            "severity": "low",
                            "code": "B303",
                            "message": "Uso de hash MD5 detectado.",
                            "line": find_lineno("md5"),
                            "col": 1,
                            "hint": "Use hashes seguros como sha256 para segurança.",
                        }
                    )

                if "os.system" in src and "+" in src:
                    results.append(
                        {
                            "severity": "medium",
                            "code": "B601",
                            "message": (
                                "Chamadas ao sistema com concatenação de strings "
                                "detectadas."
                            ),
                            "line": find_lineno("os.system"),
                            "col": 1,
                            "hint": (
                                "Use chamadas seguras sem "
                                "concatenar input do utilizador."
                            ),
                        }
                    )

                if "%s" in src and "cursor.execute" in src:
                    results.append(
                        {
                            "severity": "high",
                            "code": "B606",
                            "message": "Possível injeção SQL detectada.",
                            "line": find_lineno("cursor.execute"),
                            "col": 1,
                            "hint": (
                                "Use queries parametrizadas em vez de "
                                "formatação direta."
                            ),
                        }
                    )

                if "PASSWORD" in src and "=" in src and ('"' in src or "'" in src):
                    results.append(
                        {
                            "severity": "low",
                            "code": "B105",
                            "message": "Senha hardcoded detectada.",
                            "line": find_lineno("PASSWORD"),
                            "col": 1,
                            "hint": "Nunca guarde segredos em código fonte.",
                        }
                    )

                return {
                    "results": results,
                    "summary": {"issues_found": len(results), "status": "completed"},
                }

            # Como o bandit analisa ficheiros e não linha a linha
            # Criamos um ficheiro temporário para ele analisar
            # Usamos 'delete=False' para o ficheiro não ser apagado
            # imediatamente, para que o Bandit o possa ler.
            with tempfile.NamedTemporaryFile(
                suffix=".py",
                delete=False,
                mode="w",
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(source_code)
                temp_file_path = temp_file.name  # Guardamos o caminho do ficheiro

            try:
                # 2. Criar uma config e um gestor do Bandit
                config = BanditConfig()
                manager = BanditManager(config=config, agg_type="vuln")

                # 3. Mandar o Bandit "descobrir" o nosso ficheiro temporário
                manager.discover_files([temp_file_path])

                # 4. Executar o Bandit (nos ficheiros que ele descobriu)
                # (Isto cumpre as TAREFAS 2, 3, 4, 5, 6 de uma só vez)
                manager.run_tests()

                # 5. Mapear o nosso nível de severidade para o do Bandit
                severity_map = {"LOW": LOW, "MEDIUM": MEDIUM, "HIGH": HIGH}
                report_level = severity_map.get(self.report_severity_level, LOW)

                # 6. Obter os resultados do Bandit
                bandit_issues = manager.get_issue_list(
                    sev_level=report_level, conf_level=LOW
                )

                # 7. TRADUZIR os resultados do Bandit para o nosso formato JSON
                for issue in bandit_issues:
                    severity_translation = {
                        "LOW": "low",
                        "MEDIUM": "medium",
                        "HIGH": "high",
                    }
                    results.append(
                        {
                            "severity": severity_translation.get(issue.severity, "low"),
                            "code": issue.test_id,  # ex: B301 (pickle) ou B307 (eval)
                            "message": issue.text,
                            "line": issue.lineno,
                            "col": issue.col_offset + 1,
                            "hint": f"Bandit Test ID: {issue.test_id}",
                        }
                    )

            finally:
                # 8. Limpar (apagar o ficheiro temporário), funcionando ou não
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # Devolve uma Resposta de Sucesso
            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }

        except Exception as e:
            # TAREFA 13: Error Handling
            # Apanha todos os outros erros e Devolve uma Resposta de Falha
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Erro interno no BanditSecurityChecker: {str(e)}",
                },
            }
