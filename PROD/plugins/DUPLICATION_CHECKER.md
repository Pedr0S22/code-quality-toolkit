# Duplicate Code Checker Plugin

## Membros
- Tomás Neto – 2023229944 – @Tomass24
- Vasco Alves – 2022228207 – @vasco_alves
- Augusto Hunguana – 2023250703 – @AugustoHunguana

---

## 1. Objetivo do Plugin

O **DuplicationChecker** identifica **código duplicado** usando a regra **R0801 do pylint**, que deteta blocos repetidos entre ficheiros Python.  
O plugin integra-se com o *Code Quality Toolkit* e produz:

- lista de ocorrências de duplicação
- metadata sobre o ficheiro e linha
- severidade (“medium”)
- sugestão de refactoring
- dashboard HTML gerado automaticamente

---

## 2. Como o plugin funciona

### 2.1. Normalização da análise
O plugin:

1. Recebe um `file_path` (pode ser ficheiro ou diretoria).
2. Se for diretoria, recolhe todos os `.py` dentro dela.
3. Executa:

```bash
pylint --disable=all --enable=R0801
```

4. Processa cada linha da saída do pylint e converte-a num `IssueResult`.

---

## 3. Campos de cada resultado

Cada duplicação encontrada produz um objeto como:

```json
{
  "plugin": "DuplicationChecker",
  "file": "<path>",
  "entity": "bloco duplicado",
  "line_numbers": [n],
  "similarity": 100,
  "refactoring_suggestion": "Consolidar bloco",
  "metric": "duplicate_code",
  "severity": "medium",
  "code": "R0801",
  "message": "<mensagem pylint>",
  "line": n,
  "col": c
}
```

---

## 4. Dashboard HTML

O plugin inclui duas novas funcionalidades:

### `render_html(results)`
Renderiza o template Jinja2 (`dashboard.html`) com a lista de duplicações.

### `generate_dashboard(results, output_dir)`
Cria automaticamente um ficheiro:

```
plugin_duplicate_code_checker_dashboard.html
```

no diretório indicado.

Este dashboard mostra:

- número de duplicações
- ficheiros envolvidos
- mensagem de cada ocorrência
- visualização HTML com tabela (compatível com futura integração D3.js)

---

## 5. Métodos principais

| Método | Função |
|-------|--------|
| `get_metadata()` | devolve nome, versão e descrição |
| `configure()` | lê configurações globais |
| `analyze(source_code, file_path)` | executa pylint, extrai duplicações, devolve o relatório |
| `render_html(results)` | gera HTML usando template Jinja2 |
| `generate_dashboard(results, output_dir)` | guarda dashboard no disco |

---

## 6. Como usar o plugin

### Analisar ficheiros
```bash
python -m toolkit.core.cli analyze <path> --plugins DuplicationChecker
```

### Gerar dashboard após a análise

```python
from toolkit.plugins.duplicate_code_checker.plugin import Plugin

p = Plugin()
report = p.analyze("", "/caminho/do/projeto")
p.generate_dashboard(report["results"], "./out")
```

Será criado:

```
plugin_duplicate_code_checker_dashboard.html
```

---

## 7. Conformidade com o enunciado

O plugin cumpre:

### Must-Have
- integração com o Core  
- análise por ficheiro/diretoria  
- deteção real de duplicações (via pylint R0801)  
- formatação em IssueResult  

### Should-Have
- dashboard HTML  
- separação clara de renderização e geração de ficheiro  
- compatível com testes automáticos  


---

## 8. Conclusão

O **DuplicationChecker** está completo e funcional, produzindo relatórios e dashboards estruturados e alinhados com o framework do projeto e os requisitos do sprint final.
