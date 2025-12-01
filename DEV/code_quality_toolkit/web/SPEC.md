# Developer Documentation — Web UI / Client–Server Architecture
## Introdução

Este documento descreve a arquitetura técnica do sistema Web UI desenvolvido na Sprint, incluindo:

Arquitetura Client–Server

Fluxo de transação de ficheiros

Comunicação com FastAPI

Mecanismos internos da análise

Integração com Toolkit Engine

Estrutura dos endpoints

## Arquitetura Geral

A aplicação é constituída por três camadas:

+-------------------+         +----------------------+        +-----------------------+
|      CLIENT       | ----->  |      CONTROLLER      | -----> |      TOOLKIT ENGINE   |
|  (client.py GUI)  |         |   (FastAPI server)   |        |  (Core + Plugins)     |
+-------------------+         +----------------------+        +-----------------------+

Funções de cada camada:
### Client (UI)

Seleção de diretórios

Configuração de plugins

Criação automática de ZIP

Envio de pedidos ao servidor

Receção de ZIP devolvido

Abertura automática de report.html

### Controller (FastAPI)

Recebe ZIP via POST /api/v1/analyze

Extrai para diretório temporário

Invoca a engine do toolkit

Gera dashboards e report.html

Reempacota resultados e devolve ao cliente

### Toolkit Engine

Carrega e configura plugins

Executa análise sobre os ficheiros

Produz:

issues.json

dashboards

report.html

## Endpoints
 GET /api/v1/plugins

Retorna lista de plugins disponíveis.

 GET /api/v1/plugins/configs

Retorna configurações default de cada plugin.

 POST /api/v1/analyze

###Fluxo completo:

Recebe ZIP do cliente.

Extrai para pasta temporária.

Carrega configs enviadas.

Invoca engine:

run_analysis(path, configs)

Gera ficheiros:

report.html

dashboards D3

meta.json

Cria ZIP de retorno.

Envia ZIP ao cliente.

## File Transaction Flow

Ciclo completo ZIP Upload → Analysis → ZIP Return

CLIENT
  ↓ cria ZIP
POST /analyze
  ↓ envia ZIP
SERVER
  ↓ extrai
TOOLKIT ENGINE
  ↓ analisa
  ↓ gera report.html
SERVER
  ↓ cria ZIP
  ↓ devolve ZIP
CLIENT
  ↓ extrai
  ↓ abre report.html

## Comunicação Assíncrona (Signal/Slot Equivalent)

Embora o projeto não use diretamente Qt signals/slots, o mecanismo equivalente é:

### No Cliente:

Ações do utilizador → eventos GUI

Chamadas HTTP → assíncronas via threads

Callbacks → atualizam interface

### No Servidor FastAPI:

Requests → assíncronos

Handlers usam async def

Não bloqueiam event loop

## Estrutura do Projeto
DEV/
 └─ code_quality_toolkit/
     ├─ web/
     │   ├─ server.py
     │   ├─ client.py
     │   └─ README.md (User Docs)
     └─ src/
         └─ toolkit/
             ├─ core/
             ├─ plugins/
             │   └─ DASHBOARD.md
             └─ ...

## Considerações Técnicas do Dashboard

Gerado automaticamente durante análise

Criado por cada plugin no método analyze()

Deve usar D3.js

Dimensões: 1066 × 628 px

## Conclusão

Este SPEC documenta claramente:

A arquitetura client-server

O fluxo técnico completo da análise

O comportamento dos endpoints

A integração com a engine

O ciclo de dados entre cliente, servidor e toolkit

