"""
Code Analyzer - Static Code Analysis for Audit
NO external dependencies - Pure Python analysis
"""

import ast
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
import os
import subprocess

class CodeAnalyzer:
    """
    Static code analysis for financial compliance and security
    Analyzes Python files for:
    - Compliance violations (prescriptive language)
    - Security issues (hardcoded secrets, SQL injection)
    - Performance issues (infinite loops, resource leaks)
    - Code quality issues
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Compliance patterns
        self.compliance_patterns = {
            "prescriptive_language": [
                r"\b(buy now|sell now|guaranteed|risk-free|sure thing)\b",
                r"\b(definitely|certainly|absolutely) (buy|sell|invest)\b",
                r"\b(can\'t lose|cannot lose|guaranteed profit)\b"
            ],
            "financial_advice": [
                r"\b(you should|you must) (buy|sell|invest)\b",
                r"\b(recommendation|advice): (buy|sell)\b",
                r"\b(strong buy|strong sell)\b"
            ],
            "misleading_claims": [
                r"\b(100% accurate|never wrong|always profitable)\b",
                r"\b(get rich quick|easy money|instant profit)\b"
            ]
        }
        
        # Security patterns
        self.security_patterns = {
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
                r"token\s*=\s*['\"][^'\"]+['\"]"
            ],
            "sql_injection": [
                r"execute\s*\(\s*['\"].*%s.*['\"]",
                r"query\s*=\s*['\"].*\+.*['\"]",
                r"SELECT.*\+.*FROM"
            ],
            "command_injection": [
                r"os\.system\s*\(\s*.*\+",
                r"subprocess\.(call|run|Popen)\s*\(\s*.*\+"
            ]
        }
        
        # Performance patterns
        self.performance_patterns = {
            "infinite_loops": [
                r"while\s+True\s*:",
                r"for.*in.*while\s+True"
            ],
            "resource_leaks": [
                r"open\s*\([^)]*\)(?!\s*with)",
                r"connect\s*\([^)]*\)(?!\s*with)"
            ],
            "inefficient_patterns": [
                r"for.*in.*range\(len\(",
                r"time\.sleep\(0\)"
            ]
        }
        
        self.logger.info("CodeAnalyzer initialized")
    
    async def analyze_change(self, change: Dict) -> Dict:
        """
        Analyze a single code change (file)
        """
        file_path = change.get("file_path")
        
        if not file_path:
            return {"error": "No file path provided"}
        
        # Only analyze Python files
        if not file_path.endswith('.py'):
            return {
                "file_path": file_path,
                "skipped": True,
                "reason": "Non-Python file",
                "risk_level": "none"
            }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "file_path": file_path,
                    "error": "File not found",
                    "risk_level": "unknown"
                }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Perform various analyses
            analysis_results = {
                "file_path": file_path,
                "file_size": len(content),
                "line_count": len(content.split('\n')),
                "timestamp": datetime.now().isoformat()
            }
            
            # Run all analysis checks
            compliance_issues = await self._check_compliance(content, file_path)
            security_issues = await self._check_security(content, file_path)
            performance_issues = await self._check_performance(content, file_path)
            quality_issues = await self._check_code_quality(content, file_path)
            ast_issues = await self._check_ast_structure(content, file_path)
            
            # Compile all issues
            all_issues = (
                compliance_issues + 
                security_issues + 
                performance_issues + 
                quality_issues + 
                ast_issues
            )
            
            analysis_results.update({
                "compliance_issues": compliance_issues,
                "security_issues": security_issues,
                "performance_issues": performance_issues,
                "quality_issues": quality_issues,
                "ast_issues": ast_issues,
                "total_issues": len(all_issues),
                "issues": all_issues
            })
            
            # Calculate risk level
            risk_level = self._calculate_risk_level(all_issues)
            analysis_results["risk_level"] = risk_level
            
            self.logger.info(f"Code analysis complete for {file_path}: {len(all_issues)} issues, risk={risk_level}")
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Code analysis failed for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "risk_level": "unknown"
            }
    
    async def _check_compliance(self, content: str, file_path: str) -> List[Dict]:
        """
        Check for financial compliance violations
        """
        issues = []
        content_lower = content.lower()
        
        for category, patterns in self.compliance_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content_lower, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    
                    issues.append({
                        "type": "compliance",
                        "category": category,
                        "severity": "critical" if category == "prescriptive_language" else "high",
                        "description": f"Compliance violation: {category}",
                        "matched_text": match.group(),
                        "line_number": line_number,
                        "pattern": pattern
                    })
        
        return issues
    
    async def _check_security(self, content: str, file_path: str) -> List[Dict]:
        """
        Check for security vulnerabilities
        """
        issues = []
        
        for category, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    
                    severity = "critical" if category == "hardcoded_secrets" else "high"
                    
                    issues.append({
                        "type": "security",
                        "category": category,
                        "severity": severity,
                        "description": f"Security issue: {category}",
                        "matched_text": match.group(),
                        "line_number": line_number,
                        "pattern": pattern
                    })
        
        return issues
    
    async def _check_performance(self, content: str, file_path: str) -> List[Dict]:
        """
        Check for performance issues
        """
        issues = []
        
        for category, patterns in self.performance_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    
                    severity = "high" if category == "infinite_loops" else "medium"
                    
                    issues.append({
                        "type": "performance",
                        "category": category,
                        "severity": severity,
                        "description": f"Performance issue: {category}",
                        "matched_text": match.group(),
                        "line_number": line_number,
                        "pattern": pattern
                    })
        
        return issues
    
    async def _check_code_quality(self, content: str, file_path: str) -> List[Dict]:
        """
        Check code quality issues
        """
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for very long lines
            if len(line) > 120:
                issues.append({
                    "type": "quality",
                    "category": "long_line",
                    "severity": "low",
                    "description": f"Line too long: {len(line)} characters",
                    "line_number": i,
                    "matched_text": line[:50] + "..." if len(line) > 50 else line
                })
            
            # Check for TODO/FIXME comments
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line_stripped, re.IGNORECASE):
                issues.append({
                    "type": "quality",
                    "category": "todo_comment",
                    "severity": "low",
                    "description": "TODO/FIXME comment found",
                    "line_number": i,
                    "matched_text": line_stripped
                })
            
            # Check for print statements (should use logging)
            if re.search(r'\bprint\s*\(', line_stripped):
                issues.append({
                    "type": "quality",
                    "category": "print_statement",
                    "severity": "low",
                    "description": "Print statement found - consider using logging",
                    "line_number": i,
                    "matched_text": line_stripped
                })
            
            # Check for broad exception catching
            if re.search(r'except\s*:', line_stripped):
                issues.append({
                    "type": "quality",
                    "category": "broad_exception",
                    "severity": "medium",
                    "description": "Broad exception catching",
                    "line_number": i,
                    "matched_text": line_stripped
                })
        
        return issues
    
    async def _check_ast_structure(self, content: str, file_path: str) -> List[Dict]:
        """
        Check AST structure for deeper code analysis
        """
        issues = []
        
        try:
            tree = ast.parse(content)
            
            # Analyze AST nodes
            for node in ast.walk(tree):
                # Check for eval/exec usage
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec']:
                        issues.append({
                            "type": "security",
                            "category": "dynamic_code_execution",
                            "severity": "critical",
                            "description": f"Use of {node.func.id}() is dangerous",
                            "line_number": node.lineno,
                            "matched_text": f"{node.func.id}()"
                        })
                
                # Check for global variable usage
                elif isinstance(node, ast.Global):
                    for name in node.names:
                        issues.append({
                            "type": "quality",
                            "category": "global_variable",
                            "severity": "medium",
                            "description": f"Global variable usage: {name}",
                            "line_number": node.lineno,
                            "matched_text": f"global {name}"
                        })
                
                # Check for complex functions (too many arguments)
                elif isinstance(node, ast.FunctionDef):
                    arg_count = len(node.args.args)
                    if arg_count > 6:
                        issues.append({
                            "type": "quality",
                            "category": "complex_function",
                            "severity": "medium",
                            "description": f"Function {node.name} has {arg_count} arguments",
                            "line_number": node.lineno,
                            "matched_text": f"def {node.name}(...)"
                        })
                
                # Check for nested complexity
                elif isinstance(node, ast.For) or isinstance(node, ast.While):
                    # Count nested loops
                    nested_loops = self._count_nested_structures(node)
                    if nested_loops > 2:
                        issues.append({
                            "type": "quality",
                            "category": "nested_complexity",
                            "severity": "medium",
                            "description": f"High nesting level: {nested_loops}",
                            "line_number": node.lineno,
                            "matched_text": "Nested loop structure"
                        })
        
        except SyntaxError as e:
            issues.append({
                "type": "syntax",
                "category": "syntax_error",
                "severity": "critical",
                "description": f"Syntax error: {str(e)}",
                "line_number": e.lineno if hasattr(e, 'lineno') else 0,
                "matched_text": str(e)
            })
        
        except Exception as e:
            self.logger.error(f"AST analysis failed for {file_path}: {e}")
            issues.append({
                "type": "analysis",
                "category": "ast_error",
                "severity": "medium",
                "description": f"AST analysis failed: {str(e)}",
                "line_number": 0,
                "matched_text": "AST analysis error"
            })
        
        return issues
    
    def _count_nested_structures(self, node) -> int:
        """Count nested loop/conditional structures"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While, ast.If)) and child != node:
                count += 1
        return count
    
    def _calculate_risk_level(self, issues: List[Dict]) -> str:
        """
        Calculate overall risk level based on issues
        """
        if not issues:
            return "low"
        
        critical_count = len([i for i in issues if i.get("severity") == "critical"])
        high_count = len([i for i in issues if i.get("severity") == "high"])
        medium_count = len([i for i in issues if i.get("severity") == "medium"])
        
        # Risk calculation
        if critical_count > 0:
            return "critical"
        elif high_count >= 3:
            return "critical"
        elif high_count >= 1:
            return "high"
        elif medium_count >= 5:
            return "high"
        elif medium_count >= 2:
            return "medium"
        else:
            return "low"
    
    async def analyze_directory(self, directory_path: str) -> Dict:
        """
        Analyze all Python files in a directory
        """
        if not os.path.exists(directory_path):
            return {"error": f"Directory not found: {directory_path}"}
        
        try:
            python_files = []
            
            # Find all Python files
            for root, dirs, files in os.walk(directory_path):
                # Skip hidden directories and __pycache__
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        python_files.append(file_path)
            
            if not python_files:
                return {
                    "directory": directory_path,
                    "message": "No Python files found",
                    "files_analyzed": 0
                }
            
            # Analyze each file
            file_analyses = []
            total_issues = []
            
            for file_path in python_files:
                change_data = {"file_path": file_path}
                analysis = await self.analyze_change(change_data)
                file_analyses.append(analysis)
                
                if "issues" in analysis:
                    total_issues.extend(analysis["issues"])
            
            # Summary statistics
            risk_levels = [analysis.get("risk_level", "unknown") for analysis in file_analyses]
            risk_distribution = {
                "critical": risk_levels.count("critical"),
                "high": risk_levels.count("high"),
                "medium": risk_levels.count("medium"),
                "low": risk_levels.count("low"),
                "unknown": risk_levels.count("unknown")
            }
            
            overall_risk = "low"
            if risk_distribution["critical"] > 0:
                overall_risk = "critical"
            elif risk_distribution["high"] > 0:
                overall_risk = "high"
            elif risk_distribution["medium"] > 0:
                overall_risk = "medium"
            
            return {
                "directory": directory_path,
                "files_analyzed": len(python_files),
                "file_analyses": file_analyses,
                "summary": {
                    "total_issues": len(total_issues),
                    "risk_distribution": risk_distribution,
                    "overall_risk": overall_risk,
                    "files_with_issues": len([a for a in file_analyses if a.get("total_issues", 0) > 0])
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Directory analysis failed for {directory_path}: {e}")
            return {
                "directory": directory_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_recent_changes(self, git_changes: List[Dict]) -> Dict:
        """
        Analyze multiple git changes
        """
        if not git_changes:
            return {
                "message": "No changes to analyze",
                "changes_analyzed": 0
            }
        
        try:
            change_analyses = []
            total_issues = []
            
            for change in git_changes:
                analysis = await self.analyze_change(change)
                change_analyses.append(analysis)
                
                if "issues" in analysis:
                    total_issues.extend(analysis["issues"])
            
            # Calculate summary
            risk_levels = [analysis.get("risk_level", "unknown") for analysis in change_analyses]
            risk_distribution = {
                "critical": risk_levels.count("critical"),
                "high": risk_levels.count("high"),
                "medium": risk_levels.count("medium"),
                "low": risk_levels.count("low"),
                "unknown": risk_levels.count("unknown")
            }
            
            overall_risk = "low"
            if risk_distribution["critical"] > 0:
                overall_risk = "critical"
            elif risk_distribution["high"] > 0:
                overall_risk = "high"
            elif risk_distribution["medium"] > 0:
                overall_risk = "medium"
            
            # Issue categorization
            issue_types = {}
            for issue in total_issues:
                issue_type = issue.get("type", "unknown")
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1
            
            return {
                "changes_analyzed": len(git_changes),
                "change_analyses": change_analyses,
                "summary": {
                    "total_issues": len(total_issues),
                    "risk_distribution": risk_distribution,
                    "overall_risk": overall_risk,
                    "issue_types": issue_types,
                    "files_with_issues": len([a for a in change_analyses if a.get("total_issues", 0) > 0])
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Recent changes analysis failed: {e}")
            return {
                "error": str(e),
                "changes_analyzed": len(git_changes),
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_compliance_report(self, analysis_results: Dict) -> Dict:
        """
        Generate a compliance-focused report
        """
        try:
            compliance_issues = []
            
            # Extract compliance issues from analysis
            if "change_analyses" in analysis_results:
                for analysis in analysis_results["change_analyses"]:
                    if "compliance_issues" in analysis:
                        for issue in analysis["compliance_issues"]:
                            issue["file_path"] = analysis.get("file_path")
                            compliance_issues.append(issue)
            
            # Categorize compliance issues
            compliance_categories = {}
            for issue in compliance_issues:
                category = issue.get("category", "unknown")
                if category not in compliance_categories:
                    compliance_categories[category] = []
                compliance_categories[category].append(issue)
            
            # Risk assessment
            critical_violations = len([i for i in compliance_issues if i.get("severity") == "critical"])
            high_violations = len([i for i in compliance_issues if i.get("severity") == "high"])
            
            compliance_score = 1.0
            if critical_violations > 0:
                compliance_score -= critical_violations * 0.3
            if high_violations > 0:
                compliance_score -= high_violations * 0.1
            
            compliance_score = max(0.0, compliance_score)
            
            return {
                "compliance_report": {
                    "total_violations": len(compliance_issues),
                    "critical_violations": critical_violations,
                    "high_violations": high_violations,
                    "compliance_score": compliance_score,
                    "compliance_level": "excellent" if compliance_score >= 0.9 else 
                                     "good" if compliance_score >= 0.7 else
                                     "acceptable" if compliance_score >= 0.5 else "poor",
                    "violations_by_category": compliance_categories,
                    "violations": compliance_issues
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Compliance report generation failed: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }