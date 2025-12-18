Membros:

João Neto 2023234004 @Imajellyfish

João Eduardo Duarte 2011187848 @jeduarteldm

Bernardo Fonseca 2021239253 @jF202

Diogo Delvivo 2021150174 @delvivo.diogo1

Catarina Vieira 2023218473 @27634982

Como usar e configurar o plugin CommentDensity
1. Visão Geral do Uso
O CommentDensity foi desenhado para ser uma ferramenta de métrica de qualidade "zero-configuração" inicial. Assim que o Toolkit de análise de código é executado, o plugin entra em ação automaticamente para verificar todos os ficheiros Python do projeto.

O utilizador não precisa de instalar dependências externas nem executar comandos manuais de contagem. O plugin integra-se no fluxo padrão de análise, devolvendo alertas sempre que um ficheiro viola as regras de documentação estipuladas pela equipa.

2. Como a Análise é Executada
O processo ocorre de forma transparente em quatro etapas:

Validação: O plugin verifica primeiro se o ficheiro é código Python válido (usando ast.parse). Se houver erros de sintaxe, o utilizador é notificado imediatamente no relatório de erros.

Filtragem: Ficheiros muito pequenos (menos de 5 linhas) são ignorados automaticamente para evitar ruído (ex: ficheiros __init__.py vazios).

Contagem Inteligente: O plugin conta as linhas de código lógico versus linhas de comentários (incluindo docstrings e comentários inline).

Relatórios:

JSON: Gera um relatório técnico com a densidade calculada (ex: 0.15 para 15%) e, se necessário, emite um aviso (LOW_COMMENT_DENSITY ou HIGH_COMMENT_DENSITY).

Dashboard HTML: Gera um gráfico visual para análise macro do projeto.

3. Configuração do Plugin
O utilizador pode ajustar a rigorosidade do plugin através do ficheiro global toolkit.toml (na secção rules ou na secção específica do plugin, dependendo da versão do Core).

Parâmetros Configuráveis:

min_density (Float): A percentagem mínima de comentários exigida. (Padrão: 0.1 = 10%).

max_density (Float): A percentagem máxima de comentários permitida antes de ser considerado excessivo. (Padrão: 0.5 = 50%).

Exemplo de Configuração (toolkit.toml):

Ini, TOML

[rules]
# Exige que pelo menos 20% do código seja documentado,
# mas permite até 60% antes de alertar sobre excesso.
min_density = 0.2
max_density = 0.6
Nota: Se o utilizador não configurar estes valores, o plugin utiliza os padrões seguros (10% a 50%).

4. Visualização dos Resultados (Novo Dashboard)
Para além dos logs no terminal, o utilizador tem agora acesso ao ficheiro comment_density_dashboard.html.

Como interpretar o Dashboard:

Cabeçalho: Mostra o total de ficheiros analisados e quantas violações foram encontradas.

Gráfico de Violações (Blue Theme): Exibe visualmente quantas violações são por "Falta de Comentários" (Low Density) versus "Excesso de Comentários" (High Density).

Top Offenders: Uma lista dos ficheiros que mais se desviam dos padrões, permitindo ao utilizador focar a refatoração nos piores casos.

5. Interpretação dos Resultados da Análise
No relatório final (JSON ou Terminal), o utilizador encontrará métricas claras para cada ficheiro analisado:

Code Lines: Quantidade de linhas de código executável.

Comment Lines: Quantidade de linhas identificadas como documentação.

Density: O valor calculado.

Se Density < min_density: O plugin sugere "Add documentation".

Se Density > max_density: O plugin sugere "Simplify comments".

6. Experiência de Uso em Diferentes Cenários
Desenvolvimento Local: O programador corre o Toolkit antes de submeter o código. Se o plugin reclamar de "Low Density", o programador sabe que deve adicionar docstrings às suas funções antes de fazer o commit.

Code Reviews: Em equipas grandes, o plugin serve como um árbitro imparcial. Em vez de discutir subjetivamente se "o código está bem documentado", a equipa define um valor no TOML (ex: 15%) e o plugin garante o cumprimento desse padrão.

Manutenção de Legado: Ao pegar num projeto antigo, o Dashboard permite identificar rapidamente quais os módulos que são "caixas pretas" (sem comentários) para priorizar a criação de documentação técnica.