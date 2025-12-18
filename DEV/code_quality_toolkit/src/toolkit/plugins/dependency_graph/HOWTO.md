Membros:

João Neto 2023234004 @Imajellyfish

João Eduardo Duarte 2011187848 @jeduarteldm

Bernardo Fonseca 2021239253 @jF202

Diogo Delvivo 2021150174 @delvivo.diogo1

Catarina Vieira 2023218473 @27634982

Como usar e configurar o plugin DependencyGraph
1. Visão Geral do Uso
O DependencyGraph foi concebido para funcionar como um módulo de análise arquitetural dentro do Toolkit. A sua função é mapear todas as importações (dependências) de um projeto Python. O utilizador não interage diretamente com o parser AST (Abstract Syntax Tree), mas sim com o plugin, que serve como uma camada de abstração inteligente.

Na prática, o utilizador apenas fornece o código-fonte (ficheiros ou diretórios), e o plugin devolve:

Um relatório estruturado (JSON) com todas as dependências categorizadas.

Um Dashboard Visual (HTML) para análise gráfica da arquitetura.

2. Como a Análise é Executada
A execução é transparente e integrada no fluxo do Toolkit:

Acionamento: O utilizador executa o comando de análise (ex: toolkit analyze).

Processamento Interno: O plugin recebe o código e utiliza o módulo nativo ast do Python para varrer a estrutura sintática. Ele identifica declarações import e from ... import, extraindo:

Nome do módulo importado.

Linha de ocorrência.

Tipo de importação (Absoluta vs. Relativa).

Saída de Dados:

JSON: É gerado um relatório detalhado contendo a lista de dependências classificadas (Biblioteca Padrão, Terceiros ou Local), severidade baseada em más práticas e estatísticas agregadas.

Dashboard HTML: É criado o ficheiro dependency_graph_dashboard.html, que permite visualizar graficamente o acoplamento do sistema.

Este fluxo é automático e leve: o utilizador não precisa de instalar ferramentas externas (como o Bandit ou Pylint), pois o plugin usa apenas a biblioteca padrão do Python.

3. Configuração do Plugin
A configuração é realizada através do ficheiro global toolkit.toml. O utilizador pode ajustar o comportamento do plugin para ser mais ou menos rigoroso em relação a padrões de importação.

Parâmetros Configuráveis:

warn_wildcard_imports (Booleano): Controla se importações "coringa" (from x import *) devem ser reportadas com severidade MEDIUM. (Padrão: true)

max_relative_import_level (Inteiro): Define o nível máximo aceitável para importações relativas (ex: from ..utils import x é nível 2). Importações mais profundas que este valor geram avisos. (Padrão: 1)

track_stdlib_modules (Booleano): Define se os módulos da biblioteca padrão do Python (ex: os, json) devem aparecer no relatório e nos gráficos. Desativar isto ajuda a focar apenas em dependências externas e locais. (Padrão: true)

Exemplo de Configuração (toolkit.toml):

Ini, TOML

[rules]
# Penaliza imports do tipo 'from *', aceita imports relativos simples
# e ignora a biblioteca padrão para limpar o relatório.
warn_wildcard_imports = true
max_relative_import_level = 1
track_stdlib_modules = false
Nota: O plugin é resiliente. Se estes campos não existirem no TOML, ele utiliza valores padrão seguros definidos internamente, garantindo que a análise nunca falha por falta de configuração.

4. Visualização dos Resultados (Dashboard)
Para além do JSON, o utilizador deve consultar o ficheiro dependency_graph_dashboard.html gerado na pasta de saída.

Funcionalidades do Dashboard:

Métricas de Arquitetura: Total de importações, número de módulos únicos e contagem de ficheiros analisados.

Distribuição de Tipos: Gráficos que mostram a proporção entre dependências da stdlib, third-party (pacotes externos) e local (módulos do projeto).

Top Consumers: Uma lista dos ficheiros que realizam mais importações, ajudando a identificar módulos com acoplamento excessivo (potenciais "God Classes").

5. Pré-requisitos e Robustez
Sem Dependências Extras: A grande vantagem deste plugin é a sua portabilidade. Não requer pip install de nada extra; funciona em qualquer ambiente que tenha Python instalado.

Tratamento de Erros: O plugin segue a "Golden Rule" de robustez. Se encontrar um ficheiro com erro de sintaxe (código Python inválido), ele não encerra a execução. Em vez disso, gera um relatório de erro controlado para aquele ficheiro específico e continua a analisar o resto do projeto.

6. Cenários de Uso Típicos
Desenvolvimento Local: O programador utiliza o plugin para mapear a estrutura de um projeto desconhecido ou para garantir que não está a criar dependências circulares ou a usar wildcards indevidos antes de submeter o código.

Pipelines CI/CD: O plugin atua como um validador de arquitetura. Pode ser configurado para falhar o build se alguém introduzir from * import * ou se o número de dependências externas crescer inesperadamente.

Documentação Automática: O Dashboard gerado serve como documentação viva das dependências do projeto, útil para onboarding de novos membros na equipa.