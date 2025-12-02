# Security checker to see any malicious intent that might be present on any file
from __future__ import annotations

import os
import tempfile
from typing import Any

# Imports do Bandit (a ferramenta que faz o trabalho)
try:
    from bandit.core.config import BanditConfig
    from bandit.core.constants import HIGH, LOW, MEDIUM
    from bandit.core.manager import BanditManager

except ImportError:
    # Se o Bandit não estiver instalado, estas classes não existem.
    # O plugin vai falhar, mas o nosso 'except' no 'analyze' vai pegar.
    BanditConfig = None
    BanditManager = None
    LOW, MEDIUM, HIGH = None, None, None

# 2. Imports do Core do Projeto
from ...core.contracts import IssueResult
from ...utils.config import ToolkitConfig


# --- TAREFA 9: Implementação da API  ---
class Plugin:
    """
    Plugin de Segurança: Um "wrapper" (adaptador) que executa o Bandit
    e traduz os seus resultados para o formato do Toolkit.

    """

    def __init__(self) -> None:
        """Inicializa o plugin."""
        # Verifica se o import do Bandit funcionou
        # Só avisar se efectivamente não temos o Bandit disponível
        if BanditManager is None:
            print(
                "AVISO: Dependência 'bandit' não instalada. "
                "O SecurityChecker não vai funcionar. Usando verificação fallback."
            )
        # TAREFA 7: Configuração (TOML)
        # O Bandit usa o seu próprio ficheiro, mas podemos definir o nível
        # de severidade que queremos reportar.
        self.report_severity_level = "LOW"  # Reporta Low, Medium, e High

    def get_metadata(self) -> dict[str, str]:
        return {
            "name": "SecurityChecker",
            "version": "1.0.0",
            "description": (
                "Deteta vulnerabilidades (eval, pickle, SQLi, etc.) usando o Bandit."
            ),
        }

    def configure(self, config: ToolkitConfig) -> None:
        """
        TAREFA 7: Configura o plugin a partir do ficheiro TOML global.

        """

        # Como não podemos mudar o config.py, temos de verificar se o atributo
        # 'security_report_level' existe ANTES de tentar ler.
        # Se não existir, ele simplesmente ignora e usa o valor 'default' ('LOW')
        # definido no __init__.
        if hasattr(config.rules, "security_report_level"):
            self.report_severity_level = config.rules.security_report_level

    def analyze(self, source_code: str, file_path: str | None) -> dict[str, Any]:
        """
        TAREFA 8: Corre a análise no ficheiro e devolve um Relatório JSON.
        Isto NUNCA DEVE levantar uma exceção (seguindo a Golden Rule).
        """

        # Inicializa a estrutura padrão de retorno
        report = {
            "results": [],
            "summary": {"issues_found": 0, "status": "completed"},
        }

        try:
            results: list[IssueResult] = []

            # --- Fallback scanner se Bandit não estiver disponível ---
            if BanditManager is None:
                src = source_code or ""
                lines = src.splitlines()

                def find_lineno(substr: str) -> int:
                    for idx, line in enumerate(lines, start=1):
                        if substr in line:
                            return idx
                    return 1

                # Heurísticas simples
                if "eval(" in src:
                    results.append({
                        "severity": "high",
                        "code": "B307",
                        "message": "Uso de eval() detectado.",
                        "line": find_lineno("eval("),
                        "col": 1,
                        "hint": "Evite usar eval() em código não confiável.",
                    })

                if "exec(" in src:
                    results.append({
                        "severity": "high",
                        "code": "B307",
                        "message": "Uso de exec() detectado.",
                        "line": find_lineno("exec("),
                        "col": 1,
                        "hint": "Evite usar exec() em código não confiável.",
                    })

                if "import pickle" in src or "pickle.load" in src:
                    results.append({
                        "severity": "medium",
                        "code": "B301",
                        "message": "Uso de pickle detectado.",
                        "line": find_lineno("pickle"),
                        "col": 1,
                        "hint": "Evite usar pickle para dados não confiáveis.",
                    })

                if "hashlib.md5" in src or ".md5(" in src:
                    results.append({
                        "severity": "low",
                        "code": "B303",
                        "message": "Uso de hash MD5 detectado.",
                        "line": find_lineno("md5"),
                        "col": 1,
                        "hint": "Use hashes seguros como sha256 para segurança.",
                    })

                if "os.system" in src and "+" in src:
                    results.append({
                        "severity": "medium",
                        "code": "B601",
                        "message": (
                            "Chamadas ao sistema com concatenação de strings "
                            "detectadas."
                        ),
                        "line": find_lineno("os.system"),
                        "col": 1,
                        "hint": (
                            "Use chamadas seguras sem "
                            "concatenar input do utilizador."
                        ),
                    })


                if "%s" in src and "cursor.execute" in src:
                    results.append({
                        "severity": "high",
                        "code": "B606",
                        "message": "Possível injeção SQL detectada.",
                        "line": find_lineno("cursor.execute"),
                        "col": 1,
                        "hint":(
                            "Use queries parametrizadas em vez de "
                            "formatação direta."
                        ),

                    })

                if "PASSWORD" in src and "=" in src and ('"' in src or "'" in src):
                    results.append({
                        "severity": "low",
                        "code": "B105",
                        "message": "Senha hardcoded detectada.",
                        "line": find_lineno("PASSWORD"),
                        "col": 1,
                        "hint": "Nunca guarde segredos em código fonte.",
                    })

                return {
                    "results": results,
                    "summary": {"issues_found": len(results), "status": "completed"},
                }
            
            # Como o bandit analisa ficheiros e não linha a linha
            # Criamos um ficheiro temporário para ele analisar
            # Usamos 'delete=False' para o ficheiro não ser apagado
            # imediatamente, para que o Bandit o possa ler.
            with tempfile.NamedTemporaryFile(
                suffix=".py",
                delete=False,
                mode="w",
                encoding="utf-8",
            ) as temp_file:
                temp_file.write(source_code)
                temp_file_path = temp_file.name  # Guardamos o caminho do ficheiro

            try:
                # 2. Criar uma config e um gestor do Bandit
                config = BanditConfig()
                manager = BanditManager(config=config, agg_type="vuln")

                # 3. Mandar o Bandit "descobrir" o nosso ficheiro temporário
                manager.discover_files([temp_file_path])

                # 4. Executar o Bandit (nos ficheiros que ele descobriu)
                # (Isto cumpre as TAREFAS 2, 3, 4, 5, 6 de uma só vez)
                manager.run_tests()

                # 5. Mapear o nosso nível de severidade para o do Bandit
                severity_map = {"LOW": LOW, "MEDIUM": MEDIUM, "HIGH": HIGH}
                report_level = severity_map.get(self.report_severity_level, LOW)

                # 6. Obter os resultados do Bandit
                bandit_issues = manager.get_issue_list(
                    sev_level=report_level, conf_level=LOW
                )

                # 7. TRADUZIR os resultados do Bandit para o nosso formato JSON
                for issue in bandit_issues:
                    severity_translation = {
                        "LOW": "low",
                        "MEDIUM": "medium",
                        "HIGH": "high",
                    }
                    results.append(
                        {
                            "severity": severity_translation.get(issue.severity, "low"),
                            "code": issue.test_id,  # ex: B301 (pickle) ou B307 (eval)
                            "message": issue.text,
                            "line": issue.lineno,
                            "col": issue.col_offset + 1,
                            "hint": f"Bandit Test ID: {issue.test_id}",
                        }
                    )

            finally:
                # 8. Limpar (apagar o ficheiro temporário), funcionando ou não
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # Devolve uma Resposta de Sucesso
            return {
                "results": results,
                "summary": {
                    "issues_found": len(results),
                    "status": "completed",
                },
            }

        except Exception as e:
            # TAREFA 13: Error Handling
            # Apanha todos os outros erros e Devolve uma Resposta de Falha
            return {
                "results": [],
                "summary": {
                    "issues_found": 0,
                    "status": "failed",
                    "error": f"Erro interno no BanditSecurityChecker: {str(e)}",
                },
            }
