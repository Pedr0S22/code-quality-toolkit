Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982

Como usar e configurar o plugin:

1. Instalação e Disponibilização do Plugin

O utilizador não precisa fazer nenhuma configuração especial para tornar o plugin utilizável — basta que o sistema de análise de código (o "Toolkit") carregue automaticamente todos os plugins disponíveis. O ficheiro Python contendo esta classe deve estar localizado dentro da pasta de plugins do Toolkit. Assim que o Toolkit arrancar, ele identifica o plugin através do método get_metadata(), que fornece o nome, versão e descrição, tornando-o pronto para ser usado na análise.

2. Configuração dos Limites de Densidade de Comentários

O utilizador pode configurar o plugin alterando os valores de densidade mínima e máxima permitidos para comentários no código. Esta configuração é feita através de um ficheiro ou objeto ToolkitConfig, no qual o utilizador define regras como min_comment_density e max_comment_density. Quando o Toolkit inicializa os plugins, ele chama automaticamente plugin.configure(config), e esses valores são carregados.
Caso o utilizador não configure nada, o plugin usa os valores por defeito: mínimo 10% e máximo 50% de linhas de comentário.

3. Processo de Utilização Durante a Análise de Código 

Quando o utilizador solicita uma análise normal ao Toolkit—por exemplo, ao pedir que um ficheiro ou projeto seja verificado—o sistema chama automaticamente o método analyze() do plugin. O utilizador não precisa interagir diretamente com o plugin; ele funciona de forma transparente no fluxo normal de análise. O plugin começa por verificar que o ficheiro tem uma sintaxe válida usando ast.parse(). Se a sintaxe estiver incorreta, o utilizador recebe imediatamente um erro claro na saída da análise.

Caso o ficheiro seja válido, o plugin calcula a quantidade de linhas de código e de comentários através do seu método interno _count_lines(). O utilizador não vê esse processo, mas recebe no final os resultados num formato standard do Toolkit: uma lista de problemas encontrados e um sumário de métricas. Se a densidade de comentários estiver abaixo ou acima dos limites configurados, o utilizador recebe uma recomendação explícita indicando se há poucos comentários ou demasiados, com percentagens calculadas e sugestões sobre o que melhorar. Se não houver problemas, o utilizador simplesmente vê que o ficheiro foi analisado com sucesso e pode consultar as métricas de densidade.

4. Interpretação dos Resultados da Análise

Após a análise, o utilizador obtém um relatório estruturado. Nele, surgem os problemas detetados — como densidade demasiado baixa ou demasiado alta — juntamente com sugestões de melhoria. O sumário inclui dados úteis: total de linhas, número de comentários, número de linhas de código e densidade exata. Estes valores permitem ao utilizador compreender rapidamente se o nível de comentários no ficheiro é adequado.

5. Experiência de Uso em Diferentes Cenários

Em desenvolvimento local, o utilizador pode recorrer ao plugin para verificar rapidamente se está a documentar de forma equilibrada. Em ambientes corporativos ou de equipas maiores, o plugin permite reforçar padrões internos, ajudando a manter boa legibilidade e consistência entre ficheiros. Em pipelines de CI, torna-se particularmente útil para impedir commits que não cumpram os critérios mínimos de documentação, ou para alertar sobre ficheiros excessivamente comentados, que podem dificultar a leitura.