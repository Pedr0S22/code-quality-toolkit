# Web UI Specification

## Visão Geral

A interface Web serve apenas para consumir o `report.json` previamente gerado pela CLI. Não executa a análise. O foco é permitir aos estudantes explorar o
relatório e construir visualizações.

## Funcionalidades

1. **Dashboard**
   - Cartões com totais (`total_files`, `total_issues`).
   - Gráfico (pode ser tabela simples) com contagem por severidade.
   - Gráfico por plugin (`issues_by_plugin`).
   - Lista “Top Offenders” mostrando ficheiros com mais issues.

2. **Lista de Issues**
   - Tabela com colunas: Ficheiro, Plugin, Severidade, Código, Mensagem, Linha.
   - Filtros por severidade e plugin (dropdowns).
   - Ao clicar numa linha, mostrar detalhes/hint.

## Wireframes (ASCII)

```
+-----------------------------------------------------------+
| Dashboard                                                 |
+-------------------+------------------+--------------------+
| Total Files: 10   | Total Issues: 24 | Status: completed  |
+-------------------+------------------+--------------------+
| Severity Counts: info=5 low=10 medium=6 high=3            |
| Plugin Issues: StyleChecker=14 Cyclomatic=10              |
+-----------------------------------------------------------+
| Top Offenders                                            |
| 1. src/app.py (6)                                        |
| 2. src/utils.py (4)                                      |
+-----------------------------------------------------------+

+-----------------------------------------------------------+
| Issues Table                                              |
+-----------------------------------------------------------+
| Filters: [Plugin v] [Severity v] [Search ____]            |
|-----------------------------------------------------------|
| File           | Plugin     | Sev | Code     | Line | Msg |
|-----------------------------------------------------------|
| src/app.py     | StyleCheck | low | LINE_LEN |  45  | ... |
| src/utils.py   | Cyclomatic | med | HIGH_C   |  22  | ... |
+-----------------------------------------------------------+
```

## API Endpoints

Implementados em `web/app_stub.py` usando Starlette/FastAPI minimalista:

- `GET /api/report` — devolve o JSON completo carregado de disco.
- `GET /api/summary` — devolve apenas `report["summary"]`.

Os endpoints lêem o ficheiro `report.json` no diretório de execução. Em caso de
erro (ficheiro inexistente), retornar HTTP 404 com mensagem amigável.

## Fluxo sugerido

1. CLI gera `report.json`.
2. Servidor Web lê e mantém cache leve (opcional) para responder aos pedidos.
3. Frontend (React, Vue ou HTML estático) consome `GET /api/report`.

## Notas Pedagógicas

- Incentivar estudantes a desenhar componentes reutilizáveis para cartões e
  tabelas.
- Destacar boas práticas de separação entre backend (servindo JSON) e frontend.
