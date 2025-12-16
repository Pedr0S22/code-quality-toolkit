# BasicMetrics Plugin

## Membros
- Tomás Neto — 2023229944 — @Tomass24  
- Vasco Alves — 2022228207 — @vasco_alves  
- Augusto Hunguana — 2023250703 — @AugustoHunguana  


## 1. Objetivo do Plugin

O **BasicMetrics** é um plugin do *Code Quality Toolkit* responsável por calcular métricas fundamentais de um ficheiro de código.  
Estas métricas permitem avaliar dimensões estruturais, documentação e complexidade do código, incluindo:

- número de linhas totais e lógicas  
- comentários  
- docstrings  
- linhas em branco  
- métricas de Halstead (se o módulo `radon` estiver disponível)  
- geração automática de *issues* quando certos limites são ultrapassados  
- **dashboard HTML** baseado em *Jinja2* para visualização dos resultados  


## 2. Funcionalidades Atuais

O plugin aplica várias análises ao código-fonte:

### Contagem de Linhas
- `total_lines`  
- `logical_lines`  
- `comment_lines`  
- `blank_lines`  
- `docstring_lines`  

### Métricas de Halstead
Se `radon` estiver instalado:
- `h_volume`  
- `h_difficulty`  
- `h_effort`  
- `h_bugs`  

Caso contrário, devolvem:
- `0.0`

### Dashboard Jinja2
O plugin suporta geração de um dashboard:

- `render_html(results)` → devolve HTML renderizado  
- `generate_dashboard(results, output_dir)` → cria o ficheiro  
  `plugin_basic_metrics_dashboard.html`

O ficheiro baseia-se no template Jinja2:
```
toolkit/plugins/basic_metrics/dashboard.html
```


## 3. Issues Geradas

Com base nas métricas, o plugin gera *issues* automáticas:

| Métrica | Regra | Severidade |
|--------|--------|-------------|
| `total_lines` | >1000 / >2000 / >3000 | low / medium / high |
| `logical_lines` | >100 / >200 / >300 | low / medium / high |
| `comment_lines` | percentagem <10% | low / medium / high |

`blank_lines` e `docstring_lines` **não geram issues** nesta versão.


## 4. Como Usar

### Executar apenas o BasicMetrics
```bash
python -m toolkit.core.cli analyze . --plugins BasicMetrics
```

### Com outros plugins
```bash
python -m toolkit.core.cli analyze src/ \
    --plugins StyleChecker,CyclomaticComplexity,BasicMetrics
```

O relatório contém:
- `results` → lista de issues  
- `summary["metrics"]` → todas as métricas calculadas  


## 5. Integração e Configuração

O plugin lê da configuração (`toolkit.toml`):

```toml
[rules]
metrics_report_level = "LOW"
```

O valor é armazenado mas ainda **não altera thresholds** → reservado para iterações futuras.


## 6. Tratamento de Erros

O plugin segue a “Golden Rule”:  
**nunca crasha o engine**.

Em erro interno:
```json
{
  "results": [],
  "summary": {
    "issues_found": 0,
    "status": "failed",
    "error": "Internal error in BasicMetrics: <detalhe>"
  }
}
```


## 7. Funcionalidades Que Estão de Acordo com o Enunciado

### Implementado
- Métricas essenciais (LOC, comentários, docstrings, Halstead)  
- Issues automáticas  
- Robustez total contra erros  
- Dashboard HTML com Jinja2  
- Integração total com CLI e relatório  

### Não implementado (e não é obrigatório neste sprint)
- métricas agregadas por projeto  
- estatísticas globais  
- ranking de ficheiros  
- contagem de funções/classes  
- D3.js dinâmico para gráficos avançados  

Esses pontos são designados como extensões futuras e **não fazem parte deste sprint**.


## 8. Conclusão

O **BasicMetrics** cumpre integralmente o que o sprint exige:  
✓ métricas completas  
✓ deteção de problemas  
✓ dashboard funcional  
✓ integração com CLI  
✓ documentação técnica atualizada  

