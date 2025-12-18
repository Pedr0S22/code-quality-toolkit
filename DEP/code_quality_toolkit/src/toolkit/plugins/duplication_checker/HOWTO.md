# HOWTO – Duplicate Code Checker Plugin

## Membros
- Tomás Neto 2023229944 @Tomass24
- Vasco Alves 2022228207 @vasco_alves
- Augusto Hunguana 2023250703 @AugustoHunguana

---

## 1. O que este plugin faz

O **DuplicationChecker** procura **código duplicado** entre vários ficheiros Python.  
Baseia-se na regra **R0801 do pylint**, que é um método robusto e amplamente usado.

Ele:

- percorre diretórios e recolhe todos os ficheiros `.py`
- executa pylint internamente
- transforma cada ocorrência em IssueResult
- gera um dashboard HTML com os resultados

---

## 2. Como correr o plugin via CLI

### Análise simples
```
python -m toolkit.core.cli analyze <path> --plugins DuplicationChecker
```

Exemplo:
```
python -m toolkit.core.cli analyze src/ --plugins DuplicationChecker
```

O relatório final incluirá:

- lista de duplicações
- metadata
- contagem total

---

## 3. Como gerar o dashboard HTML

Depois de obteres o relatório:

```python
from toolkit.plugins.duplicate_code_checker.plugin import Plugin

plugin = Plugin()
report = plugin.analyze("", "./meu_projeto")

plugin.generate_dashboard(
    results=report["results"],
    output_dir="./dashboard"
)
```

Será criado o ficheiro:

```
plugin_duplicate_code_checker_dashboard.html
```

---

## 4. Explicação dos métodos principais

### analyze(source_code, file_path)
- aceita um caminho para ficheiro ou diretoria
- recolhe ficheiros `.py`
- executa pylint R0801
- devolve:
  - `results`: lista de duplicações
  - `summary`: número total de duplicações

### render_html(results)
Usa Jinja2 para transformar os resultados num template HTML.

### generate_dashboard(results, output_dir)
Cria um ficheiro HTML final, pronto para abrir no browser.

---

## 5. Requisitos

### Dependências necessárias
- `pylint` (obrigatório)
- `jinja2` (para dashboard)

Instalação:
```
pip install pylint jinja2
```

---

## 6. Interpretação do dashboard

O dashboard inclui:

- número total de duplicações
- tabela com ficheiros e linhas afetadas
- mensagens geradas pelo pylint
- nível de severidade e sugestões de refactoring

---

## 7. O que este plugin "já cumpre"

- deteção real de duplicação  
- relatório estruturado compatível com o Core  
- dashboard HTML funcional  
- renderização separada (boas práticas)  
- integração com Jinja2  
- suporte total aos testes requeridos  


---

## 8. Conclusão

Este HOWTO explica:

- como correr o plugin  
- como gerar o dashboard  
- como interpretar o output  
