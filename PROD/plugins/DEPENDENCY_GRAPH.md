Membros:

João Neto 2023234004 @Imajellyfish

João Eduardo Duarte 2011187848 @jeduarteldm

Bernardo Fonseca 2021239253 @jF202

Diogo Delvivo 2021150174 @delvivo.diogo1

Catarina Vieira 2023218473 @27634982

Análise do código do plugin DependencyGraph
1. Propósito e Utilidade Geral
Este código implementa um plugin chamado DependencyGraph, cuja função é analisar e mapear estaticamente todas as dependências (imports) de código Python. O plugin utiliza o módulo nativo ast (Abstract Syntax Tree) para fazer o parsing do código-fonte e extrair informação estruturada sobre declarações de importação.

A utilidade prática foi expandida nesta versão: além de identificar dependências e detetar padrões problemáticos (como wildcard imports ou importações relativas profundas), o plugin agora gera automaticamente uma visualização gráfica (Dashboard). Isso é essencial para arquitetos de software e líderes técnicos visualizarem o acoplamento do sistema, documentarem a arquitetura automaticamente e facilitarem auditorias de dependências externas.

2. Funcionamento do Plugin
O plugin é inicializado com listas de categorização (biblioteca padrão) e lê as regras de negócio a partir do arquivo TOML global (ex: nível máximo de importação relativa, rastreio de módulos stdlib).

O método principal é o analyze, que orquestra um fluxo robusto:

Parsing AST Seguro: Tenta converter o código-fonte numa árvore sintática usando ast.parse(). Se houver erros de sintaxe (código inválido), o processo é interrompido graciosamente, reportando a falha sem derrubar a ferramenta.

Extração de Imports (_extract_imports): Percorre a árvore AST (via ast.walk), identificando nós ast.Import e ast.ImportFrom. Extrai metadados cruciais: linha, módulo alvo, alias e nível relativo (0=absoluto, 1+=relativo).

Categorização (_categorize_imports): Classifica cada dependência em três baldes:

stdlib: Biblioteca padrão do Python (ex: os, json).

third_party: Pacotes externos (ex: requests, pandas).

local: Módulos internos do projeto.

Avaliação de Severidade (_assess_severity): Aplica regras de linting:

Importações relativas profundas (level > 1) -> MEDIUM.

Wildcard imports (from x import *) -> MEDIUM (configurável).

Importações normais -> INFO.

Agregação e Dashboard (generate_dashboard): Após processar os ficheiros, o plugin utiliza o método _aggregate_data_for_dashboard para compilar métricas globais e gera um ficheiro HTML independente. Este dashboard utiliza D3.js para apresentar gráficos sobre a distribuição de tipos de dependência e os ficheiros com maior número de imports externos.

3. Qualidade da Implementação
O código demonstra maturidade em engenharia de software e adesão aos requisitos do projeto:

Independência de Dependências: Ao contrário de outros plugins, o DependencyGraph utiliza apenas a biblioteca padrão (ast), não exigindo instalação de pacotes extra (como bandit ou pylint), o que simplifica o deployment.

Robustez ("Golden Rule"): O uso extensivo de tratamento de exceções garante que erros de parsing em ficheiros individuais não abortem a análise global. O plugin falha apenas no escopo do ficheiro problemático.

Modularização: A lógica é dividida em métodos privados com responsabilidades únicas (_extract, _categorize, _assess), facilitando a manutenção e os testes unitários.

Visualização de Dados: A inclusão de um gerador de Dashboard HTML/D3.js eleva o nível da ferramenta, transformando dados brutos JSON em informação gerencial visualizável (Theme Green).

Configurabilidade: O plugin é flexível, permitindo que o utilizador defina via TOML se quer ser avisado sobre wildcards ou se quer ignorar módulos da biblioteca padrão, adaptando-se a diferentes estilos de projeto.

Type Hints e Documentação: O código está totalmente tipado e documentado com docstrings, facilitando a leitura e a prevenção de erros de tipo durante o desenvolvimento.