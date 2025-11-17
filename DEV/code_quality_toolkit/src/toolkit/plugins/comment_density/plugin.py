import ast
from typing import Any

from toolkit.utils.config import ToolkitConfig


class Plugin:
    """Comment Density Analyzer Plugin"""
    
    def __init__(self) -> None:
        self.min_density = 0.1  # 10% default
        self.max_density = 0.5  # 50% default
        self.config = None
    
    def configure(self, config: ToolkitConfig) -> None:
        """Configure plugin with rules"""
        self.config = config
        self.min_density = getattr(config.rules, 'min_comment_density', 0.1)
        self.max_density = getattr(config.rules, 'max_comment_density', 0.5)
    
    def get_metadata(self) -> dict[str, str]:
        """Return plugin metadata"""
        return {
            "name": "CommentDensity",
            "version": "0.1.0", 
            "description": "Analyzes comment density in source code"
        }
    
    def _count_lines(self, source: str) -> tuple[int, int]:
        """Count code and comment lines"""
        lines = source.split('\n')
        code_lines = 0
        comment_lines = 0
        in_multiline_comment = False
        multiline_comment_char = None
        
        for _line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            if in_multiline_comment:
                comment_lines += 1
                if multiline_comment_char in stripped_line:
                    if (stripped_line.endswith(multiline_comment_char) or 
                        stripped_line.count(multiline_comment_char) >= 2):
                        in_multiline_comment = False
                continue
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                comment_lines += 1
                if stripped_line.startswith('"""'):
                    multiline_comment_char = '"""'
                else:
                    multiline_comment_char = "'''"
                if (stripped_line.endswith(multiline_comment_char) and 
                    len(stripped_line) > 3 and 
                    stripped_line.count(multiline_comment_char) == 2):
                    in_multiline_comment = False
                else:
                    in_multiline_comment = True
                continue
            
            if '#' in stripped_line:
                parts = stripped_line.split('#', 1)
                code_part = parts[0].strip()
                comment_part = parts[1] if len(parts) > 1 else ""
                
                if code_part:
                    code_lines += 1
                if comment_part:
                    comment_lines += 1
                elif not code_part:
                    comment_lines += 1
            else:
                code_lines += 1
        
        return code_lines, comment_lines
    
    def analyze(self, source: str, filename: str) -> dict[str, Any]:
        """Analyze comment density in source code"""
        try:
            ast.parse(source)
            
            code_lines, comment_lines = self._count_lines(source)
            total_lines = code_lines + comment_lines
            density = comment_lines / total_lines if total_lines > 0 else 0
            issues = []
            if density < self.min_density:
                issues.append({
                    "line": 1,
                    "column": 0,
                    "message": (
                        f"Low comment density: {density:.1%} "
                        f"(minimum: {self.min_density:.1%})"
                    ),
                    "code": "LOW_COMMENT_DENSITY",
                    "severity": "high",
                    "hint": "Consider adding more comments to improve documentation"
                })
            elif density > self.max_density:
                issues.append({
                    "line": 1, 
                    "column": 0,
                    "message": (
                        f"High comment density: {density:.1%} "
                        f"(maximum: {self.max_density:.1%})"
                    ),
                    "code": "HIGH_COMMENT_DENSITY",
                    "severity": "high",
                    "hint": "Consider if some comments could be removed or simplified"
                })
            
            return {
                "results": issues,
                "summary": {
                    "issues_found": len(issues),
                    "status": "completed",
                    "metrics": {
                        "code_lines": code_lines,
                        "comment_lines": comment_lines,
                        "total_lines": total_lines,
                        "comment_density": density
                    }
                }
            }
            
        except SyntaxError as exc:
            return {
                "results": [{
                    "line": exc.lineno or 1,
                    "column": exc.offset or 0,
                    "message": f"Syntax error: {exc}",
                    "code": "SYNTAX_ERROR",
                    "severity": "high",
                    "hint": "Fix syntax errors before analyzing comment density"
                }],
                "summary": {
                    "issues_found": 1,
                    "status": "partial",
                    "error": str(exc)
                }
            }
        except Exception as exc:
            return {
                "results": [{
                    "line": 1,
                    "column": 0, 
                    "message": f"Analysis error: {exc}",
                    "code": "ANALYSIS_ERROR",
                    "severity": "high",
                    "hint": "Check the source code for issues"
                }],
                "summary": {
                    "issues_found": 1,
                    "status": "error",
                    "error": str(exc)
                }
            }