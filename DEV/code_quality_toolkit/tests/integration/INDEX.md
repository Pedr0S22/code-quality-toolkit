# Testes de Integração com Métricas - Índice

## 📖 Documentação

### 1. **README.md** ⭐ COMECE AQUI
   - Resumo executivo
   - Status atual (114 testes ✅)
   - Estrutura criada
   - Comandos rápidos
   - Checklist de validação

### 2. **QUICK_START.md** 🚀 GUIA RÁPIDO
   - O que são testes de integração
   - Estrutura de diretórios
   - Lista dos 11 testes
   - Como rodar os testes
   - Fixtures disponíveis
   - Exemplo simples

### 3. **EXAMPLES.md** 💡 8 EXEMPLOS PRÁTICOS
   1. Coleta com um plugin
   2. Agregação de múltiplos plugins
   3. Detecção de regressão
   4. Análise de top offenders
   5. Distribuição de severidades
   6. JSON serialization
   7. Rastreamento de melhoria
   8. Custom fixture

### 4. **README_INTEGRATION_TESTS.md** 📚 DOCUMENTAÇÃO COMPLETA
   - Padrões de teste detalhados
   - Estrutura do relatório (schema)
   - Tips & boas práticas
   - Integração com CI/CD
   - Recursos relacionados

## 📁 Código

### `test_metrics_integration.py` - 11 Testes
```
TestMetricsIntegration (8 testes)
├── test_metrics_collection_single_plugin
├── test_metrics_aggregation
├── test_metrics_severity_distribution
├── test_metrics_top_offenders
├── test_metrics_plugin_breakdown
├── test_metrics_report_serialization
├── test_metrics_empty_project
└── test_metrics_consistency_across_runs

TestMetricsComparison (2 testes)
├── test_metrics_regression_detection
└── test_metrics_improvement_detection

TestMetricsReporting (1 teste)
└── test_metrics_report_completeness
```

### `conftest.py` - Fixtures
```python
@pytest.fixture
def sample_python_file(tmp_path) → Path
    # Arquivo Python limpo

@pytest.fixture
def messy_python_file(tmp_path) → Path
    # Arquivo com problemas de estilo

@pytest.fixture
def duplicated_code_file(tmp_path) → Path
    # Arquivo com duplicação

@pytest.fixture
def project_with_issues(tmp_path) → Path
    # Projeto completo com variados problemas

@pytest.fixture
def setup_pythonpath()
    # Setup automático do PYTHONPATH
```

## 🎯 Quick Navigation

**Sou novo em testes de integração:**
1. Leia `README.md` (resumo)
2. Leia `QUICK_START.md` (entenda o conceito)
3. Consulte `EXAMPLES.md` (veja exemplos)

**Vou criar um novo teste:**
1. Consulte `EXAMPLES.md` para um template
2. Veja `conftest.py` para fixtures disponíveis
3. Adapte um dos exemplos

**Preciso de documentação técnica:**
1. Consulte `README_INTEGRATION_TESTS.md` (padrões)
2. Veja `test_metrics_integration.py` (código)
3. Consulte `EXAMPLES.md` (casos de uso)

## 🚀 Commands Rápidos

```bash
# Todos os testes de integração
pytest tests/integration/ -v

# Um teste específico
pytest tests/integration/test_metrics_integration.py::TestMetricsIntegration::test_metrics_collection_single_plugin -v

# Com cobertura
pytest tests/integration/ --cov=toolkit.core --cov-report=html

# Com output verboso (debug)
pytest tests/integration/ -v -s
```

## 📊 Estrutura do Fluxo Testado

```
Arquivos Python
    ↓
run_analysis() [engine.py]
    ├─ StyleCheckerPlugin
    ├─ DuplicateCodeCheckerPlugin
    └─ [Outros Plugins]
    ↓
FileReport[]
    ↓
aggregate() [aggregator.py]
    ↓
UnifiedReport (JSON-serializable)
    ├─ summary
    │   ├─ total_files
    │   ├─ total_issues
    │   ├─ issues_by_plugin
    │   ├─ issues_by_severity
    │   └─ top_offenders
    ├─ analysis_metadata
    │   ├─ tool_version
    │   ├─ plugins_executed
    │   ├─ status
    │   └─ timestamp
    └─ details
```

## 📈 Coverage

**Análise Coberta:**
- ✅ Coleta de métricas (1+ plugins)
- ✅ Agregação de resultados
- ✅ Validação de estrutura
- ✅ Cálculos de métricas
- ✅ Severidades e rankings
- ✅ Serialização JSON
- ✅ Consistência entre runs
- ✅ Detecção de regressão
- ✅ Detecção de melhoria
- ✅ Casos limite

## 🔗 Referências

- `src/toolkit/core/engine.py` - Motor de análise
- `src/toolkit/core/aggregator.py` - Agregação
- `src/toolkit/core/contracts.py` - Schemas
- `tests/cli/test_cli_e2e.py` - Testes E2E
- `pyproject.toml` - Configuração pytest

## ✅ Status

- ✅ 11 testes de integração implementados
- ✅ Fixtures reutilizáveis criadas
- ✅ Documentação completa (4 arquivos)
- ✅ 8 exemplos práticos
- ✅ 114 testes totais passando
- ✅ Pronto para CI/CD

## 🎓 Próximos Passos

1. **Performance Tests** - Medir velocidade
2. **Snapshot Tests** - Comparar com histórico
3. **Metrics History** - Rastrear ao longo do tempo
4. **Automated CI** - Falhar se regrediu

---

**Recomendação:** Comece pelo `README.md`, depois `QUICK_START.md`, e consulte `EXAMPLES.md` conforme necessário.
