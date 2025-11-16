"""Git operations for automated test generation workflows."""

import os
import subprocess
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GitStatus:
    """Represents the status of a git repository."""
    is_clean: bool
    staged_changes: List[str]
    unstaged_changes: List[str]
    untracked_files: List[str]
    conflicts: List[str]
    current_branch: str
    commits_ahead: int


@dataclass
class GitCommitResult:
    """Result of a git commit operation."""
    success: bool
    commit_hash: Optional[str]
    message: str


@dataclass
class PullRequestResult:
    """Result of creating a pull request."""
    success: bool
    url: Optional[str]
    number: Optional[int]
    message: str


class GitTools:
    """Git operations for test generation workflows."""
    
    @staticmethod
    def git_status(repo_path: str = ".") -> GitStatus:
        """
        Get detailed git status of repository.
        
        Args:
            repo_path: Path to git repository
            
        Returns:
            GitStatus with clean status, staged changes, conflicts
            
        Raises:
            RuntimeError: If not a git repository
        """
        try:
            # Check if it's a git repo
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f"{repo_path} is not a git repository")
        
        # Get current branch
        try:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()
        except subprocess.CalledProcessError:
            current_branch = "unknown"
        
        # Get commits ahead of origin
        commits_ahead = 0
        try:
            ahead_result = subprocess.run(
                ["git", "rev-list", "--count", f"origin/{current_branch}..HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if ahead_result.returncode == 0:
                commits_ahead = int(ahead_result.stdout.strip() or 0)
        except (subprocess.CalledProcessError, ValueError):
            pass
        
        # Get status in porcelain format
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        staged_changes = []
        unstaged_changes = []
        untracked_files = []
        conflicts = []
        
        for line in status_result.stdout.strip().split("\n"):
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            # Staged (first character)
            if status_code[0] != " ":
                staged_changes.append(filename)
            
            # Unstaged (second character)
            if status_code[1] != " ":
                unstaged_changes.append(filename)
            
            # Untracked
            if status_code == "??":
                untracked_files.append(filename)
            
            # Conflicts
            if status_code in ["DD", "AU", "UD", "UA", "DD", "AA", "UU"]:
                conflicts.append(filename)
        
        is_clean = (
            not staged_changes and 
            not unstaged_changes and 
            not conflicts and
            commits_ahead == 0
        )
        
        return GitStatus(
            is_clean=is_clean,
            staged_changes=staged_changes,
            unstaged_changes=unstaged_changes,
            untracked_files=untracked_files,
            conflicts=conflicts,
            current_branch=current_branch,
            commits_ahead=commits_ahead
        )
    
    @staticmethod
    def git_add_all(
        repo_path: str = ".",
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Stage all changes with intelligent filtering.
        Excludes build artifacts and temporary files.
        
        Args:
            repo_path: Path to git repository
            exclude_patterns: Patterns to exclude (default: build artifacts)
            
        Returns:
            Dict with success status and staged files count
        """
        if exclude_patterns is None:
            exclude_patterns = [
                "*.class",
                "*.jar",
                "target/",
                "build/",
                "dist/",
                "__pycache__/",
                "*.pyc",
                ".pytest_cache/",
                ".venv/",
                "node_modules/",
                ".coverage",
                "*.egg-info/"
            ]
        
        try:
            # Get current status first
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files_to_add = []
            for line in status_result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                filename = line[3:]
                
                # Skip if matches exclude patterns
                skip = False
                for pattern in exclude_patterns:
                    if pattern.endswith("/"):
                        if filename.startswith(pattern):
                            skip = True
                            break
                    elif pattern.startswith("*"):
                        if filename.endswith(pattern[1:]):
                            skip = True
                            break
                    elif pattern in filename:
                        skip = True
                        break
                
                if not skip:
                    files_to_add.append(filename)
            
            # Add files
            if files_to_add:
                for filename in files_to_add:
                    subprocess.run(
                        ["git", "add", filename],
                        cwd=repo_path,
                        check=True,
                        capture_output=True
                    )
            
            return {
                "success": True,
                "files_staged": len(files_to_add),
                "staged_files": files_to_add,
                "message": f"Staged {len(files_to_add)} files"
            }
        
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": f"Failed to stage changes: {e.stderr.decode()}"
            }
    
    @staticmethod
    def git_commit(
        repo_path: str = ".",
        message: str = "",
        coverage_stats: Optional[Dict[str, float]] = None
    ) -> GitCommitResult:
        """
        Automated commit with standardized message.
        Includes coverage statistics in commit message.
        
        Args:
            repo_path: Path to git repository
            message: Commit message
            coverage_stats: Optional dict with coverage metrics
                           (e.g., {"line_coverage": 75.5, "branch_coverage": 60.0})
            
        Returns:
            GitCommitResult with success status and commit hash
        """
        try:
            # Build commit message
            full_message = message
            
            if coverage_stats:
                stats_lines = "\n\nCoverage Update:"
                if "line_coverage" in coverage_stats:
                    stats_lines += f"\n- Line Coverage: {coverage_stats['line_coverage']:.2f}%"
                if "branch_coverage" in coverage_stats:
                    stats_lines += f"\n- Branch Coverage: {coverage_stats['branch_coverage']:.2f}%"
                if "tests_generated" in coverage_stats:
                    stats_lines += f"\n- Tests Generated: {coverage_stats['tests_generated']}"
                if "coverage_gap" in coverage_stats:
                    stats_lines += f"\n- Coverage Gap: {coverage_stats['coverage_gap']:.2f}%"
                
                full_message += stats_lines
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", full_message],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit_hash = hash_result.stdout.strip()[:7]
                
                return GitCommitResult(
                    success=True,
                    commit_hash=commit_hash,
                    message=f"Committed with hash {commit_hash}"
                )
            else:
                return GitCommitResult(
                    success=False,
                    commit_hash=None,
                    message=f"Commit failed: {result.stderr.strip()}"
                )
        
        except Exception as e:
            return GitCommitResult(
                success=False,
                commit_hash=None,
                message=f"Error during commit: {str(e)}"
            )
    
    @staticmethod
    def git_push(
        repo_path: str = ".",
        remote: str = "origin",
        branch: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Push to remote with upstream configuration.
        Handles authentication through existing credential helpers.
        
        Args:
            repo_path: Path to git repository
            remote: Remote name (default: origin)
            branch: Branch to push (default: current branch)
            
        Returns:
            Dict with success status and push details
        """
        try:
            # Get current branch if not specified
            if branch is None:
                branch_result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                branch = branch_result.stdout.strip()
            
            # Push with upstream configuration
            push_result = subprocess.run(
                ["git", "push", "-u", remote, branch],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if push_result.returncode == 0:
                return {
                    "success": True,
                    "remote": remote,
                    "branch": branch,
                    "message": f"Pushed to {remote}/{branch}"
                }
            else:
                # Check if already up to date
                if "everything up-to-date" in push_result.stderr.lower():
                    return {
                        "success": True,
                        "remote": remote,
                        "branch": branch,
                        "message": f"Everything up-to-date on {remote}/{branch}"
                    }
                
                return {
                    "success": False,
                    "message": f"Push failed: {push_result.stderr.strip()}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Error during push: {str(e)}"
            }
    
    @staticmethod
    def git_pull_request(
        repo_path: str = ".",
        base: str = "main",
        title: str = "",
        body: str = "",
        coverage_stats: Optional[Dict[str, float]] = None
    ) -> PullRequestResult:
        """
        Create a pull request against specified base branch.
        Uses gh CLI (GitHub CLI) for automation.
        Requires: gh cli installed and authenticated
        
        Args:
            repo_path: Path to git repository
            base: Base branch for PR (default: main)
            title: PR title
            body: PR description
            coverage_stats: Optional coverage metrics to include in body
            
        Returns:
            PullRequestResult with URL and number
        """
        try:
            # Check if gh is installed
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            return PullRequestResult(
                success=False,
                url=None,
                number=None,
                message="GitHub CLI (gh) not installed or not authenticated. "
                        "Install with: brew install gh (macOS) or visit https://cli.github.com"
            )
        
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()
            
            if current_branch == base:
                return PullRequestResult(
                    success=False,
                    url=None,
                    number=None,
                    message=f"Cannot create PR: already on base branch {base}"
                )
            
            # Build PR body
            full_body = body
            if coverage_stats:
                stats_section = "\n## Coverage Improvements\n"
                if "line_coverage" in coverage_stats:
                    stats_section += f"- Line Coverage: {coverage_stats['line_coverage']:.2f}%\n"
                if "branch_coverage" in coverage_stats:
                    stats_section += f"- Branch Coverage: {coverage_stats['branch_coverage']:.2f}%\n"
                if "tests_generated" in coverage_stats:
                    stats_section += f"- Tests Generated: {coverage_stats['tests_generated']}\n"
                if "coverage_improvement" in coverage_stats:
                    stats_section += f"- Coverage Improvement: +{coverage_stats['coverage_improvement']:.2f}%\n"
                
                full_body += stats_section
            
            # Create PR
            pr_result = subprocess.run(
                ["gh", "pr", "create", "--base", base, "--title", title, "--body", full_body],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if pr_result.returncode == 0:
                # Extract PR URL
                pr_url = pr_result.stdout.strip()
                
                # Extract PR number from URL
                pr_number = None
                if "/pull/" in pr_url:
                    pr_number = int(pr_url.split("/pull/")[1])
                
                return PullRequestResult(
                    success=True,
                    url=pr_url,
                    number=pr_number,
                    message=f"PR created: {pr_url}"
                )
            else:
                return PullRequestResult(
                    success=False,
                    url=None,
                    number=None,
                    message=f"PR creation failed: {pr_result.stderr.strip()}"
                )
        
        except Exception as e:
            return PullRequestResult(
                success=False,
                url=None,
                number=None,
                message=f"Error creating PR: {str(e)}"
            )
