# User Documentation — Code Quality Toolkit UI
## Introdução

Esta interface gráfica permite analisar projetos Python utilizando o Code Quality Toolkit de forma simples, visual e intuitiva.
O utilizador deixa de executar comandos manuais e passa a interagir apenas com o cliente gráfico.

## Como iniciar a aplicação
### Iniciar o servidor (controller)

No diretório raiz do projeto:

uvicorn DEV.code_quality_toolkit.web.server:app --reload


O servidor ficará disponível em:

http://127.0.0.1:8000

### Iniciar a interface (client)
python DEV/code_quality_toolkit/web/client.py

## Navegação na aplicação
### Ecrã inicial (lista de plugins)

[PRINT 1 – UI inicial com lista de plugins]

No painel esquerdo encontras:

Lista de plugins disponíveis

Botão “Select All”

Ícones para expandir configurações de cada plugin

### Selecionar um diretório ou ficheiro

[PRINT 2 – Seleção de diretório no UI]

O utilizador escolhe a pasta ou ficheiro que deseja analisar.

### Configurar plugins

[PRINT 3 – Configuração de plugins]

Para cada plugin podes:

Ativar / desativar

Consultar opções

Modificar parâmetros quando aplicável

### Executar a análise

O UI envia um pedido:

POST /api/v1/analyze


Fluxo automático:

O UI cria ZIP do diretório selecionado

Envia ZIP + configurações ao servidor

O servidor processa, gera relatório e envia ZIP final

O UI extrai o ZIP

O relatório report.html abre automaticamente no navegador

### Visualizar relatório

[PRINT 4 – report.html no browser]

O relatório inclui:

Dashboard principal

Total de ficheiros analisados

Total de issues

Severidades agregadas

Issues por plugin

Top Offenders

Tabela detalhada de issues

## Como interpretar o Dashboard
### Métricas globais

Mostra:

Número total de ficheiros

Issues totais

Estado da análise

### Severidade agregada

Agrupa issues por:

info

low

medium

high

### Issues por plugin

Permite compreender quais plugins identificaram mais problemas.

### Top Offenders

Lista os ficheiros com mais problemas.

### Tabela detalhada

Inclui:

ficheiro

plugin

tipo de issue

severidade

linha

mensagem

## Porquê esta interface?

Evita comandos complexos

Torna o toolkit acessível a utilizadores não técnicos

Fornece análises rápidas visualmente

Facilita a adoção da framework pela equipa

## Suporte

Para dúvidas contactar os responsáveis da equipa.

