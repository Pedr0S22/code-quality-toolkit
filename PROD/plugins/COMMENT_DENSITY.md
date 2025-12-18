Membros:

João Neto 2023234004 @Imajellyfish

João Eduardo Duarte 2011187848 @jeduarteldm

Bernardo Fonseca 2021239253 @jF202

Diogo Delvivo 2021150174 @delvivo.diogo1

Catarina Vieira 2023218473 @27634982

Análise do código do plugin CommentDensity
1. Propósito e Utilidade Geral
Este código implementa o plugin CommentDensity, uma ferramenta de métrica de qualidade de software cujo objetivo é calcular a razão entre linhas de comentários e linhas de código lógico num projeto Python. O plugin identifica tanto a falta de documentação (densidade baixa), que prejudica a manutenção e o onboarding, quanto o excesso de comentários (densidade alta), que pode indicar código complexo ("code smell") ou obsoleto.

A utilidade prática do plugin foi elevada nesta versão com a inclusão de um Dashboard Visual (D3.js). Isso permite que equipas não apenas definam regras de linting (ex: "todo ficheiro deve ter pelo menos 10% de comentários"), mas também visualizem a "saúde documental" do projeto inteiro num gráfico interativo.

2. Funcionamento do Plugin
O ciclo de vida do plugin divide-se em configuração, análise sintática e geração de relatórios:

Configuração e Metadados: O plugin lê os limites de densidade (min_density e max_density) a partir do ficheiro TOML global. Se não configurado, assume valores padrão (10% a 50%).

Análise e "Early Exit": O método analyze inicia com uma verificação de tamanho. Ficheiros muito pequenos (< 5 linhas) são ignorados para evitar ruído estatístico.

Validação AST: Antes de contar linhas, o plugin utiliza ast.parse() para garantir que o ficheiro é código Python válido. Se houver erro de sintaxe, a análise é abortada de forma controlada (status failed).

Motor de Contagem (_count_lines): Esta é a lógica central. O algoritmo percorre o ficheiro linha a linha e é capaz de distinguir:

Comentários de linha única (#).

Comentários inline (código seguido de #).

Docstrings e Comentários Multilinha: O algoritmo rastreia o estado de abertura e fecho de aspas triplas (""" ou '''), garantindo que docstrings de classes e funções sejam contadas corretamente como documentação.

Cálculo e Classificação: Calcula a percentagem (linhas_comentário / total_linhas) e gera issues com severidade HIGH se violar os limites configurados.

Dashboarding: O método generate_dashboard agrega os dados e produz um ficheiro HTML independente (comment_density_dashboard.html). Este utiliza D3.js (Blue Theme) para exibir gráficos de violações e uma lista dos ficheiros com pior documentação.

3. Qualidade da Implementação
A implementação destaca-se pela robustez e precisão do algoritmo de contagem:

Robustez: O uso de blocos try/except abrangentes e a validação prévia com ast.parse asseguram que o plugin segue a "Golden Rule", nunca propagando exceções que possam derrubar o Toolkit principal.

Precisão de Parsing: Diferente de contadores simples que usam apenas Regex, a lógica de estado implementada em _count_lines lida corretamente com docstrings complexas e indentadas, evitando falsos positivos/negativos comuns em ferramentas mais simples.

Separação de Responsabilidades: A lógica de cálculo matemático, a extração de texto e a geração de HTML estão isoladas em métodos distintos, facilitando testes unitários e manutenção.

Visualização: A integração de um Dashboard responsivo adiciona valor gerencial ao plugin, transformando métricas abstratas em insights acionáveis.

4. Utilidade Prática
Na prática, o CommentDensity atua como um fiscal da manutenibilidade do código.

Em Code Reviews: Automatiza a verificação trivial de "este código está comentado?", libertando os revisores humanos para focarem na lógica.

Gestão de Dívida Técnica: O Dashboard permite identificar rapidamente módulos legados que são "caixas pretas" (0% documentação) ou módulos esparguete que exigem explicação excessiva (densidade > 50%).

Pipelines CI/CD: Pode ser configurado para bloquear merges se a documentação do novo código não atingir os padrões mínimos da equipa.