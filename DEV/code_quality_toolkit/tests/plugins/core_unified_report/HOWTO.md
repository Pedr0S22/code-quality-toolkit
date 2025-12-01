Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982


Como usar e configurar o sistema de relatórios:

1. Visão Geral do Uso:
O core Unified Report é o componente central do Toolkit responsável por agregar os resultados de todos os plugins e gerar num formato legível e partilhável.
O  user não interage diretamente com as funções de agregação, mas sim com o CLI que orquestra todo o processo.
Na prática, o user executa uma análise e o sistema automaticamente recolhe os resusltados de todos os plugins, agrega-os numa estrutura unificada e exporta para o formato desejado (JSON ou HTML).
O processo é totalmente integrado no fluxo normal de execução do toolkit.


2. Como a Análise e Eportação são executadas:
Para usar o sistema de relatórios, o user precisa apenas de executar o comando de análise através do CLI, especificando opcionalmente o formato de saída desejado.
O processo segues estes passos automaticamente:
    1-Execução de Plugins: o core executa todos os plugins ativados no toolkit.toml sobre os ficheiros analisados.

    2-Agregação de Resultados: a função aggregate() recolhe os outputs de cada plugin e consolida-os num relatório unificado.

    3-Geração de Relatório: conforme o formato especificado, o sistema gera o relatório final:
        .JSON (padrão): estrutura de dados completa e processável por máquinas.
        .HTML: visualização formatada e legível para humanos.

Este fluxo é completamente automático: o user não precisa de chamar funções individualmente ou manipular dados manualmente.


3. Configuração do Sistema de Relatórios:
A configuração do sistema de relatórios é mínima, pois foi desenhado para funcionar "out of the box" com configurações sensatas por defeito.
As opções disponíveis são:

    1-Formato de Saída via CLI: o formato de saída é especificadp através da extensão do ficheiro de output:
        .Gerar o relatório JSON:
            python -m toolkit.core.cli analyze src/ --out report.json

        .Gerar o relatório HTML:
            python -m toolkit.core.cli analyze src/ --out report.html

    O sistema deteta automaticamente o formato baseado na extensão do ficheiro (.json ou .html).


4. Estrutura do Relatório Unificado:
O relatório gerado segue uma estrutura consistente, independentemente do formato de saída:

    1-Metadata de Análise:
        .timestamp: data e hora da análise
        .tool_version: versão do toolkit
        .status: estado geral da análise (completed/partial/failed)
        .plugins_executed: lista de plugins que foram executados

    2-Sumário agregado:
        .total_files: número total de ficheiros analisados
        .total_issues: soma total de problemas encontrados
        .issues_by_severity: contagem por nível (high/medium/low/info)
        .issues_by_plugin: contagem de issues encontrados por cada plugin
        .top_offenders: lista dos ficheiros com mais problemas (ordenada)

    3-Detalhes por Ficheiro:
        .nome do ficheiro
        .lista de resultados de cada plugin executado:
            -nome do plugin
            -estado da execuçao (completed/failed)
            -issues encontrados (severidade, código, mensagem, linha, coluna)
            -métricas calculadas (se aplicável)
            -erros de execução (se aplicável)


5. Experiência de Uso para Diferentes Cenários:
    1-Desenvolvimento Local-> Análise Rápida: 
    Em desenvolvimento local, o user pode gerar rapidamente um relatório HTML visual:

        python -m toolkit.core.cli analyze meu_ficheiro.py --out report.html

    Isto permite verificar rapidamente a qualidade do código e partilhar o relatório com colegas.

    2-Pipelines CI/CD-> Validação Automatizada:
    Em pipelines CI/CD, o relatório JSON é mais apropriado para processamento automático:

        python -m toolkit.core.cli analyze src/ --out report.json
        jq '.summary.issues_by_severity.high' report.json

    O pipeline pode falhar automaticamente se o número de issues high exceder um limite.

    3-Revisões de Código-> Partilha com Equipa:
    Para reuniões ou revisões de código, o relatório HTML oferece uma visualização clara:

        python -m toolkit.core.cli analyze src/ --out quality_report.html

    O HTML inclui:
        .tabelas formatadas de sumário
        .listas organizadas de problemas
        .código de cores por severiadade
        .links navegáveis entre secções


6.Intrepetação dos Relatórios:
    1- Relatório JSON: 
    Estrutura ideal para processamentos programático:
        {
            "analysis_metadata": {
                "timestamp": "2025-09-08T10:30:00Z",
                "tool_version": "1.0.0",
                "status": "completed",
                "plugins_executed": ["StyleChecker", "SecurityChecker"]
            },
            "summary": {
                "total_files": 12,
                "total_issues": 45,
                "issues_by_severity": {
                "high": 2,
                "medium": 15,
                "low": 28,
                "info": 0
                },
                "issues_by_plugin": {
                "StyleChecker": 30,
                "SecurityChecker": 15
                },
                "top_offenders": [
                {"file": "main.py", "issues": 12},
                {"file": "utils.py", "issues": 8}
                ]
            },
            "details": [...]
        }
    
    2- Relatório HTML:
    Interface visual com:
        .cabeçalho: metadata da análise
        .painel de sumário: estatísticas agregadas em tabelas
        .top offenders: ficheiros mais problemáticos destacados
        .detalhes por ficheiro:
            -cada ficheiro numa secção separada
            -cada plugin com seu estado e resultados
            -issues formatados com cores por severidade
            -hints e mensagens explicativas


7. Pré-requisitos e Considerações Práticas
    1-Sem Dependências Externas:
    O sistema de relatórios não requer bibliotecas externas além do Python padrão:
        .Agregação usa estruturas de dados nativas (dict, list)
        .geração de HTML usa string templates simples
        .parsing de JSON usa bibliotecas padrão json

    2-Robustez e Error Handling:
    O sistema está preparado para:
        .plugins com falhas: se um plugin falhar, o relatório inclui o erro mas continua
        .dados vazios: funciona corretamente mesmmo sem issues encontrados
        .ficheiros grandes: processa eficientemente grandes volumes de dados

    3-Validação de Schema:
    O sistema valida automaticamente que:
        .todos os plugins devolvem o schema esperado
        .o relatório final contém todas as chaves obrigatórias
        .os dados agregados mantêm consistência matemática


8. Troubleshooting Comum:
    1-HTM não abre no browser:
    Verifica se o ficheiro termina em .html e se foi criado no disco:

        ls -lh report.html
        file report.html
    
    2-Contagens incorretas no sumário:
    O sistema tem teste unitário que validam a matemática. Se suspeitar de erros:

        pytest tests/core/test_aggregator.py -v

    3-Relatório vazio ou incompleto:
    Verificar que plugins foram executados:

        jq '.analysis_metadata' report.json




    
