"""
Git Monitor - Git Repository Monitoring for Audit  
Pure GitPython implementation - NO external conflicts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class GitMonitor:
    """
    Git repository monitoring for code change detection
    Monitors commits, file changes, and repository health
    """
    
    def __init__(self, repo_path: str = None):
        self.logger = logging.getLogger(__name__)
        self.repo_path = repo_path or "/app"  # Default to current directory
        self.repo = None
        self._initialize_repo()
    
    def _initialize_repo(self):
        """Initialize Git repository"""
        try:
            import git
            
            # Find the git repository
            if os.path.exists(os.path.join(self.repo_path, '.git')):
                self.repo = git.Repo(self.repo_path)
                self.logger.info(f"Git repository initialized: {self.repo_path}")
            else:
                # Try to find git repo in parent directories
                current_path = self.repo_path
                while current_path != '/':
                    if os.path.exists(os.path.join(current_path, '.git')):
                        self.repo = git.Repo(current_path)
                        self.repo_path = current_path
                        self.logger.info(f"Git repository found: {current_path}")
                        break
                    current_path = os.path.dirname(current_path)
                
                if not self.repo:
                    self.logger.warning("No git repository found")
                    
        except ImportError:
            self.logger.error("GitPython not available")
            self.repo = None
        except Exception as e:
            self.logger.error(f"Failed to initialize git repository: {e}")
            self.repo = None
    
    async def get_recent_changes(self, hours: int = 24) -> List[Dict]:
        """
        Get recent git changes within specified hours
        """
        if not self.repo:
            return await self._get_changes_fallback(hours)
        
        try:
            # Calculate time threshold
            since_time = datetime.now() - timedelta(hours=hours)
            
            changes = []
            
            # Get recent commits
            commits = list(self.repo.iter_commits(since=since_time.isoformat()))
            
            for commit in commits:
                try:
                    # Get files changed in this commit
                    changed_files = []
                    
                    if commit.parents:  # Not the initial commit
                        # Compare with parent
                        parent = commit.parents[0]
                        diffs = parent.diff(commit)
                        
                        for diff in diffs:
                            if diff.a_path:  # File path exists
                                file_change = {
                                    "file_path": os.path.join(self.repo_path, diff.a_path),
                                    "change_type": diff.change_type,
                                    "relative_path": diff.a_path,
                                    "additions": diff.a_blob.size if diff.a_blob else 0,
                                    "deletions": diff.b_blob.size if diff.b_blob else 0
                                }
                                changed_files.append(file_change)
                    
                    # Create change record
                    change = {
                        "commit_hash": commit.hexsha,
                        "commit_message": commit.message.strip(),
                        "author": str(commit.author),
                        "author_email": commit.author.email,
                        "commit_date": commit.committed_datetime.isoformat(),
                        "changed_files": changed_files,
                        "files_count": len(changed_files)
                    }
                    
                    changes.append(change)
                    
                    # Also add individual file changes for analysis
                    for file_change in changed_files:
                        if file_change["file_path"].endswith('.py'):  # Only Python files
                            changes.append({
                                "file_path": file_change["file_path"],
                                "relative_path": file_change["relative_path"],
                                "change_type": file_change["change_type"],
                                "commit_hash": commit.hexsha,
                                "commit_message": commit.message.strip(),
                                "author": str(commit.author),
                                "commit_date": commit.committed_datetime.isoformat()
                            })
                
                except Exception as commit_error:
                    self.logger.error(f"Error processing commit {commit.hexsha}: {commit_error}")
                    continue
            
            self.logger.info(f"Found {len(changes)} recent changes in last {hours} hours")
            return changes
            
        except Exception as e:
            self.logger.error(f"Failed to get recent changes: {e}")
            return await self._get_changes_fallback(hours)
    
    async def _get_changes_fallback(self, hours: int) -> List[Dict]:
        """
        Fallback method using git commands directly
        """
        try:
            import subprocess
            import json
            
            # Calculate time threshold
            since_time = datetime.now() - timedelta(hours=hours)
            since_str = since_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Get recent commits using git log
            git_log_cmd = [
                "git", "log", 
                f"--since={since_str}",
                "--pretty=format:%H|%s|%an|%ae|%ci",
                "--name-only"
            ]
            
            result = subprocess.run(
                git_log_cmd, 
                cwd=self.repo_path,
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.error(f"Git log command failed: {result.stderr}")
                return []
            
            changes = []
            current_commit = None
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if '|' in line:  # Commit info line
                    parts = line.split('|')
                    if len(parts) >= 5:
                        current_commit = {
                            "commit_hash": parts[0],
                            "commit_message": parts[1],
                            "author": parts[2],
                            "author_email": parts[3],
                            "commit_date": parts[4],
                            "changed_files": []
                        }
                        changes.append(current_commit)
                
                elif current_commit and line.endswith('.py'):  # Python file
                    file_path = os.path.join(self.repo_path, line)
                    
                    file_change = {
                        "file_path": file_path,
                        "relative_path": line,
                        "change_type": "modified",  # We don't have detailed change type
                        "commit_hash": current_commit["commit_hash"],
                        "commit_message": current_commit["commit_message"],
                        "author": current_commit["author"],
                        "commit_date": current_commit["commit_date"]
                    }
                    
                    current_commit["changed_files"].append(file_change)
                    changes.append(file_change)  # Also add as individual change
            
            self.logger.info(f"Fallback git analysis found {len(changes)} changes")
            return changes
            
        except Exception as e:
            self.logger.error(f"Git fallback failed: {e}")
            return []
    
    async def get_repository_status(self) -> Dict:
        """
        Get current repository status and health
        """
        if not self.repo:
            return await self._get_status_fallback()
        
        try:
            status = {
                "repository_path": self.repo_path,
                "current_branch": str(self.repo.active_branch),
                "head_commit": self.repo.head.commit.hexsha,
                "head_commit_message": self.repo.head.commit.message.strip(),
                "head_commit_date": self.repo.head.commit.committed_datetime.isoformat(),
                "head_author": str(self.repo.head.commit.author),
                "is_dirty": self.repo.is_dirty(),
                "untracked_files": self.repo.untracked_files,
                "modified_files": [item.a_path for item in self.repo.index.diff(None)],
                "staged_files": [item.a_path for item in self.repo.index.diff("HEAD")],
                "timestamp": datetime.now().isoformat()
            }
            
            # Get remote information
            try:
                origin = self.repo.remotes.origin
                status["remote_url"] = list(origin.urls)[0] if origin.urls else None
            except Exception:
                status["remote_url"] = None
            
            # Get total commit count
            try:
                status["total_commits"] = len(list(self.repo.iter_commits()))
            except Exception:
                status["total_commits"] = "unknown"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get repository status: {e}")
            return await self._get_status_fallback()
    
    async def _get_status_fallback(self) -> Dict:
        """
        Fallback repository status using git commands
        """
        try:
            import subprocess
            
            status = {
                "repository_path": self.repo_path,
                "timestamp": datetime.now().isoformat()
            }
            
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if branch_result.returncode == 0:
                status["current_branch"] = branch_result.stdout.strip()
            
            # Get head commit
            head_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if head_result.returncode == 0:
                status["head_commit"] = head_result.stdout.strip()
            
            # Get repository status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.returncode == 0:
                status_lines = status_result.stdout.strip().split('\n')
                status["is_dirty"] = len(status_lines) > 0 and status_lines[0] != ''
                status["modified_files"] = [
                    line[3:] for line in status_lines 
                    if line.startswith(' M') or line.startswith('MM')
                ]
                status["untracked_files"] = [
                    line[3:] for line in status_lines 
                    if line.startswith('??')
                ]
                status["staged_files"] = [
                    line[3:] for line in status_lines 
                    if line.startswith('M ') or line.startswith('A ')
                ]
            
            return status
            
        except Exception as e:
            self.logger.error(f"Git status fallback failed: {e}")
            return {
                "repository_path": self.repo_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_commit_statistics(self, days: int = 7) -> Dict:
        """
        Get commit statistics for the specified period
        """
        if not self.repo:
            return await self._get_stats_fallback(days)
        
        try:
            # Calculate time threshold
            since_time = datetime.now() - timedelta(days=days)
            
            commits = list(self.repo.iter_commits(since=since_time.isoformat()))
            
            # Statistics
            stats = {
                "period_days": days,
                "total_commits": len(commits),
                "authors": {},
                "files_changed": {},
                "commit_messages": [],
                "hourly_distribution": [0] * 24,
                "daily_distribution": [0] * 7
            }
            
            for commit in commits:
                # Author statistics
                author = str(commit.author)
                if author not in stats["authors"]:
                    stats["authors"][author] = 0
                stats["authors"][author] += 1
                
                # Commit message
                stats["commit_messages"].append({
                    "hash": commit.hexsha[:8],
                    "message": commit.message.strip(),
                    "author": author,
                    "date": commit.committed_datetime.isoformat()
                })
                
                # Time distribution
                commit_hour = commit.committed_datetime.hour
                commit_weekday = commit.committed_datetime.weekday()
                stats["hourly_distribution"][commit_hour] += 1
                stats["daily_distribution"][commit_weekday] += 1
                
                # File changes
                if commit.parents:
                    parent = commit.parents[0]
                    diffs = parent.diff(commit)
                    
                    for diff in diffs:
                        if diff.a_path:
                            file_path = diff.a_path
                            if file_path not in stats["files_changed"]:
                                stats["files_changed"][file_path] = 0
                            stats["files_changed"][file_path] += 1
            
            # Sort by frequency
            stats["top_authors"] = sorted(
                stats["authors"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            stats["most_changed_files"] = sorted(
                stats["files_changed"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            stats["timestamp"] = datetime.now().isoformat()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get commit statistics: {e}")
            return await self._get_stats_fallback(days)
    
    async def _get_stats_fallback(self, days: int) -> Dict:
        """
        Fallback commit statistics using git commands
        """
        try:
            import subprocess
            
            # Calculate time threshold
            since_time = datetime.now() - timedelta(days=days)
            since_str = since_time.strftime("%Y-%m-%d")
            
            # Get commit count
            count_result = subprocess.run(
                ["git", "rev-list", "--count", f"--since={since_str}", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            total_commits = 0
            if count_result.returncode == 0:
                total_commits = int(count_result.stdout.strip())
            
            # Get author stats
            author_result = subprocess.run(
                ["git", "shortlog", "-sn", f"--since={since_str}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            authors = {}
            if author_result.returncode == 0:
                for line in author_result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            count = int(parts[0])
                            author = parts[1]
                            authors[author] = count
            
            return {
                "period_days": days,
                "total_commits": total_commits,
                "authors": authors,
                "top_authors": list(authors.items())[:5],
                "timestamp": datetime.now().isoformat(),
                "method": "fallback"
            }
            
        except Exception as e:
            self.logger.error(f"Git statistics fallback failed: {e}")
            return {
                "error": str(e),
                "period_days": days,
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_repository_health(self) -> Dict:
        """
        Check repository health and integrity
        """
        health_checks = {
            "repository_exists": os.path.exists(os.path.join(self.repo_path, '.git')),
            "git_available": False,
            "repository_accessible": False,
            "recent_activity": False,
            "branch_status": "unknown",
            "issues": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check if git is available
            import subprocess
            git_version = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            health_checks["git_available"] = git_version.returncode == 0
            
            if not health_checks["git_available"]:
                health_checks["issues"].append("Git command not available")
                return health_checks
            
            # Check repository accessibility
            if self.repo:
                health_checks["repository_accessible"] = True
                
                # Check for recent activity (last 7 days)
                recent_changes = await self.get_recent_changes(hours=24 * 7)
                health_checks["recent_activity"] = len(recent_changes) > 0
                
                # Check branch status
                try:
                    status = await self.get_repository_status()
                    health_checks["branch_status"] = status.get("current_branch", "unknown")
                    
                    if status.get("is_dirty", False):
                        health_checks["issues"].append("Repository has uncommitted changes")
                    
                    if status.get("untracked_files"):
                        health_checks["issues"].append(f"Repository has {len(status['untracked_files'])} untracked files")
                        
                except Exception as status_error:
                    health_checks["issues"].append(f"Could not get repository status: {status_error}")
            
            else:
                health_checks["issues"].append("Repository not accessible via GitPython")
            
            # Overall health score
            health_score = 1.0
            if not health_checks["repository_exists"]:
                health_score -= 0.5
            if not health_checks["git_available"]:
                health_score -= 0.3
            if not health_checks["repository_accessible"]:
                health_score -= 0.2
            
            health_checks["health_score"] = max(0.0, health_score)
            health_checks["health_status"] = (
                "healthy" if health_score >= 0.8 else
                "warning" if health_score >= 0.5 else
                "critical"
            )
            
        except Exception as e:
            self.logger.error(f"Repository health check failed: {e}")
            health_checks["issues"].append(f"Health check error: {str(e)}")
            health_checks["health_score"] = 0.0
            health_checks["health_status"] = "error"
        
        return health_checks
    
    async def get_file_change_details(self, file_path: str, commits_limit: int = 5) -> Dict:
        """
        Get detailed change history for a specific file
        """
        if not self.repo:
            return {"error": "Repository not available"}
        
        try:
            # Get commits that modified this file
            relative_path = os.path.relpath(file_path, self.repo_path)
            commits = list(self.repo.iter_commits(paths=relative_path, max_count=commits_limit))
            
            file_history = {
                "file_path": file_path,
                "relative_path": relative_path,
                "commits_analyzed": len(commits),
                "changes": []
            }
            
            for commit in commits:
                change_info = {
                    "commit_hash": commit.hexsha,
                    "commit_message": commit.message.strip(),
                    "author": str(commit.author),
                    "author_email": commit.author.email,
                    "commit_date": commit.committed_datetime.isoformat(),
                    "changes": []
                }
                
                # Get diff for this file in this commit
                if commit.parents:
                    parent = commit.parents[0]
                    diffs = parent.diff(commit, paths=relative_path)
                    
                    for diff in diffs:
                        if diff.a_path == relative_path or diff.b_path == relative_path:
                            change_detail = {
                                "change_type": diff.change_type,
                                "insertions": 0,
                                "deletions": 0
                            }
                            
                            # Count lines changed
                            if diff.diff:
                                diff_text = diff.diff.decode('utf-8', errors='ignore')
                                lines = diff_text.split('\n')
                                
                                for line in lines:
                                    if line.startswith('+') and not line.startswith('+++'):
                                        change_detail["insertions"] += 1
                                    elif line.startswith('-') and not line.startswith('---'):
                                        change_detail["deletions"] += 1
                            
                            change_info["changes"].append(change_detail)
                
                file_history["changes"].append(change_info)
            
            file_history["timestamp"] = datetime.now().isoformat()
            return file_history
            
        except Exception as e:
            self.logger.error(f"Failed to get file change details for {file_path}: {e}")
            return {
                "file_path": file_path,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }