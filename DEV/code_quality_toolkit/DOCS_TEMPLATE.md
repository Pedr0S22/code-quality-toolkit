# 🟦 USER DOCUMENTATION
Code Quality Toolkit – User Guide

(Sprint 2 – UI & Dashboard Integration)

A User Interface (UI) desenvolvida nesta sprint fornece uma forma intuitiva e visual de utilizar o Code Quality Toolkit, permitindo:

-Seleccionar plugins

-Escolher ficheiros ou diretórios para análise

-Enviar pedidos ao servidor FastAPI

-Receber o relatório de qualidade

-Visualizar dashboards interativos gerados com D3.js

Esta interface substitui a necessidade de executar comandos manuais na linha de comandos, tornando o processo acessível a qualquer utilizador.

## 1. Como iniciar a aplicação
1.1 – Iniciar o servidor (Backend FastAPI)

No diretório do projeto:

uvicorn DEV.code_quality_toolkit.web.server:app --reload


O servidor ficará disponível em:

http://127.0.0.1:8000

1.2 – Iniciar o UI (Cliente PyQt6)
python DEV/code_quality_toolkit/web/client.py


Ao iniciar o UI, a janela principal exibirá:

Lista de plugins (coluna esquerda)

Botão Show Report

Área central “Ready to Analyze”

[INSERT SCREENSHOT: tela inicial]

## 2. Como usar a interface
Passo 1 — Selecionar Plugins

Cada plugin tem uma checkbox.
Pode ativar individualmente ou usar Select All.

Screenshot placeholder:

[INSERT SCREENSHOT: seleção de plugins no UI]

Passo 2 — Escolher diretório ou ficheiro para análise

Ao clicar em Analyze, o UI abre um diálogo do sistema para escolher uma pasta ou projeto.

Screenshot placeholder:

[INSERT SCREENSHOT: janela de seleção de diretório]

Passo 3 — Executar a análise

O cliente:

Cria um ZIP do diretório selecionado

Envia-o via POST ao backend

Recebe um ZIP com:

report.html

dashboards

ficheiros auxiliares

O terminal backend mostrará a requisição, por exemplo:

Screenshot placeholder:

[INSERT SCREENSHOT: terminal do servidor mostrando POST /analyze]

Passo 4 — Visualizar o relatório (Dashboard)

O UI descompacta o ZIP e abre automaticamente o relatório:

report.html


Este ficheiro contém:

Dashboard global

Total de ficheiros

Total de issues

Severidade agregada

Issues por plugin

Tabela completa de issues

Top Offenders

Screenshot placeholder:

[INSERT SCREENSHOT: report.html aberto no navegador]

## 3. Como interpretar o dashboard

O relatório apresenta:

Dashboard principal

Mostra métricas globais:

Total de ficheiros analisados

Total de issues

Estado da análise

Severidade agregada

Issues por plugin

Top Offenders

Ficheiros com mais problemas.

Tabela de issues

Lista detalhada com:

ficheiro

plugin

tipo

linha

severidade

descrição

Porquê esta interface?

Esta interface:

Facilita a análise visual

Simplifica a navegação

Elimina complexidade da CLI

Garante acesso imediato a métricas importantes

Melhora a experiência de utilizador

# 🟦 DEVELOPER DOCUMENTATION
SPEC.md – UI + Backend Architecture (Sprint 2 Additions)

Esta secção descreve a arquitetura cliente-servidor, fluxo de ficheiros e mecanismos internos necessários para compreender e estender o sistema.

## 1. Arquitetura Cliente-Servidor

O UI funciona como Rich Client que comunica com um servidor FastAPI.
A interação segue o modelo:

CLIENT (PyQt)  →  FastAPI Controller  →  Toolkit Engine  →  D3 Dashboards

Componentes:
client.py

Interface gráfica (PyQt6 + WebEngine)

Seleção de diretórios

Envio de ZIP via POST

Receção e extração do relatório

Visualização do dashboard

server.py

Endpoints:

GET  /api/v1/plugins
GET  /api/v1/plugins/configs
POST /api/v1/analyze


Funções:

Recebe ZIP

Extrai para diretório temporário

Invoca run_analysis()

Gera report.html + dashboards

Reempacota tudo e devolve ao cliente

## 2. File Transaction Flow

O fluxo completo zip → análise → zip é:

CLIENT
    ↓ (zip do projeto)
POST /analyze
    ↓
SERVER
    - unzip
    - run_analysis()
    - gera dashboards
    - gera report.html
    - zip final
    ↑
CLIENT
    - unzip
    - abre report.html


Screenshot placeholder:

[INSERT SCREENSHOT: UI após execução, mostrando estado/progresso]

## 3. Mecanismo de Sinais/Slots (UI Async)

O UI utiliza PyQt6 signals/slots para:

Executar pedidos de rede sem bloquear a janela

Atualizar a interface após resposta do servidor

Abrir automaticamente o relatório após conclusão

Exemplo simplificado:

analysisWorker.finished.connect(self.onAnalysisFinished)
analysisWorker.error.connect(self.onAnalysisError)

## 4. Dashboard Pipeline (D3.js Integration)

Cada plugin pode gerar dashboards personalizados.
A sprint exige:

Tamanho: 1066x628 px

Gerado dentro de plugin.py (método analyze())

Utilizar D3.js

Ficheiro:

<plugin_name>_dashboard.html


Guardado em:

src/toolkit/plugins/<plugin>/

## 5. Estrutura do ZIP devolvido

O ZIP contém:

report.html
meta.json
dashboard/
    <plugin>_dashboard.html
assets/
    charts.js
    styles.css

# 🟦 DASHBOARD DOCUMENTATION (DASHBOARD.md)

Cada dashboard deve:

Ser implementado em plugin.py durante analyze()
Utilizar D3.js
Ter dimensões fixas: 1066 × 628 px
Ser guardado como:
src/toolkit/plugins/<plugin>/<plugin_name>_dashboard.html


Elementos obrigatórios:

Área de métricas globais

Severidades

Issues por plugin

Top Offenders

Issues Table

### Placeholder para screenshot do dashboard de exemplo:
[INSERT SCREENSHOT: dashboard gerado no projeto]

# AUTHORS (Sprint UI Documentation)

Tiago Alves — Owner of UI Documentation 

Rabia Saygin — integração entre o UI e o CLI (backend)

André Silva — UI Visual Design

Sasha — UI Visual Design

Pedro Silva — Toolkit + Coordinator