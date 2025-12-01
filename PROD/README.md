
# User Documentation — Code Quality Toolkit Web UI
## Introdução

A interface Web/Cliente deste projeto permite que qualquer utilizador execute análises de qualidade de código sem recorrer à linha de comandos.
A aplicação fornece:

Seleção de diretórios

Configuração de plugins

Execução da análise

Visualização automática do relatório final (dashboard HTML)

Comunicação direta com o servidor FastAPI

Este UI existe para tornar o processo mais simples, rápido e acessível.

## Como iniciar a aplicação
### Iniciar o Servidor (Controller)

No diretório raiz do projeto:

uvicorn DEV.code_quality_toolkit.web.server:app --reload


Servidor ficará disponível em:

http://127.0.0.1:8000

### Iniciar o Client (UI)
python DEV/code_quality_toolkit/web/client.py


O cliente abrirá uma interface gráfica que permite executar todo o fluxo de análise.

## Interface do Utilizador
### Ecrã inicial (UI Overview)

Aqui é apresentada a lista de plugins disponíveis e o estado inicial da aplicação.

[PRINT 1 – UI inicial com lista de plugins]
![PRINT 1](img/print1.png)

### Selecionar Diretório a Analisar

O utilizador escolhe um ficheiro ou pasta que será enviada ao servidor.

[PRINT 2 – Seleção de diretório]
![PRINT 2](img/print2.png)

### Configurar Plugins

Cada plugin pode ser ativado/desativado e configurado.

[PRINT 3 – Configuração de plugins]
![PRINT 3](img/print3.png)

### Executar a Análise

Depois de selecionado o diretório e plugins:

O cliente cria automaticamente um ZIP do projeto.

Envia-o para o servidor através de POST /api/v1/analyze.

Recebe um ZIP com os resultados.

Extrai os ficheiros.

Abre o relatório final.

### Interpretar o Relatório Final (Dashboard)

Após a análise, abre automaticamente o ficheiro:

report.html


Este dashboard apresenta:

Métricas globais

Total de ficheiros analisados

Total de issues

Estado (completed, partial, failed)

Severidades (info, low, medium, high)

Issues por plugin

Mostra quantos problemas cada plugin detetou.

Top Offenders

Os ficheiros com mais problemas.

Tabela completa de issues

Com filtro por severidade e plugin.

[PRINT 4 – Dashboard/Report HTML no navegador]
![PRINT 4](img/print4.png)

## Porquê esta interface?

O objetivo é:

Evitar lidar com CLI complexa

Facilitar testes rápidos

Permitir visualização clara do relatório

Melhorar a experiência de análise de código

Garantir consistência nas análises dentro do grupo

## Problemas Comuns
❌ O servidor não inicia

Verificar se executou:

uvicorn DEV.code_quality_toolkit.web.server:app --reload

❌ O UI não encontra o servidor

Garantir que o servidor está a correr na mesma máquina.

❌ report.html não abre

Verificar permissões de browser ou antivírus.

## Autores

Grupo PL8 – Sprint Web App
Tiago Alves -(User Documentation)
Rabia Saygin -integração entre o UI e o CLI
Isaque Capra- testes manuais e de integração
Sasha/André Silva - design da app
Pedro Silva - toolkit + coordinator





