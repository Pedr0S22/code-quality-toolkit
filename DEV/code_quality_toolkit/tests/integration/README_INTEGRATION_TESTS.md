# Integration Tests with Metrics

## Visão Geral

Os testes de integração com métricas verificam o fluxo completo de análise de código:

```
Projeto Python → Análise de Plugins → Agregação de Métricas → Relatório Final
```

## Estrutura de Diretórios

```
tests/integration/
├── __init__.py
├── conftest.py                      # Fixtures compartilhadas
├── test_metrics_integration.py       # Suite principal de testes
├── test_performance_metrics.py       # Testes de performance
└── test_metrics_comparison.py        # Comparação de métricas entre runs
```

## Componentes Chave

### 1. **Fixtures (conftest.py)**

Fornece dados de teste reutilizáveis:

```python
@pytest.fixture
def project_with_issues(tmp_path: Path) -> Path:
    """Cria projeto com arquivos contendo problemas."""
    # Implementação
```

**Tipos de fixtures disponíveis:**
- `sample_python_file`: Arquivo Python limpo
- `messy_python_file`: Arquivo com problemas de estilo
- `duplicated_code_file`: Arquivo com duplicação
- `project_with_issues`: Projeto completo com variados problemas

### 2. **Classes de Testes**

#### `TestMetricsIntegration`
Testa coleta e agregação de métricas:

```python
def test_metrics_collection_single_plugin(self, temp_project: Path) -> None:
    """Testa coleta de métricas usando um único plugin."""
    engine = Engine(project_root=str(temp_project))
    files = engine.analyze(
        target=str(temp_project),
        plugins=["StyleChecker"],
    )
    # Asserções
```

**Métodos principais:**
- `test_metrics_collection_single_plugin()`: Análise com um plugin
- `test_metrics_aggregation()`: Agregação completa
- `test_metrics_severity_distribution()`: Categorização por severidade
- `test_metrics_top_offenders()`: Identificação de arquivos problemáticos
- `test_metrics_plugin_breakdown()`: Breakdown por plugin
- `test_metrics_report_serialization()`: JSON serialization
- `test_metrics_consistency_across_runs()`: Consistência entre runs

#### `TestMetricsComparison`
Testa comparação de métricas entre versões:

```python
def test_metrics_regression_detection(self, tmp_path: Path) -> None:
    """Detecta regressão (aumento) em métricas."""
```

**Métodos principais:**
- `test_metrics_regression_detection()`: Detecta piora
- `test_metrics_improvement_detection()`: Detecta melhoria

#### `TestMetricsReporting`
Testa geração e completude de relatórios:

```python
def test_metrics_report_completeness(self, tmp_path: Path) -> None:
    """Verifica que todas as métricas necessárias estão presentes."""
```

## Como Criar Novos Testes de Integração

### Passo 1: Preparar Dados de Teste

```python
def test_novo_teste(self, tmp_path: Path) -> None:
    """Testa novo aspecto de métricas."""
    # Criar arquivos de teste
    file1 = tmp_path / "test.py"
    file1.write_text("x=1\ny=2\n", encoding="utf-8")
    
    # Preparar projeto
    project_root = tmp_path
```

### Passo 2: Executar Análise

```python
    # Criar engine
    engine = Engine(project_root=str(project_root))
    
    # Executar análise
    files = engine.analyze(
        target=str(project_root),
        plugins=["StyleChecker", "DuplicateCodeChecker"],
    )
```

### Passo 3: Agregar Métricas

```python
    # Definir status dos plugins
    plugin_status = {
        "StyleChecker": "completed",
        "DuplicateCodeChecker": "completed",
    }
    
    # Agregar resultados
    report = aggregate(files, plugin_status)
```

### Passo 4: Validar Resultados

```python
    # Validar relatório
    assert validate_unified_report(report)
    
    # Verificar métricas específicas
    assert report["summary"]["total_files"] >= 1
    assert "total_issues" in report["summary"]
```

## Padrões de Teste

### Padrão 1: Teste de Estrutura

Verifica se o relatório tem a estrutura correta:

```python
def test_report_structure(self, temp_project: Path) -> None:
    engine = Engine(project_root=str(temp_project))
    files = engine.analyze(target=str(temp_project), plugins=["StyleChecker"])
    report = aggregate(files, {"StyleChecker": "completed"})
    
    # Verificar chaves necessárias
    assert "summary" in report
    assert "analysis_metadata" in report
    assert "files" in report
```

### Padrão 2: Teste de Valores

Verifica se os valores fazem sentido:

```python
def test_metric_values_validity(self, temp_project: Path) -> None:
    engine = Engine(project_root=str(temp_project))
    files = engine.analyze(target=str(temp_project), plugins=["StyleChecker"])
    report = aggregate(files, {"StyleChecker": "completed"})
    
    # Verificar valores não-negativos
    assert report["summary"]["total_files"] >= 0
    assert report["summary"]["total_issues"] >= 0
```

### Padrão 3: Teste de Consistência

Verifica se o sistema é consistente:

```python
def test_consistency(self, temp_project: Path) -> None:
    engine = Engine(project_root=str(temp_project))
    
    # Primeira run
    files1 = engine.analyze(target=str(temp_project), plugins=["StyleChecker"])
    report1 = aggregate(files1, {"StyleChecker": "completed"})
    
    # Segunda run
    files2 = engine.analyze(target=str(temp_project), plugins=["StyleChecker"])
    report2 = aggregate(files2, {"StyleChecker": "completed"})
    
    # Comparar resultados
    assert report1["summary"]["total_issues"] == report2["summary"]["total_issues"]
```

### Padrão 4: Teste de Serialização

Verifica se dados podem ser serializados:

```python
def test_json_serialization(self, temp_project: Path) -> None:
    engine = Engine(project_root=str(temp_project))
    files = engine.analyze(target=str(temp_project), plugins=["StyleChecker"])
    report = aggregate(files, {"StyleChecker": "completed"})
    
    # Serializar para JSON
    json_str = json.dumps(report, indent=2)
    
    # Desserializar e validar
    deserialized = json.loads(json_str)
    assert validate_unified_report(deserialized)
```

## Executar Testes de Integração

```bash
# Todos os testes de integração
python -m pytest tests/integration/ -v

# Teste específico
python -m pytest tests/integration/test_metrics_integration.py::TestMetricsIntegration::test_metrics_collection_single_plugin -v

# Com cobertura
python -m pytest tests/integration/ --cov=toolkit.core --cov-report=html

# Com output detalhado
python -m pytest tests/integration/ -vv -s
```

## Estrutura do Relatório (Schema)

```python
{
    "summary": {
        "total_files": int,
        "total_issues": int,
        "issues_by_plugin": {
            "PluginName": int,
            ...
        },
        "issues_by_severity": {
            "info": int,
            "low": int,
            "medium": int,
            "high": int,
        },
        "top_offenders": [
            {"file": str, "issues": int},
            ...
        ]
    },
    "analysis_metadata": {
        "tool_version": str,
        "plugins_executed": [str, ...],
        "status": "completed" | "partial" | "failed",
        "timestamp": str,  # ISO 8601 com Z
    },
    "files": [
        {
            "file": str,
            "plugins": [
                {
                    "plugin": str,
                    "results": [
                        {
                            "code": str,
                            "message": str,
                            "severity": str,
                            "line": int,
                            ...
                        },
                        ...
                    ],
                    "summary": {
                        "issues_found": int,
                        "status": str,
                    }
                },
                ...
            ]
        },
        ...
    ]
}
```

## Dicas Práticas

### 1. Use Fixtures Reutilizáveis
```python
# ❌ Evitar
def test_a(self, tmp_path): 
    file = tmp_path / "test.py"
    file.write_text("x=1\n")
    # ...

def test_b(self, tmp_path):
    file = tmp_path / "test.py"
    file.write_text("x=1\n")
    # ...

# ✅ Preferir
def test_a(self, messy_python_file):
    # usar messy_python_file
    
def test_b(self, messy_python_file):
    # usar messy_python_file
```

### 2. Teste Casos Limite
```python
# Projeto vazio
def test_empty_project(self, tmp_path: Path) -> None:
    engine = Engine(project_root=str(tmp_path))
    files = engine.analyze(...)
    # Verificar comportamento com zero arquivos
```

### 3. Valide Sempre a Estrutura
```python
# Sempre incluir validação
report = aggregate(files, plugin_status)
assert validate_unified_report(report)  # ✅
```

### 4. Use Descritores Claros
```python
# ❌ Evitar
def test_m1(self): pass

# ✅ Preferir
def test_metrics_collection_with_multiple_plugins_returns_all_results(self):
    pass
```

## Integração com CI/CD

```yaml
# .github/workflows/test.yml
- name: Run integration tests
  run: |
    export PYTHONPATH=${{ github.workspace }}/src
    python -m pytest tests/integration/ -v --junitxml=results.xml
```

## Recursos Relacionados

- `toolkit.core.engine.Engine`: Motor de análise
- `toolkit.core.aggregator.aggregate()`: Função de agregação
- `toolkit.core.contracts`: Esquemas de validação
- `tests/cli/test_cli_e2e.py`: Testes E2E do CLI

## Próximos Passos

1. **Performance Tests**: Adicionar testes de performance em `test_performance_metrics.py`
2. **Snapshot Tests**: Comparar relatórios com snapshots conhecidos
3. **Regression Detection**: Detectar automaticamente regressões de qualidade
4. **Metrics History**: Rastrear histórico de métricas ao longo do tempo
