# Membros:

- Vasco Alves   2022228207  @vasco_alves
- Tomás Neto 2023229944 @Tomass24

# Plugin de Métricas Básicas (`BasicMetrics`)

Este documento descreve, de forma técnica, o funcionamento interno do plugin **BasicMetrics**, incluindo:

- interface (métodos obrigatórios);
- métricas calculadas;
- formato do relatório devolvido por `analyze`;
- regras usadas para gerar *issues* (avisos);
- comportamento em caso de erro.


## 1. Visão Geral do Uso

O `BasicMetrics` é um plugin do **Code Quality Toolkit** responsável por calcular métricas simples de cada ficheiro de código, tais como:

- número de linhas totais e lógicas;
- número de comentários, linhas em branco e docstrings;
- métricas de Halstead (volume, dificuldade, esforço, bugs).

O plugin pode ser executado via CLI através da opção:

```bash
python -m toolkit.core.cli analyze <caminho> --plugins BasicMetrics
```

As métricas são guardadas em `summary["metrics"]` e alguns valores extremos originam *issues* na lista `results`.


## 2. Interface do Plugin (`Plugin`)

A classe principal está em `basic_metrics/plugin.py` e chama-se `Plugin`.  
Ela implementa os três métodos exigidos pelo contrato do Toolkit:

- `get_metadata(self) -> dict[str, str]`
- `configure(self, config: ToolkitConfig) -> None`
- `analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]`

### 2.1. `get_metadata()`

Devolve os metadados básicos do plugin:

```python
def get_metadata(self) -> dict[str, str]:
    return {
        "name": "BasicMetrics",
        "version": "1.0.0",
        "description": (
            "Reports basic code metrics like LOC, comments, blanks "
            "and Halstead metrics."
        ),
    }
```

- `name` → identificador do plugin (**BasicMetrics**), usado na opção `--plugins`;
- `version` → versão atual do plugin;
- `description` → descrição curta.

### 2.2. `configure(config: ToolkitConfig)`

O método `configure` lê o nível de detalhe a partir da configuração global:

```python
def __init__(self) -> None:
    self.report_level: str = "LOW"

def configure(self, config: ToolkitConfig) -> None:
    if hasattr(config.rules, "metrics_report_level"):
        self.report_level = config.rules.metrics_report_level
```

- A opção esperada na configuração é `metrics_report_level` (em `[rules]`).
- Valores típicos: `"LOW"`, `"MEDIUM"`, `"HIGH"`.
- Na versão atual, este valor é guardado mas ainda não altera os thresholds; é um ponto de extensão para iterações futuras.

### 2.3. `analyze(source_code, file_path)`

O método `analyze` é o ponto de entrada principal.  
A lógica é, em resumo:

1. Calcula um dicionário de métricas numéricas com `_compute_basic_metrics`.
2. Usa `_maybe_build_issue` para decidir se alguma métrica deve gerar um aviso.
3. Devolve:
   - `results`: lista de `IssueResult` (avisos);
   - `summary`: com `issues_found`, `status` e `metrics`.

Em pseudocódigo:

```python
def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
    try:
        metrics = self._compute_basic_metrics(source_code)
        total = int(metrics.get("total_lines", 0))

        issues: list[IssueResult] = []
        for name, val in metrics.items():
            issue_obj = self._maybe_build_issue(name, val, total)
            if issue_obj is not None:
                issues.append(issue_obj)

        return {
            "results": issues,
            "summary": {
                "issues_found": len(issues),
                "status": "completed",
                "metrics": metrics,
            },
        }
    except Exception as exc:
        # Nunca deixa a exceção sair
        return {
            "results": [],
            "summary": {
                "issues_found": 0,
                "status": "failed",
                "error": f"Internal error in BasicMetrics: {exc}",
            },
        }
```

Este padrão cumpre a **Golden Rule** do toolkit: um erro interno do plugin não deve crashar o engine.


## 3. Métricas Calculadas

As métricas são construídas em três etapas:

1. `_docstring_line_numbers(source_code)`  
   - usa o AST para encontrar docstrings de módulo, funções e classes;
   - devolve o conjunto de números de linha que pertencem a docstrings.

2. `_count_comments_and_blanks(source_code, docstring_lines)`  
   - usa o módulo `tokenize` para contar linhas de comentário, excluindo docstrings;
   - conta também as linhas em branco.

3. `_compute_raw_metrics(source_code)`  
   - se a biblioteca `radon` estiver disponível (`RADON_AVAILABLE`):
     - usa `radon.raw.analyze` para obter `loc` e `lloc`;
   - caso contrário, faz um cálculo aproximado baseado em texto.

4. `_compute_halstead_metrics(source_code)`  
   - se `radon.metrics.h_visit` estiver disponível:
     - calcula `h_volume`, `h_difficulty`, `h_effort`, `h_bugs`;
   - se não estiver, devolve 0.0 para todas essas métricas.

### 3.1. Estrutura de `metrics`

O dicionário final é a união de métricas “raw” e Halstead:

```python
{
  "total_lines": int,
  "logical_lines": int,
  "comment_lines": int,
  "blank_lines": int,
  "docstring_lines": int,
  "h_volume": float,
  "h_difficulty": float,
  "h_effort": float,
  "h_bugs": float
}
```

Este dicionário é guardado em:

```python
summary["metrics"] = metrics
```

no relatório do plugin.


## 4. Geração de Issues a partir das Métricas

A função `_maybe_build_issue` analisa algumas métricas específicas e, quando apropriado, cria um `IssueResult` simples.

### 4.1. Ficheiros muito grandes – `total_lines`

Se `metric_name == "total_lines"`:

- sem aviso se `value <= 1000`;
- `low` se `value > 1000`;
- `medium` se `value > 2000`;
- `high` se `value > 3000`.

Exemplo de issue gerada:

```python
{
    "severity": "medium",
    "code": "total_lines",
    "message": "File has 2200 total lines.",
    "hint": "Large files are harder to navigate; consider splitting the module."
}
```

### 4.2. Blocos lógicos extensos – `logical_lines`

Se `metric_name == "logical_lines"`:

- sem aviso se `value <= 100`;
- `low` se `value > 100`;
- `medium` se `value > 200`;
- `high` se `value > 300`.

Mensagem típica:

```python
{
    "severity": "high",
    "code": "logical_lines",
    "message": "File has 350 logical lines.",
    "hint": "Long logical blocks can often be split into smaller functions."
}
```

### 4.3. Poucos comentários – `comment_lines`

Para `metric_name == "comment_lines"`:

- é calculada a percentagem `percent = (value / total_lines) * 100`;
- se `percent >= 10` → não gera aviso;
- se `percent < 10` → gera aviso com severidade:
  - `low` para percentagens entre 5% e 10%;
  - `medium` para percentagens entre 2% e 5%;
  - `high` para percentagens abaixo de 2%.

Exemplo:

```python
{
    "severity": "high",
    "code": "comment_lines",
    "message": "Only 1.5% of lines are comments.",
    "hint": "Consider adding more explanatory comments and docstrings."
}
```

### 4.4. Outras métricas

As métricas `blank_lines`, `docstring_lines` e as métricas de Halstead atualmente **não geram issues explícitos** em `_maybe_build_issue`.  
No entanto, os valores são sempre incluídos em `summary["metrics"]`, podendo ser usados por ferramentas externas ou futuras extensões do plugin.


## 5. Formato do Relatório do Plugin

O relatório devolvido por `analyze` segue o contrato geral do toolkit:

### 5.1. Estrutura em caso de sucesso

```json
{
  "results": [
    {
      "severity": "medium",
      "code": "total_lines",
      "message": "File has 2200 total lines.",
      "hint": "Large files are harder to navigate; consider splitting the module."
    }
  ],
  "summary": {
    "issues_found": 1,
    "status": "completed",
    "metrics": {
      "total_lines": 2200,
      "logical_lines": 1800,
      "comment_lines": 50,
      "blank_lines": 200,
      "docstring_lines": 10,
      "h_volume": 3500.0,
      "h_difficulty": 12.0,
      "h_effort": 42000.0,
      "h_bugs": 0.4
    }
  }
}
```

### 5.2. Estrutura em caso de falha interna

Se ocorrer qualquer exceção dentro de `analyze`, esta é apanhada e é devolvida uma estrutura de falha:

```json
{
  "results": [],
  "summary": {
    "issues_found": 0,
    "status": "failed",
    "error": "Internal error in BasicMetrics: <mensagem>"
  }
}
```

Isto garante que o motor principal continua a correr e que o relatório final pode ser marcado como `"partial"` em vez de o processo crashar.


## 6. Considerações Finais

- O plugin **nunca lança exceções para fora de `analyze`**: qualquer problema interno é reportado através de `status: "failed"`.
- As métricas são sempre calculadas da forma mais completa possível:
  - com `radon`, as medições são mais precisas;
  - sem `radon`, o plugin utiliza um fallback baseado em texto.
- Os thresholds para gerar avisos são conservadores, focando-se em:
  - ficheiros muito grandes;
  - blocos lógicos extensos;
  - baixa densidade de comentários.

Este README serve como documentação técnica para quem quiser **entender ou evoluir o plugin BasicMetrics**, garantindo compatibilidade com o ecossistema do Code Quality Toolkit.
