from typing import Dict, List, Any
import ast
import re
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
    
    def get_metadata(self) -> Dict[str, str]:
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
        
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                continue
            
            # Handle multi-line comments
            if in_multiline_comment:
                comment_lines += 1
                if multiline_comment_char in stripped_line:
                    # Check if this line ends the multi-line comment
                    if (stripped_line.endswith(multiline_comment_char) or 
                        stripped_line.count(multiline_comment_char) >= 2):
                        in_multiline_comment = False
                continue
            print(comment_lines)
            # Check for multi-line comment start (triple quotes)
            if stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                comment_lines += 1
                multiline_comment_char = '"""' if stripped_line.startswith('"""') else "'''"
                
                # Check if it's a one-line docstring or starts multi-line
                if (stripped_line.endswith(multiline_comment_char) and 
                    len(stripped_line) > 3 and 
                    stripped_line.count(multiline_comment_char) == 2):
                    # One-line docstring
                    in_multiline_comment = False
                else:
                    # Starts multi-line comment
                    in_multiline_comment = True
                continue
            
            # Check for comments (both full-line and inline)
            if '#' in stripped_line:
                # Split on '#' to separate code from comment
                parts = stripped_line.split('#', 1)
                code_part = parts[0].strip()
                comment_part = parts[1] if len(parts) > 1 else ""
                
                # If there's actual code before the comment, count it as a code line
                if code_part:
                    code_lines += 1
                
                # If there's a comment (even inline), count it as a comment line
                if comment_part:
                    comment_lines += 1
                elif not code_part:
                    # This handles the case of just '#' on a line
                    comment_lines += 1
            else:
                # No '#' found, this is a pure code line
                code_lines += 1
        
        return code_lines, comment_lines
    
    def analyze(self, source: str, filename: str) -> Dict[str, Any]:
        """Analyze comment density in source code"""
        try:
            # Try to parse AST to catch syntax errors
            ast.parse(source)
            
            # Count lines of code and comments
            code_lines, comment_lines = self._count_lines(source)
            
            # Calculate comment density
            total_lines = code_lines + comment_lines
            density = comment_lines / total_lines if total_lines > 0 else 0
            
            # Generate report
            issues = []
            if density < self.min_density:
                issues.append({
                    "line": 1,
                    "column": 0,
                    "message": f"Low comment density: {density:.1%} (minimum: {self.min_density:.1%})",
                    "code": "LOW_COMMENT_DENSITY",
                    "severity": "warning",
                    "hint": f"Consider adding more comments to improve documentation"
                })
            elif density > self.max_density:
                issues.append({
                    "line": 1, 
                    "column": 0,
                    "message": f"High comment density: {density:.1%} (maximum: {self.max_density:.1%})",
                    "code": "HIGH_COMMENT_DENSITY",
                    "severity": "info",
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