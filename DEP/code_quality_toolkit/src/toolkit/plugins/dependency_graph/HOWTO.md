Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982

Como usar e configurar o plugin:

1. Visão Geral do Uso:

O Dependency Graph foi concebido para ser usado como parte do Toolkit de análise de código, funcionando como um módulo de análise de dependências que mapeia todas as importações de um projeto Python. O user não interage diretamente com o parser AST, mas sim com o plugin, que serve como camada de abstração. 

Na prática, o user apenas fornece código-fonte para análise, e o plugin devolve um relatório estrturado com todas as dependências identificadas, categorizadas e com estatísticas detalhadas.

O processo de utilização é simples e totalmente integrado no fluxo normal de execução da ferramenta maior onde o plugin está inserido.


2. Como a Análise é Executada:

Para usar o plugin, o user precisa apenas de acionar a análise de um ficheiro ou de um bloco de código através da aplicação que integra o Dependency Graph. O plugin receberá o código como texto e, de forma transparente, analisará a sua estrutura sintática usando o módulo ast do Python. Este processo identifica todos os statements de importação, tanto "import" como "from ... import", extraindo informações coom o nome do módulo, linha onde aparece, tipo de importação e nível de importção relativa.

Quando o processo termina, o plugin devolve um relatório JSON??? contendo uma lista de resultados com cada dependência encontrada, incluindo informações sobre a sua categoria(biblioteca padrão, pacote externo ou módulo local), severidade baseada em padrões potencialmente problemáticos, e mensagens descritivas. Além disso, inclui um sumário com estatísticas agregadas e dados para contrução de grafos de dependência.

Este fluxo é completamente automático: o user não precisa de instalar ferramentas externas al+em do Python padrão, o que simplifica muito o uso e torna o plugin acessível mesmo para quem não está familiarizado com análise de dependências.


3. Configuração do Plugin pelo User:

A configuração do Dependency Graph é feita atrav+es do ficheiro TOML global do Toolkit, por meio de uma secção rules. Os parâmetro disponíveis incluem:

- warn_wildcard_imports: controla se importações wildcard (from x import *) devem ser reportadas como severidade mais alta.

- max_relative_import_level: define o nível máximo aceitável para importações relativas antes de serem reportadas como problemáticas.

- track_stdlib_modules: define se módulos da biblioteca padrão devem ser incluídos no relatório.

Paara alterar estas configurações, o user precisa apenas de editar o ficheiro TOML e acrescentar, por exemplo:

[rules]
warn_wildcard_imports= true
max_relative_import_level= 1
track_stdlib_modules= false

Com estas configurações, o plugin adaptará o seu comportamento: wildcard imports serão marcados como "medium", importações relativas profundas serão destacadas, e módulos da stdlib serão excluídos do relatório final, focando apenas em dependências externas e locais.

O user não necessita de modificar código e não precisa de saber detalhes internos do AST, a configuração é simples, declarativa e centralizada.

Além disso, se estes campos não existirem no TOML, o plugin continua a funcionar normalmente, recorrendo aos valores padrão configurados no __init__, o que evita falhas e torna o sistema mais resiliente.


4. Pré-requisitos e Considerações Práticas:

Uma das grandes vantagens deste plugin é que não requer dependências externas além do Python padrão. O módulo "ast" faz parte da biblioteca padrão do Python, pelo que o plugin está sempre pronto a ser usado sem instalações adicionais.

Do ponto de vista prático, o utilizador não precisa de se preocupar com parsing manual, tratamento de erros sintáticos ou construção de estruturas de dados complexas, pois o plugin gere tudo automaticamente. O uso é, portanto, altamente conveniente e adequado tanto para fluxos manuais quanto automáticos.

o plugin também é robusto face a erros de sintaxe: se o código fornecido não for Python válido, o plugin devolve um relatório de erro controlado sem crashar, explicando o problema encontrado.


5. Experiência de Uso para Diferentes Cenários:

- Desenvolvimento Local:em ambientes de desenvolvimento local, o user pode executar a análise de dependências sempre que quiser. Para verificar rapidamente todas as dependências de um ficheiro, identificar dependências circulares potenciais, descobrir dependências externas que precisam de ser instaladas, ou mapear a estrutura de imports de um projeto.

- Pipelines CI/CD: em pipelines CI/CD, o plugin naturalmente como uma etapa de validação, permite verificar se existem wildcard imports no código, garantir que não há importações relativas excessivamente profundas, gear relatórios de dependências para documentação, e monitorizar o crescimento de dependências externas ao longo do tempo.

- Análise de Projetos: para análise de projetos completos, o plugin pode identificar todos os módulos externos usado, mapear a estrutura de dependências internas, detetar padrões de acoplamento excessivo, e fornecer dados para visualização de grafos de dependência.

O user final não precisa de ajustar nada além das configurações desejadas, sendo que todo o restantes, desde a análise até ao formato final do relatório, é gerido automaticamente pelo plugin.