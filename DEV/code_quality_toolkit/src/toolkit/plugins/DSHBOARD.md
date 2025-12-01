# Dashboard Generation Documentation for Plugins
## Introdução

Cada plugin do Toolkit deve gerar um dashboard próprio, utilizando D3.js, durante o seu analyze().

O objetivo é fornecer visualizações independentes para cada plugin, integradas no relatório final.

## Regras do Dashboard
Tamanho obrigatório
1066 x 628 px

Nome do ficheiro
<plugin_name>_dashboard.html

Localização do ficheiro
src/toolkit/plugins/<plugin>/

Gerado dentro do método:
def analyze(self, source_code, file_path):
    ...
    self.generate_dashboard(results, output_dir)

## Dados disponíveis para o dashboard

Cada plugin deve gerar pelo menos:

Número total de issues

Severidades

Ficheiros afetados

Informação relevante ao plugin

Estes dados vêm do dicionário results devolvido pelo plugin.

## Exemplo de Estrutura HTML + D3.js
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <title>Plugin Dashboard</title>
</head>
<body>
<div id="app"></div>

<script>
    const data = {{DATA_JSON}};

    const svg = d3.select("#app")
        .append("svg")
        .attr("width", 1066)
        .attr("height", 628);

    // Example: Bar chart
    svg.selectAll("rect")
        .data(data.severity_counts)
        .enter()
        .append("rect")
        .attr("x", (d,i)=>i*100)
        .attr("y", d => 500 - d.count*10)
        .attr("width", 80)
        .attr("height", d => d.count*10);
</script>

</body>
</html>

## Função Auxiliar Recomendada
def generate_dashboard(self, results, output_dir):
    dashboard_file = output_dir / f"{self.name}_dashboard.html"
    html = self.build_html(results)
    dashboard_file.write_text(html, encoding="utf-8")

## Conclusão

Este documento define:

Como criar dashboards

Como integrar D3.js

Onde guardar ficheiros

Como estruturar o HTML

O fluxo de geração dentro do plugin

