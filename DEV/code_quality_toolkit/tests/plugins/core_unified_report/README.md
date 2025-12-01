Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982

Análise do código do Core Unified Report:

1. Propósito e Utilidade Geral:
Este código implementa o sistema central de agregação e exportação de relatórios do Code Quality Toolkit. 
Composto por 2 módulos principais (aggregator.py e exporters.py), o sistema é responsável por recolher os outputs individuais de todos os plugins executados, consolidá-los numa estrutura unificada
e transformá-los em formatos consumíveis tanto por humanos (HTML) como por máquinas (JSON).
A utilidade prática é fundamental: permite que diferentes plugins trabalhem independentemente, produzindo outputs no mesmo formato, que são depois combinados automaticamente num relatório coerente.
Este tipo de sistema é essencial em ferramentas de análise estática modulares, pipelines de qualidade de código, relatórios de conformidade e processos de revisão automatizada.

2. Funcionamento do Sistema:
O sistema está organizado em duas fases principais: agregação e exportação.

    1-Fase 1: Agregação de Resultados
    A função aggregate() no módulo aggregator.py é o coração do sistema. Recebe uma lista de resultados por ficheiro (cada um contendo outputs de múltiplos plugins) e um dicionário com o estado de execução de cada plugin.
    O processo de agregaçãi segue esta lógica:

        1) Inicialização de Estruturas: cria contadores para severidades (high, medium, low, info) e para issues por plugin, inicializados todos a zero.

        2) Iteração por ficheiros: para cada ficheiro analisado:
            -Itera sobre os resultados de cada plugin executado nesse ficheiro
            -Extrai a lista de issues do campo results
            -para cada issue encontrado:
                .Incrementa o contador da severidade correpondente
                .Incrementa o contados do plugin que encontrou o issue
                .Acumula no total geral

        3) Cálculo de top offenders: constrói uma lista de tuplas (ficheiro, contagem) agregando todos os issues por ficheiro, ordena por contagem descendente, e converte par formato de dicionário.

        4) Contrução de Metadata: recolhe informação sobre a análise:
            -Timestamp da execução
            -Versão do toolkit
            -Lista de plugins executados
            -Estado geral (completed se todos plugins succeeded)

        5) Montagem do Relatório Final: combina metadata, sumário agregado e detalhes completos numa estrtura UnifiedReport que segue o schema definido no documento de especificação.

    A agregação é matemáticamente rigorosa: todos os contadores são validados por testes unitários que garantem que a soma total é consistente e que não h+a duplicações ou perdas de informação.

    2-Fase 2: Exportação para HTML
    A função generate_html() no módulo exporters.py transforma o relatório unificao em HTML legível.
    O processo é essencialmente um template engine simples:

        1) Estrutura Base: cria o esqueleto HTML com DOCTYPE, head com charset UTF-8, e body estruturado.

        2) Secção de Metadata: renderiza informações de alto nível:
            -Timestamp de análise
            -Versão da ferramenta
            -Status geral
            -Lisya de plugins executados

        3) Secção de Sumário: gera 3 sub-secções:
            -Totais: total de ficheiros e total de issues
            -Issues by Severity: lista não-ordenada com cada severidade e sua contagem
            -Issues by plugin: lista não-ordenada com cada plugin e quantos issues encontrou
            -Top Offenders: lista ordenada dos ficheiros mais problemáticos

        4)Secção de Detalhes: para cada ficheiro analisado:
            -Cria cabeçalho com nome do ficheiro
            -Para cada plugin executado nesse ficheiro:
                .Cabeçalho com nome do plugin
                .Informação de estado e métricas
                .se houver erros, exibe-os
                .Se houver issues, renderiza lista HTML com cada issue contendo:
                    > Severidade em uppercase
                    >código do issue
                    >mensagem (escaped com html.escape() para segurança)
                    >linha e coluna
                    >hit explicativa
            
            -Importante: HTML exibe todos os plugins, mesmo os que não encontraram issues, mostrando "No issues found" nesse caso

        5) Escape de HTML: usa html.escape() em todas as mensagens user-provided para prevenir XSS
    
    O HTML gerado é standalone, ou seja, nao depende de CSS externo ou JavaScript, podendo ser aberto em qualquer browser moderno sem configuração adicional.


3. Qualidade da Implementação
O código demonstra várias boas práticas de engenharia de software:

    1- Separação de Responsabilidades: a clara divisão entre agregação (aggregator.py) e exportação (Exporters.py) facilita manutenção e testes.
    Cada módulo tem uma responsabilidade única bem definida.

    2- Robustez e Error Handling:
    O sistema é preparado para:
        .Plugins que falham (mantém o erro no campo error do sumário)
        .Dados vazios (funciona corretamente com 0 issues)
        .Campos opcionais ausentes (usa .get() com fallbacks)

    3- Validação Matemática:
    Os testes unitários em test_exporters.py validam rigorosamente:
        .Precisão de contagens: verifica que total_issues == sum(all issues)
        .Agrupamento Correto: Confirma que issues_by_severity soma corretamente
        .Ordenação: garante que top_offenders está ordenado descendentemente
        Schema Integrity: Valida que todas as chaves obrigatórias existem

    4- Segurança:
    O uso de html.escape() previne vulnerabilidades XSS, essencial quando se renderiza conteúdo user-provided.

    5- Type hints:
    O uso de type hints, como dict[str, Any], list, etc, melhora a legibilidade e permite deteção estática de erros com ferramentas como mypy.

    6- Testabilidade:
    O design modular permite testes unitário isolados. A função create_mock_result() nos testes demonstra como é fácil criar dados de teste que passam validação.


4. Arquitetura de Testes:
    1- Testes de precisão matemáticas:
        .test_aggregate_counts_total_issues_correctly: valida soma total
        .test_aggregate_counts_by_severity_correctly: valida distribuição por severidade
        .test_aggregate_counts_by_plugin_correctly: valida contagem por plugin

    2-Testes de lógica de ordenação:
        .test_top_offenders_sorting_logic: garante que worst offenders aparecem primeiro


5. Integração com o Core System:
O Unified Report integra-se perfeitamente com o resto do toolkit:

    1-Contrato de Plugin Respeitado:
    Todos os plugins devolvem estrutura compatível:

        {
            "results": [...],
            "summary": {
                "issues_found": int,
                "status": str
            }
        }

    2- CLI Integration:
    O CLI orquestra:
        1) Descoerta e carregameto de plugins
        2) Execução de plugins em cada ficheiro
        3) Agregação via aggregate()
        4) Exportação via generate_html() ou JSON nativo


6. Utilidade Prática:
Em ambiente real, este sistema é fundamental para:
    1- Comunicação de resultados:
    Transforma dados técnicos em formatos compreensíveis:
        .Developers: HTML visual para revisão rápida
        .CI Systems: JSON para decisões automatizadas
        .Management: Relatórios formatados para tracking de qualidade
    
    2- Rastreabilidade e Auditoria:
    Relatório timestamped permitem:
        .Acompanhar evolução de métricas ao longo do tempo
        .Provar conformidade com standards
        .Identificar regressões em qualidade

    3- Facilitação de Workflows:
    Integra-se naturalemnte em:
        .Pre-commit hooks: validação local antes de commit
        .Pull request checks: cometários automáticos com findings
        .Scheduled scans: relatórios periódicos por email

    4- Tomada de decisões:
    O sumário agregado facilita:
        .Priorização de refactoring (focar em top offenders)
        .Alocação de recursos (plugings com mais issues)
        .Tracking de KPIs (tendência de issues ao longo do tempo)

