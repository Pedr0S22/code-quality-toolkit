# Exemplos Práticos de Testes de Integração com Métricas

## Exemplo 1: Testar Coleta de Métricas com Um Plugin

```python
def test_style_checker_metrics(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Coleta métricas usando apenas StyleChecker."""
    
    # Criar arquivo com problemas
    file = tmp_path / "messy.py"
    file.write_text("x=1\ny=2\ndef  foo():\n    pass\n")
    
    # Executar análise
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files, plugin_status = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    
    # Verificar resultados
    assert len(files) >= 1
    assert plugin_status["StyleChecker"] == "completed"
    
    # Agregar
    report = aggregate(files, plugin_status)
    assert report["summary"]["total_issues"] > 0
    assert "StyleChecker" in report["summary"]["issues_by_plugin"]
```

## Exemplo 2: Testar Agregação de Múltiplos Plugins

```python
def test_multiple_plugins_aggregation(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Testa agregação de múltiplos plugins."""
    
    # Criar projeto com vários problemas
    (tmp_path / "duplicated.py").write_text(
        "def a():\n    x = 1\n    return x\n"
        "def b():\n    x = 1\n    return x\n"
    )
    (tmp_path / "ugly.py").write_text("x=1;y=2;z=3\n")
    
    # Análise
    plugins = {
        "StyleChecker": StyleCheckerPlugin(),
        "DuplicateCodeChecker": DuplicateCodeCheckerPlugin(),
    }
    files, plugin_status = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    
    # Agregação
    report = aggregate(files, plugin_status)
    
    # Verificar breakdown por plugin
    issues_by_plugin = report["summary"]["issues_by_plugin"]
    assert len(issues_by_plugin) == 2
    print(f"Issues: {issues_by_plugin}")
    
    # Verificar severidades
    severities = report["summary"]["issues_by_severity"]
    print(f"Severities: {severities}")
```

## Exemplo 3: Testar Detecção de Regressão

```python
def test_quality_regression_detection(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Detecta quando a qualidade piora (regressão)."""
    
    # Baseline: código limpo
    file = tmp_path / "code.py"
    file.write_text(
        '"""Module."""\n'
        "def hello() -> None:\n"
        '    """Greet."""\n'
        "    print('hello')\n"
    )
    
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files_before, status_before = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    report_before = aggregate(files_before, status_before)
    baseline = report_before["summary"]["total_issues"]
    print(f"Baseline issues: {baseline}")
    
    # Degrade: introduzir problemas
    file.write_text(
        "x=1\ny=2\nz=3\n"
        "# " + "x" * 100 + "\n"
    )
    
    files_after, status_after = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    report_after = aggregate(files_after, status_after)
    current = report_after["summary"]["total_issues"]
    print(f"Current issues: {current}")
    
    # Verificar regressão
    assert current > baseline, "Quality regression detected!"
```

## Exemplo 4: Analisar Top Offenders

```python
def test_identify_worst_files(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Identifica os arquivos com mais problemas."""
    
    # Criar vários arquivos com diferentes níveis de qualidade
    (tmp_path / "bad1.py").write_text("x=1;y=2;z=3\n" * 10)
    (tmp_path / "bad2.py").write_text("a=1;b=2\n" * 5)
    (tmp_path / "good.py").write_text('"""Clean."""\ndef hello(): pass\n')
    
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files, status = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    report = aggregate(files, status)
    
    # Análisar top offenders
    top = report["summary"]["top_offenders"]
    print("\nTop offenders:")
    for rank, offender in enumerate(top, 1):
        print(f"  {rank}. {offender['file']}: {offender['issues']} issues")
    
    # O arquivo "bad1.py" deve estar no topo
    assert top[0]["issues"] > top[-1]["issues"]
```

## Exemplo 5: Validar Distribuição de Severidades

```python
def test_severity_distribution_analysis(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Analisa distribuição de severidades dos problemas."""
    
    # Arquivo com diversos tipos de problemas
    file = tmp_path / "mixed_issues.py"
    file.write_text(
        "x=1;y=2;z=3\n"  # Low severity: formatting
        "# " + "x" * 200 + "\n"  # Medium severity: line too long
        "unused_var = 42\n"  # Info level
    )
    
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files, status = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    report = aggregate(files, status)
    
    # Analisar severidades
    severity_dist = report["summary"]["issues_by_severity"]
    print("\nSeverity distribution:")
    for severity, count in severity_dist.items():
        if count > 0:
            print(f"  {severity.upper()}: {count} issues")
    
    # Verificar que temos múltiplas severidades
    non_zero = [s for s, c in severity_dist.items() if c > 0]
    assert len(non_zero) > 0, "Should have at least one severity level"
```

## Exemplo 6: JSON Serialization

```python
def test_export_metrics_as_json(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Exporta métricas para JSON para integração com outras ferramentas."""
    
    file = tmp_path / "app.py"
    file.write_text("x=1\n")
    
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files, status = run_analysis(
        root=tmp_path,
        plugins=plugins,
        config=toolkit_config,
    )
    report = aggregate(files, status)
    
    # Exportar para JSON
    json_report = json.dumps(report, indent=2)
    
    # Salvar em arquivo (exemplo)
    report_file = tmp_path / "report.json"
    report_file.write_text(json_report)
    
    # Verificar que pode ser lido
    loaded = json.loads(report_file.read_text())
    assert loaded["summary"]["total_issues"] >= 0
    print(f"Report saved to {report_file}")
```

## Exemplo 7: Medir Melhoria Incremental

```python
def test_track_quality_improvement(
    self, tmp_path: Path, toolkit_config: ToolkitConfig
) -> None:
    """Rastreia melhorias de qualidade ao longo do tempo."""
    
    file = tmp_path / "improving.py"
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    
    # Fase 1: Código sujo
    file.write_text("x=1;y=2;z=3\n" * 20)
    files, status = run_analysis(root=tmp_path, plugins=plugins, config=toolkit_config)
    report1 = aggregate(files, status)
    phase1_issues = report1["summary"]["total_issues"]
    
    # Fase 2: Refatorado
    file.write_text("x = 1\ny = 2\nz = 3\n" * 20)
    files, status = run_analysis(root=tmp_path, plugins=plugins, config=toolkit_config)
    report2 = aggregate(files, status)
    phase2_issues = report2["summary"]["total_issues"]
    
    # Fase 3: Bem formatado
    file.write_text(
        '"""Module."""\n'
        "x = 1\ny = 2\nz = 3\n" * 10
    )
    files, status = run_analysis(root=tmp_path, plugins=plugins, config=toolkit_config)
    report3 = aggregate(files, status)
    phase3_issues = report3["summary"]["total_issues"]
    
    # Mostrar progresso
    print(f"\nQuality improvement tracking:")
    print(f"  Phase 1 (messy):    {phase1_issues} issues")
    print(f"  Phase 2 (formatted): {phase2_issues} issues")
    print(f"  Phase 3 (clean):    {phase3_issues} issues")
    
    # Verificar melhoria
    assert phase1_issues >= phase2_issues >= phase3_issues
```

## Exemplo 8: Custom Fixture para Projeto Específico

```python
@pytest.fixture
def django_project(tmp_path: Path) -> Path:
    """Cria estrutura típica de projeto Django."""
    
    # App structure
    app = tmp_path / "myapp"
    app.mkdir()
    (app / "__init__.py").touch()
    
    (app / "models.py").write_text(
        "from django.db import models\n"
        "class User(models.Model):\n"
        "    name=models.CharField(max_length=100)\n"
    )
    
    (app / "views.py").write_text(
        "from django.shortcuts import render\n"
        "def user_list(request):\n"
        "    users=[]\n"
        "    return render(request, 'users.html', {'users':users})\n"
    )
    
    return tmp_path


def test_django_project_quality(
    self, django_project: Path, toolkit_config: ToolkitConfig
) -> None:
    """Analisa qualidade de um projeto Django."""
    
    plugins = {"StyleChecker": StyleCheckerPlugin()}
    files, status = run_analysis(
        root=django_project,
        plugins=plugins,
        config=toolkit_config,
    )
    report = aggregate(files, status)
    
    print(f"\nDjango project quality:")
    print(f"  Files: {report['summary']['total_files']}")
    print(f"  Issues: {report['summary']['total_issues']}")
```

## Dicas e Boas Práticas

### 1. Use Fixtures para Dados de Teste
```python
# ❌ Evitar repetição
def test_1(self, tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x=1\n")

def test_2(self, tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x=1\n")

# ✅ Preferir fixture
@pytest.fixture
def messy_file(tmp_path):
    f = tmp_path / "test.py"
    f.write_text("x=1\n")
    return f

def test_1(self, messy_file): pass
def test_2(self, messy_file): pass
```

### 2. Sempre Verificar Estrutura Básica
```python
def test_any_analysis(self, ...):
    files, status = run_analysis(...)
    report = aggregate(files, status)
    
    # Sempre verificar estas chaves
    assert "summary" in report
    assert "analysis_metadata" in report
    assert report["summary"]["total_files"] >= 0
```

### 3. Use Descritores Claros
```python
# ❌ Evitar
def test_m(self): pass

# ✅ Preferir
def test_detects_style_issues_in_code_with_multiple_formatting_problems(self):
    pass
```

### 4. Print para Debug
```python
def test_something(self, ...):
    report = aggregate(files, status)
    
    # Use print() para ver valores em test com -s flag
    print(f"Issues found: {report['summary']['total_issues']}")
    # Run with: pytest -s tests/integration/...
```

## Correr Exemplos

```bash
cd DEV/code_quality_toolkit

# Rodar todos
python -m pytest tests/integration/ -v

# Rodar com output verboso
python -m pytest tests/integration/ -v -s

# Rodar teste específico
python -m pytest tests/integration/test_metrics_integration.py::TestMetricsIntegration::test_metrics_aggregation -v -s

# Gerar relatório HTML de cobertura
python -m pytest tests/integration/ --cov=toolkit.core --cov-report=html
# Abrir htmlcov/index.html no navegador
```
