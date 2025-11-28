# Membros:

- Vasco Alves  2022228207  @vasco\_alves
- Augusto Hunguana  2023250703  @AugustoHunguana


## 1. Visão Geral do Uso

O plugin de métricas básicas é executado através da **CLI** do Code Quality Toolkit, tal como os restantes plugins.  
O nome do plugin (na opção `--plugins`) é "BasicMetrics".


Este plugin:

- calcula métricas como:
  - `total_lines` – número total de linhas;
  - `logical_lines` – linhas “lógicas” de código;
  - `comment_lines` – linhas de comentário (não confundir com docstrings);
  - `blank_lines` – linhas em branco;
  - `docstring_lines` – linhas que pertencem a docstrings;
- calcula algumas métricas de **Halstead**:
  - `h_volume`, `h_difficulty`, `h_effort`, `h_bugs`;
- guarda todas estas métricas em `summary["metrics"]` no relatório do plugin;
- gera avisos (issues) quando:
  - o ficheiro é demasiado grande;
  - o número de linhas lógicas é muito elevado;
  - a percentagem de comentários é muito baixa.

O plugin pode ser usado isoladamente ou em conjunto com outros (StyleChecker, CyclomaticComplexity, etc.).


## 2. Como a Análise é Executada

A análise é feita pelo comando `analyze` da CLI do Code Quality Toolkit.  
Alguns exemplos de utilização do plugin `BasicMetrics`:

### 2.1. Executar apenas o BasicMetrics

```bash
python -m toolkit.core.cli analyze . \
    --plugins BasicMetrics \
    --out report_basic_metrics.json
```

- `.` → pasta a analisar (pode ser substituída por `src/`, por exemplo);
- `--plugins BasicMetrics` → executa apenas o plugin de métricas básicas;
- `--out report_basic_metrics.json` → ficheiro onde o relatório final será guardado.

### 2.2. Executar o BasicMetrics juntamente com outros plugins

```bash
python -m toolkit.core.cli analyze . \
    --plugins StyleChecker,CyclomaticComplexity,BasicMetrics \
    --out report.json
```

Neste caso, o `BasicMetrics` é executado em cada ficheiro, em paralelo com os restantes plugins, e as métricas aparecem na secção de detalhes do `report.json`.

Durante a execução:

1. O engine do Toolkit percorre os ficheiros de código.
2. Para cada ficheiro, chama `Plugin.analyze(source_code, file_path)` do BasicMetrics.
3. O plugin calcula as métricas e, se necessário, gera avisos.
4. O resultado é agregado no relatório unificado.


## 3. Configuração do Plugin pelo Utilizador

O plugin lê uma opção de configuração chamada `metrics_report_level` do objeto global `ToolkitConfig.rules`.  
Esta opção permite, numa versão futura, ajustar o “nível de detalhe” ou a sensibilidade do relatório.

Exemplo de configuração no ficheiro `toolkit.toml`:

```toml
[rules]
# Nível de detalhe do relatório de métricas:
# Pode ser "LOW", "MEDIUM" ou "HIGH".
metrics_report_level = "LOW"
```

Na implementação atual do plugin:

- o valor é lido e guardado em `self.report_level`;
- todas as métricas são sempre calculadas;
- os limiares usados para gerar avisos são fixos (não dependem ainda do valor de `metrics_report_level`).

 **Resumo:** o utilizador pode já definir `metrics_report_level` para manter consistência com a configuração global, mas esse valor é principalmente guardado para extensões futuras do plugin.


## 4. Pré-requisitos e Considerações Práticas

### 4.1. Dependência opcional: `radon`

O plugin tenta usar a biblioteca **radon** para obter métricas mais precisas:

- `radon.raw.analyze` para métricas “raw” (LOC, LLOC, etc.);
- `radon.metrics.h_visit` para métricas de Halstead.

Se `radon` estiver instalada no ambiente:

- as métricas `total_lines` e `logical_lines` são calculadas com base na análise da radon;
- as métricas de Halstead (`h_volume`, `h_difficulty`, `h_effort`, `h_bugs`) terão valores reais.

Se `radon` **não** estiver instalada:

- o plugin continua a funcionar (não falha!);
- usa um cálculo simples baseado em texto para as métricas de linhas;
- as métricas de Halstead são devolvidas todas como `0.0`.

Instalação opcional:

```bash
pip install radon
```

### 4.2. Performance

O plugin analisa cada ficheiro individualmente:

- para projetos pequenos/médios o custo é praticamente negligenciável;
- para projetos grandes, o custo depende da combinação:
  - tamanho dos ficheiros (`total_lines`);
  - disponibilidade da `radon` (que aumenta a precisão mas também o trabalho feito).

Mesmo em caso de erro interno inesperado, o `BasicMetrics`:

- apanha a exceção;
- devolve um resumo com `status: "failed"` e uma mensagem em `error`;
- nunca faz a CLI falhar por completo.


## 5. Experiência de Uso para Diferentes Cenários

### 5.1. Ficheiros pequenos e simples

Para scripts curtos (por exemplo, menos de 200 linhas):

- normalmente não são gerados avisos;
- o utilizador pode consultar as métricas em `summary.metrics` para ter uma ideia da dimensão do ficheiro.

Exemplo típico de métricas:

```json
"metrics": {
  "total_lines": 80,
  "logical_lines": 60,
  "comment_lines": 10,
  "blank_lines": 10,
  "docstring_lines": 4,
  "h_volume": 250.0,
  "h_difficulty": 8.0,
  "h_effort": 2000.0,
  "h_bugs": 0.1
}
```

### 5.2. Ficheiros muito grandes

Quando um ficheiro tem mais de **1000 linhas**:

- o plugin pode gerar um aviso com código `"total_lines"` e severidade crescente:
  - mais de 1000 linhas → `low`;
  - mais de 2000 linhas → `medium`;
  - mais de 3000 linhas → `high`.

A mensagem típica será:

> `"File has XXXX total lines. Large files are harder to navigate; consider splitting the module."`

### 5.3. Ficheiros com poucos comentários

Se a percentagem de linhas de comentário (`comment_lines / total_lines`) for:

- inferior a 10% → gera aviso;
- inferior a 5% → severidade pelo menos `medium`;
- inferior a 2% → severidade `high`.

Mensagem típica:

> `"Only X.Y% of lines are comments. Consider adding more explanatory comments and docstrings."`

### 5.4. Interpretação no relatório unificado

No `report.json` final:

- os avisos do BasicMetrics surgem na lista de `results` do plugin, tal como os de outros plugins;
- as métricas numéricas completas ficam em `summary["metrics"]` do plugin, permitindo exportar ou tratar estes dados noutros scripts.

Desta forma, o plugin de Métricas Básicas é útil tanto para:

- ter **informação quantitativa** sobre o código (tamanho, comentários, Halstead);
- como para receber **avisos** sobre ficheiros demasiado grandes ou mal documentados.
