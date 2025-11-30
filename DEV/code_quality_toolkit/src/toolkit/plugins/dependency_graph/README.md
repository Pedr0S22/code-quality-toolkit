Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982

Análise do código do plugin dependency_graph:

1. Propósito e Utilidade Geral

Este código implementa um plugin chamado Dependency Graph, cuja função é analisar e mapear todas as dependênias(imports) de código Python. O plugin utiliza o módulo "ast", Abstract Syntax Tree, da biblioteca padrão do Python para fazer parsing do código-fonte e extrair informação estruturada sobre todas as declarações de importação. A utilidade prática é significativa: permite identificar todas as dependências de um projeto, categorizá-las(biblioteca padrão, pacotes externos, módulos locais), detetar padrões problemáticos (como wildcard imports ou importações relativas excessivas) e fornecer dados estruturados para visualização de grafos de dependência. Este tipo de plugin é essencial em gestão de projetos, documentação automatizada, análise de acoplamento, auditorias de dependências e processos de manutenção de código.

2. Funcionamento do Plugin:

O plugin é inicializado definindo uma lista de módulos da biblioteca padrão do Python, para categorização, e configurações padrão relacionadas com avisos sobre padrões problemáticos. Possui um método para fornecer metadados básicos e um método de configuração que lê regras do arquivo TOML global, especialmente configurações sobre wildcard import, nível máximo de importações relativas e se deve rastrear módulos stdlib.

O método principal é o "analyze", que segue uma estratégia robusta e estruturada:

- Parsing AST: primeiro tenta fazer o parsing do código-fonte usando ast.parse(). Se o código contiver erros de sintaxe, o processo é interrompido de forma controlada e devolve um relatório de erro.

- Extração de Imports: o método _extract_imports() percorre toda a árvore AST usando ast.walk(), identificando nós do tipo sat.import e as.ImportFrom. Para cada import encontrado, extrai informações como: tipo de informação, nome do módulo, alias se existir, linha no código, nível de importação relativa (0= absoluta, 1+= relativa), e nomes específicos importados (no caso de from-import).

- Categorização: o método _categorize_imports() classifica cada import em 3 categorias: stdlib (módulos da biblioteca padrão do Python), third_party (pacotes externos instalados via pip), local (módulos locais do projeto, incluindo imports relativos). A categorização usa heurísticas como verificação contra lista de módulos conhecidos, análise de importações relativas (level>0), e padrões de nomenclatura.

- Avaliação de Severidade: o método _assess_severity() analisa cada import para determinar o seu nível de importância/risco. Importações relativas profundas (level>1) são marcadas como "medium". Wildcard imports (from x import *) são marcados como "medium" se configurado. Importações normais são marcados como "info".

- Geração de Mensagens: o método _genetate_message() cria mensagens descritivas para cada import, incluindo informação sobre categoria, avisos para padrões problemáticos,e conttexto adicional.

- Criação de Sumário: o método _create_summary() agrega estatísticas como total de imports, distribuição por categoria, número de módulos únicos, e contrói uma estrutura de dados, dependency_graph, adequada para visualização.

- Contrução de grafo: o méotodo _build_graph_data() organiza os dados numa estrutura facilita a criação de visualizações de grafos de dependência, separando nós por categoria.

Após todo o process, o étodo devlve um relatório JSON contendo todos os imports encontrados com suas classificações, mensagens e estatísticas agregadas. Em caso de erro, como SyntaxError, devolve um relatório de falha controlado sem propagrar exceções.


3. Qualidade da Implementação:

O código demostra várias boas práticas de engenharia de software:
 - Robustez: o uso de try-except garante que erros de sintaxe sejam tratados graciosamente, devolvendo relatórios de erros estruturados em vez de crashar. Isto segue o princípio da "Golden Rule" de nunca lançar execeções fora do plugin.

 - Modularização: o c´doigo está bem organizado em métodos privados com responsabilidades claras (_extract_imports, _categorize_imports, _assess_severity, etc.), facilitando manutenção e testes.

 - Configurabilidade: o plugin aceita configuração via TOML, mas funciona com valores padrão razoáveis se a configuração não existir, tornando-o resiliente a diferentes ambientes.

 - Sem Dependências Externas: ao usar apenas o módulo ast da stdlib, o plugin não requer instalação de pacotes adicionais, simplificando deployment.

 - Informação Rica: o plugin não só identifica imports, mas também os categoriza, avalia severidade, gera mensagens contextuais e cria estruturas de dados para visualização.

 - Type Hints: o uso de type hints melhora a legibilidade e permite deteção de erros estáticos.

 - Documentação: Docstrings claras explicam o propósito de cada método e os seus parâmetro/returns.