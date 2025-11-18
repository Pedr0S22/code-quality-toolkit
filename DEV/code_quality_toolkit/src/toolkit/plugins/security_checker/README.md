Membros:

João Neto  2023234004  @Imajellyfish
João Eduardo Duarte  2011187848  @jeduarteldm
Bernardo Fonseca  2021239253  @jF202 
Diogo Delvivo  2021150174  @delvivo.diogo1 
Catarina Vieira 2023218473  @27634982

Análise do código do plugin security_checker:

1. Propósito e Utilidade Geral

Este código implementa um plugin chamado SecurityChecker, cuja função é servir como um wrapper para a ferramenta Bandit, um analisador estático especializado em detecção de vulnerabilidades em código Python. O plugin executa o Bandit nos ficheiros fornecidos e converte os seus resultados para o formato interno esperado pelo Toolkit. A utilidade prática é significativa: ele permite identificar padrões perigosos como uso de eval, pickle inseguro, injeção de SQL e outros problemas de segurança. Esse tipo de plugin é essencial em pipelines de CI, auditorias de segurança, ferramentas de análise estática e processos de conformidade.

2. Funcionamento do Plugin

O plugin é inicializado verificando se o Bandit está instalado; caso não esteja, informa o utilizador e continua de forma controlada. Possui um método para fornecer metadados básicos e um método de configuração que lê regras do arquivo TOML global, especialmente o nível mínimo de severidade dos problemas que devem ser reportados.

O método principal é o analyze, que segue uma estratégia clara: primeiro aplica o princípio da “Golden Rule”, garantindo que nenhum erro escape para fora do plugin. Depois, como o Bandit só funciona com ficheiros físicos, o código cria um ficheiro temporário e escreve nele o conteúdo a ser analisado. Em seguida, inicializa o Bandit, descobre o ficheiro, executa os testes e recolhe os resultados. Estes resultados são então filtrados conforme o nível de severidade estabelecido e convertidos para um formato unificado, contendo severidade, código da vulnerabilidade, mensagem, localização no código e uma dica associada. Após o processo, o ficheiro temporário é apagado para evitar resíduos. Finalmente, o método devolve um relatório contendo todos os problemas encontrados ou um relatório de falha em caso de erro inesperado.

3. Qualidade da Implementação

O código é estruturado para demonstrar práticas em vários aspetos. A verificação inicial das dependências garante que falhas de configuração possam ser tratadas de maneira controlada. O uso de ficheiros temporários é apropriado, visto que o Bandit não aceita apenas strings. A limpeza desses ficheiros é garantida através de um bloco finally, independente de sucesso ou falha. A conversão de resultados do Bandit para o formato interno é clara, consistente e inclui tradução de severidades para um padrão próprio.

Além disso, o uso de um bloco try/except amplo garante que o plugin nunca lança exceções para fora, respeitando a regra de robustez do sistema. Outro ponto positivo é o mapeamento explícito das severidades e a possibilidade de configurar o nível de reporte através do arquivo TOML.

4. Utilidade Prática

Em ambiente real, este plugin é altamente útil para garantir práticas de segurança no código Python. Este automatiza a deteção de vulnerabilidades comuns, melhora a qualidade do software e ajuda a prevenir falhas antes que cheguem à produção. Integrado com pipelines CI, pode funcionar como uma barreira de segurança obrigatória, impedindo deploys de código inseguro. Também é útil em revisões de código automatizadas ou como parte de um conjunto maior de ferramentas de análise estática.