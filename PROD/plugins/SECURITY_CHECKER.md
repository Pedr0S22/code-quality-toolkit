Membros:

João Neto 2023234004 @Imajellyfish

João Eduardo Duarte 2011187848 @jeduarteldm

Bernardo Fonseca 2021239253 @jF202

Diogo Delvivo 2021150174 @delvivo.diogo1

Catarina Vieira 2023218473 @27634982

Análise do código do plugin SecurityChecker
1. Propósito e Utilidade Geral
Este código implementa um plugin chamado SecurityChecker, cuja função primordial é atuar como um wrapper robusto para a ferramenta Bandit, um analisador estático de segurança para código Python. O plugin executa o Bandit nos ficheiros fornecidos e normaliza os resultados para o ecossistema do Toolkit.

A sua utilidade foi expandida significativamente nesta versão: além de identificar vulnerabilidades críticas (como uso de eval, injeção de SQL, cifras fracas, etc.), o plugin agora gera automaticamente um Dashboard visual (D3.js). Isso torna a auditoria de segurança não apenas técnica, mas também visualmente acessível, facilitando a identificação rápida de ficheiros de alto risco em pipelines de CI e processos de compliance.

2. Funcionamento do Plugin
O funcionamento do plugin foi refatorado para garantir maior confiabilidade e integridade dos dados:

Inicialização Estrita: Ao contrário das versões anteriores, o plugin agora impõe uma dependência estrita do pacote bandit. Se a ferramenta não estiver instalada, o plugin interrompe a inicialização imediatamente com um ImportError, garantindo que não haja "falsos negativos" causados pela ausência da ferramenta de análise.

Configuração: O plugin lê as configurações do sistema (via ToolkitConfig), permitindo ajustar o nível mínimo de severidade (LOW, MEDIUM, HIGH) para filtrar os relatórios de vulnerabilidade.

Análise (analyze): O método segue um fluxo rigoroso:

Criação de um ficheiro temporário com o código fonte (necessário para o Bandit).

Execução da suite de testes do Bandit sobre esse ficheiro.

Filtragem e mapeamento dos resultados para o formato padrão do Toolkit.

Limpeza garantida dos resíduos (ficheiros temporários) através de blocos finally.

Geração de Dashboard (generate_dashboard): Após a análise, o plugin agrega os dados e gera um relatório HTML independente (security_checker_dashboard.html). Este relatório utiliza a biblioteca D3.js para criar gráficos interativos (tema vermelho) que exibem a distribuição de severidade e uma lista dos ficheiros mais vulneráveis.

3. Qualidade da Implementação
A implementação demonstra maturidade técnica em vários aspetos:

Robustez e "Golden Rule": O código mantém a filosofia de capturar exceções durante a análise para não derrubar o processo principal (try/except), reportando falhas de forma estruturada no JSON final.

Eliminação de Código Morto/Fallback: A remoção do antigo scanner de fallback (baseado em strings simples) melhorou a precisão do plugin. Agora, confia-se inteiramente na análise AST sofisticada do Bandit, eliminando redundâncias e complexidade desnecessária.

Visualização de Dados: A implementação do método de dashboarding, com suporte a templates HTML e agregação de métricas (_aggregate_data_for_dashboard), adiciona uma camada de valor significativa ao produto final, permitindo uma leitura gerencial dos dados técnicos.

Testabilidade: O código foi estruturado para ser altamente testável, permitindo a injeção de configurações e a validação da geração de ficheiros sem efeitos colaterais persistentes.

4. Utilidade Prática
Em cenários reais de desenvolvimento, o SecurityChecker atua como um guardião da qualidade de segurança. A sua capacidade de bloquear a análise se as ferramentas não estiverem presentes evita a falsa sensação de segurança. A integração do relatório visual permite que equipas de desenvolvimento e gestores visualizem rapidamente o "estado de saúde" da segurança do projeto, identificando hotspots de vulnerabilidade sem necessidade de ler logs JSON extensos. É uma ferramenta essencial para DevSecOps e auditorias automáticas.