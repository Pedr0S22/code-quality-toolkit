# Integration Tests - Quick Start

## O que são testes de integração com métricas?

Testes que verificam o **fluxo completo** de análise de código: desde a descoberta de arquivos, passando pelos plugins, até a agregação final de métricas.

## Estrutura

```
tests/integration/
├── __init__.py
├── conftest.py                          # Fixtures reutilizáveis
├── test_metrics_integration.py           # Suite principal (11 testes)
├── README_INTEGRATION_TESTS.md          # Documentação completa
```

## Testes Implementados (11 testes ✅)

### `TestMetricsIntegration` (8 testes)
- ✅ `test_metrics_collection_single_plugin` - Coleta com um plugin
- ✅ `test_metrics_aggregation` - Agregação completa
- ✅ `test_metrics_severity_distribution` - Categorização por severidade
- ✅ `test_metrics_top_offenders` - Identificação de arquivos problemáticos
- ✅ `test_metrics_plugin_breakdown` - Breakdown por plugin
- ✅ `test_metrics_report_serialization` - JSON serialization
- ✅ `test_metrics_empty_project` - Projeto sem problemas
- ✅ `test_metrics_consistency_across_runs` - Consistência entre runs

### `TestMetricsComparison` (2 testes)
- ✅ `test_metrics_regression_detection` - Detecta piora
- ✅ `test_metrics_improvement_detection` - Detecta melhoria

### `TestMetricsReporting` (1 teste)
- ✅ `test_metrics_report_completeness` - Integridade do relatório

## Correr os Testes

```bash
# Todos os testes de integração
cd DEV/code_quality_toolkit
python -m pytest tests/integration/ -v

# Teste específico
python -m pytest tests/integration/test_metrics_integration.py::TestMetricsIntegration::test_metrics_collection_single_plugin -v

# Com cobertura
python -m pytest tests/integration/ --cov=toolkit.core --cov-report=html
```

## Arquitetura

```
┌─────────────────────┐
│   Projeto Python    │
│ (Arquivos .py)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  run_analysis()     │
│  (engine.py)        │
└──────────┬──────────┘
           │
           ├─────► StyleCheckerPlugin
           ├─────► DuplicateCodeCheckerPlugin
           └─────► [Outros Plugins]
           │
           ▼
┌─────────────────────┐
│  Resultados Raw     │
│  (FileReport[])     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  aggregate()        │
│  (aggregator.py)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Relatório Final    │
│  (UnifiedReport)    │
└─────────────────────┘
```

## Fixtures Disponíveis

**Em `conftest.py`:**

```python
@pytest.fixture
def project_with_issues(tmp_path: Path) -> Path:
    """Cria projeto com arquivos contendo variados problemas."""

@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Arquivo Python limpo."""

@pytest.fixture
def messy_python_file(tmp_path: Path) -> Path:
    """Arquivo com problemas de estilo."""

@pytest.fixture
def duplicated_code_file(tmp_path: Path) -> Path:
    """Arquivo com duplicação de código."""
```

## Exemplo: Criar Novo Teste

```python
def test_novo_aspecto(self, project_with_issues: Path, toolkit_config: ToolkitConfig) -> None:
    """Testa novo aspecto de métricas."""
    
    # 1. Executar análise
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files, plugin_status = run_analysis(
        root=project_with_issues,
        plugins=plugins,
        config=toolkit_config,
    )
    
    # 2. Agregar métricas
    report = aggregate(files, plugin_status)
    
    # 3. Validar resultados
    assert report["summary"]["total_files"] >= 1
    assert "total_issues" in report["summary"]
```

## Estrutura do Relatório

```python
{
    "summary": {
        "total_files": int,
        "total_issues": int,
        "issues_by_plugin": {"PluginName": int, ...},
        "issues_by_severity": {"info": int, "low": int, ...},
        "top_offenders": [{"file": str, "issues": int}, ...],
    },
    "analysis_metadata": {
        "tool_version": str,
        "plugins_executed": [str, ...],
        "status": str,  # "completed" | "partial" | "failed"
        "timestamp": str,  # ISO 8601
    },
    "details": {...}  # Detalhes adicionais
}
```

## Status Atual

✅ **11 testes passando**
- Cobertura de coleta e agregação de métricas
- Validação de estrutura e valores
- Testes de consistência e comparação

## Próximos Passos

1. **Performance Tests** - Medir tempo de análise
2. **Snapshot Tests** - Comparar com snapshots conhecidos
3. **Regression Detection** - Detectar automaticamente regressões
4. **Metrics History** - Rastrear histórico ao longo do tempo

## Recursos

- `tests/integration/README_INTEGRATION_TESTS.md` - Documentação completa
- `tests/cli/test_cli_e2e.py` - Testes end-to-end do CLI
- `src/toolkit/core/` - Core modules (engine, aggregator, contracts)
