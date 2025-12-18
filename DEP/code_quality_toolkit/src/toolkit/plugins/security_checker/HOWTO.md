Membros:

João Neto 2023234004 @Imajellyfish

João Eduardo Duarte 2011187848 @jeduarteldm

Bernardo Fonseca 2021239253 @jF202

Diogo Delvivo 2021150174 @delvivo.diogo1

Catarina Vieira 2023218473 @27634982

Como usar e configurar o plugin SecurityChecker
1. Visão Geral do Uso
O SecurityChecker funciona como um módulo de segurança integrado ao Toolkit, atuando como uma camada de abstração sobre a ferramenta Bandit. O seu objetivo é simplificar a análise de segurança: o utilizador fornece o código-fonte e o plugin encarrega-se de orquestrar a verificação, filtrar os resultados e, agora, gerar visualizações gráficas.

O utilizador obtém dois tipos de saída:

Um relatório estruturado (JSON) para processamento automático (ex: CI/CD).

Um Dashboard Interativo (HTML) para análise visual humana.

2. Como a Análise é Executada
A utilização é transparente e automática. Ao acionar o comando de análise do Toolkit (ex: toolkit analyze):

Ingestão: O plugin recebe o código como texto.

Preparação: Cria um ficheiro temporário seguro com o conteúdo do código.

Execução do Motor: Invoca o motor do Bandit internamente para varrer o ficheiro à procura de padrões de vulnerabilidade (ex: B307 para eval, B102 para exec).

Geração de Artefactos:

Compila os resultados no JSON global do Toolkit.

Gera automaticamente o ficheiro security_checker_dashboard.html no diretório de saída.

Limpeza: Remove o ficheiro temporário, garantindo que nenhum código sensível persista no disco desnecessariamente.

3. Configuração do Plugin
A configuração do SecurityChecker é realizada através do ficheiro global toolkit.toml. O principal parâmetro de controlo é o nível de severidade.

Parâmetros Suportados:

security_report_level: Define o nível mínimo de severidade para que uma vulnerabilidade seja reportada.

Valores aceites: "LOW", "MEDIUM", "HIGH".

Valor por defeito: "LOW" (Reporta tudo).

Exemplo de Configuração (toolkit.toml):

Ini, TOML

[rules]
# Apenas vulnerabilidades críticas (High) e médias (Medium) aparecerão no relatório e dashboard.
security_report_level = "MEDIUM"
Nota: Se a configuração for omitida, o plugin assume o nível "LOW" para garantir a máxima visibilidade dos problemas.

4. Visualização dos Resultados (Novo Dashboard)
Uma das grandes vantagens desta versão é o Dashboard de Segurança. Após a execução, o utilizador deve abrir o ficheiro security_checker_dashboard.html no seu navegador.

O que o Dashboard oferece:

Métricas de Topo: Contagem total de vulnerabilidades e ficheiros afetados.

Gráfico de Severidade (Red Theme): Um gráfico de barras que mostra a distribuição de riscos (quantos são HIGH, MEDIUM ou LOW).

Lista de Infratores: Uma lista ordenada dos ficheiros com maior número de vulnerabilidades, permitindo priorizar a refatoração.

5. Pré-requisitos e Dependências
O plugin possui uma dependência estrita do pacote bandit.

O ambiente Python onde o Toolkit corre deve ter o Bandit instalado (pip install bandit).

Caso o Bandit não esteja presente, o plugin não iniciará e emitirá um erro explícito no log, garantindo que o utilizador não tenha uma falsa sensação de segurança por uma análise silenciosa ou incompleta.

6. Experiência de Uso para Diferentes Cenários
Auditoria Local: O desenvolvedor corre a ferramenta e abre imediatamente o Dashboard HTML para ver "onde está o fogo" (vulnerabilidades críticas) através dos gráficos vermelhos de alerta.

Pipelines CI/CD: O sistema de integração contínua lê o output JSON. Se o plugin detetar vulnerabilidades com severidade acima do configurado, o pipeline pode ser configurado para bloquear o merge ou o deployment, agindo como um Quality Gate de segurança.