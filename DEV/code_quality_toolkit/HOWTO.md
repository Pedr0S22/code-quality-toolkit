# Guia de Utilizador (User Guide)

Este guia descreve como utilizar o **Code Quality Toolkit** para analisar projetos, configurar opções e interpretar os resultados.

## 1. Como executar uma análise

Para iniciar uma análise, utilize o comando `analyze` através da CLI.

**Sintaxe Básica:**
```bash
python -m toolkit.core.cli analyze <caminho_para_analisar> [opções]
```

## 2. Opções da CLI

Pode personalizar a execução utilizando as seguintes *flags*:

| Opção | Descrição | Exemplo |
| :--- | :--- | :--- |
| `--plugins` | Define quais plugins executar (separados por vírgula). O padrão é `all`. | `--plugins StyleChecker,CyclomaticComplexity` |
| `--out` | Define o caminho do ficheiro de saída JSON. | `--out resultados.json` |
| `--include-glob` | Padrão de ficheiros a incluir. Pode ser repetido. | `--include-glob "**/*.py"` |
| `--exclude-glob` | Padrão de ficheiros a ignorar (ex: testes). | `--exclude-glob "tests/**"` |
| `--fail-on-severity` | Define um nível de severidade que fará a ferramenta falhar (exit code > 0). | `--fail-on-severity high` |

---

## 3. Interpretar o Relatório (`report.json`)

O relatório final é um ficheiro JSON dividido em três secções.

### Estrutura do Relatório

**`analysis_metadata`**: Informações sobre a execução (data, versão, plugins usados).
    * **Nota sobre o estado `partial`**: Se o campo `status` for `"partial"`, significa que **um ou mais plugins falharam**, mas a análise continuou para os restantes. Verifique os erros nos detalhes.
**`summary`**: Estatísticas globais (total de erros, contagem por severidade).
**`details`**: Lista detalhada de todas as ocorrências encontradas, agrupadas por ficheiro.