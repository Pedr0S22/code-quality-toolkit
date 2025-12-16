# HOWTO – BasicMetrics Plugin

## Membros
- Tomás Neto — 2023229944 — @Tomass24  
- Vasco Alves — 2022228207 — @vasco_alves  
- Augusto Hunguana — 2023250703 — @AugustoHunguana  


## 1. O que o plugin faz

O `BasicMetrics` calcula:

- total de linhas  
- linhas lógicas  
- linhas de comentário  
- linhas em branco  
- docstrings  
- métricas de Halstead (se `radon` estiver instalada)  

Além disso:

- gera issues quando métricas excedem limites  
- permite gerar um dashboard HTML  
- nunca lança exceções para o engine  


## 2. Como executar o plugin

### 2.1. Apenas o BasicMetrics
```
python -m toolkit.core.cli analyze <path> --plugins BasicMetrics
```

### 2.2. Com outros plugins
```
python -m toolkit.core.cli analyze src/ \
    --plugins StyleChecker,CyclomaticComplexity,BasicMetrics
```

### 2.3. Guardar o relatório
```
python -m toolkit.core.cli analyze src/ \
    --plugins BasicMetrics --out metrics.json
```


## 3. Como gerar o dashboard

O plugin possui dois métodos:

```python
plugin.render_html(results)
plugin.generate_dashboard(results, output_dir)
```

Para gerar um dashboard:

```python
from toolkit.plugins.basic_metrics.plugin import Plugin

plugin = Plugin()
html = plugin.render_html(results)
plugin.generate_dashboard(results, "dashboards")
```

Será criado:

```
dashboards/plugin_basic_metrics_dashboard.html
```

Template usado:
```
toolkit/plugins/basic_metrics/dashboard.html
```


## 4. Como configurar

No ficheiro `toolkit.toml`:

```toml
[rules]
metrics_report_level = "LOW"
```

Atualmente este valor é apenas armazenado, sem alterar thresholds.  


## 5. Dependências

### Opcional: `radon`
Instalação:

```
pip install radon
```

Sem radon:
- Halstead = 0.0  
- contagens feitas por heurística  

Com radon:
- métricas mais precisas  


## 6. Comportamento em caso de erro

O plugin NUNCA crasha o motor.  
Qualquer exceção é capturada:

```
summary.status = "failed"
summary.error = "<detalhe>"
results = []
```


## 7. Funcionalidades implementadas

### Implementado neste sprint
- métricas completas (linhas, docstrings, Halstead)  
- issues automáticas  
- dashboard HTML com Jinja2  
- integração com CLI  
- fallback sem radon  
 


## 8. Resumo

Este HOWTO explica:

- como correr o plugin  
- como gerar dashboards  
- como configurar  
- como interpretar resultados  

