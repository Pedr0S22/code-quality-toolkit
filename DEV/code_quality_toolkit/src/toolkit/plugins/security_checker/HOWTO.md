Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982

Como usar e configurar o plugin:

1. Visão Geral do Uso

O SecurityChecker foi concebido para ser usado como parte do Toolkit de análise de código, funcionando como um módulo de segurança que deteta vulnerabilidades através do Bandit. O utilizador não interage diretamente com o Bandit, mas sim com o plugin, que serve como camada de abstração. Na prática, o utilizador apenas fornece código-fonte para análise, e o plugin devolve um relatório estruturado com os problemas de segurança encontrados. O processo de utilização é simples e totalmente integrado no fluxo normal de execução da ferramenta maior onde o plugin está inserido.

2. Como a Análise é Executada

Para usar o plugin, o utilizador precisa apenas de acionar a análise de um ficheiro ou de um bloco de código através da aplicação que integra o SecurityChecker. O plugin receberá o código como texto e, de forma transparente, criará um ficheiro temporário onde esse conteúdo será guardado. Em seguida, o Bandit é executado internamente, analisando o ficheiro para procurar padrões de vulnerabilidades conhecidos. Quando o processo termina, o plugin devolve um relatório JSON contendo uma lista de resultados, como o número da linha onde a vulnerabilidade aparece, o tipo de problema, uma mensagem descritiva e a severidade associada.

Este fluxo é completamente automático: o utilizador não precisa de instalar, executar ou conhecer o Bandit diretamente, o que simplifica muito o uso e torna o plugin acessível mesmo para quem não está familiarizado com ferramentas de segurança.

3. Configuração do Plugin pelo Utilizador

A configuração do SecurityChecker é feita exclusivamente através do ficheiro TOML global do Toolkit, por meio de uma secção rules. O parâmetro mais importante é o nível mínimo de severidade que o plugin deve reportar. O plugin suporta três níveis: LOW, MEDIUM e HIGH. O valor por defeito é LOW, o que significa que todos os problemas — desde os mais leves até aos mais graves — são registados.

Para alterar essa configuração, o utilizador precisa apenas de editar o ficheiro toolkit.toml (ou equivalente) e acrescentar, por exemplo:

[rules]
security_report_level = "MEDIUM"


Com isso, problemas classificados como “LOW” deixam de ser incluídos no relatório, e apenas vulnerabilidades mais significativas passam a ser exibidas. O utilizador não necessita de modificar código e não precisa de saber detalhes internos do Bandit; a configuração é simples, declarativa e centralizada.

Além disso, se o campo não existir no TOML, o plugin continua a funcionar normalmente, recorrendo ao valor padrão configurado no __init__, o que evita falhas e torna o sistema mais resiliente.

4. Pré-requisitos e Considerações Práticas

Antes de utilizar o plugin, é necessário garantir que a dependência Bandit está instalada. Se o plugin for executado sem esse pacote, ele não funciona e devolve uma resposta de erro controlada. O próprio código imprime um aviso visível, explicando o motivo da falha, e a mensagem de erro no relatório final orienta o utilizador a instalar a dependência necessária. Normalmente, esta instalação faz parte do processo make setup do projeto, simplificando ainda mais a preparação do ambiente.

Do ponto de vista prático, o utilizador não precisa de se preocupar com caminhos de ficheiros temporários, limpeza de artefactos ou chamadas diretas ao Bandit, pois o plugin gere tudo automaticamente. O uso é, portanto, altamente conveniente e adequado tanto para fluxos manuais quanto automáticos.

5. Experiência de Uso para Diferentes Cenários

Em ambientes de desenvolvimento local, o utilizador pode simplesmente executar a análise de segurança sempre que quiser verificar rapidamente se um ficheiro contém vulnerabilidades óbvias. Em pipelines CI/CD, o plugin integra-se naturalmente como uma etapa de validação, impedindo que código inseguro seja integrado no repositório. O utilizador final não precisa ajustar nada além do nível de severidade desejado, sendo que todo o restante — desde a análise até ao formato final do relatório — é gerido automaticamente pelo plugin.