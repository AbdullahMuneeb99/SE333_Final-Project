"""MCP Server for JaCoCo Test Generator."""

import json
from pathlib import Path
from typing import Any

try:
    from mcp import Server, Tool
    from mcp.types import TextContent
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

from .coverage_parser import JaCoCoParser, CoverageReport
from .test_generator import JavaTestGenerator, GeneratedTest
from .git_tools import GitTools


def create_server():
    """Create and configure the MCP server."""
    if not HAS_MCP:
        raise ImportError("MCP library not installed. Install with: pip install mcp")
    
    server = Server("jacoco-test-generator")
    
    @server.list_tools()
    def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="parse_jacoco_report",
                description="Parse a JaCoCo XML coverage report and extract coverage gaps",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "report_path": {
                            "type": "string",
                            "description": "Path to the JaCoCo XML report file"
                        }
                    },
                    "required": ["report_path"]
                }
            ),
            Tool(
                name="generate_tests",
                description="Generate Java tests to cover uncovered code paths",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "report_path": {
                            "type": "string",
                            "description": "Path to the JaCoCo XML report file"
                        },
                        "max_tests_per_gap": {
                            "type": "integer",
                            "description": "Maximum number of tests to generate per coverage gap",
                            "default": 3
                        }
                    },
                    "required": ["report_path"]
                }
            ),
            Tool(
                name="get_coverage_summary",
                description="Get a summary of coverage and top uncovered areas",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "report_path": {
                            "type": "string",
                            "description": "Path to the JaCoCo XML report file"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top gaps to return",
                            "default": 10
                        }
                    },
                    "required": ["report_path"]
                }
            ),
            Tool(
                name="git_status",
                description="Check git repository status: clean status, staged changes, conflicts",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Path to git repository",
                            "default": "."
                        }
                    }
                }
            ),
            Tool(
                name="git_add_all",
                description="Stage all changes with intelligent filtering (excludes build artifacts)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Path to git repository",
                            "default": "."
                        }
                    }
                }
            ),
            Tool(
                name="git_commit",
                description="Create commit with standardized message including coverage statistics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Path to git repository",
                            "default": "."
                        },
                        "message": {
                            "type": "string",
                            "description": "Commit message"
                        },
                        "coverage_stats": {
                            "type": "object",
                            "description": "Coverage metrics (line_coverage, branch_coverage, tests_generated)"
                        }
                    },
                    "required": ["message"]
                }
            ),
            Tool(
                name="git_push",
                description="Push to remote with upstream configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Path to git repository",
                            "default": "."
                        },
                        "remote": {
                            "type": "string",
                            "description": "Remote name",
                            "default": "origin"
                        },
                        "branch": {
                            "type": "string",
                            "description": "Branch to push (default: current branch)"
                        }
                    }
                }
            ),
            Tool(
                name="git_pull_request",
                description="Create pull request (requires gh CLI installed and authenticated)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {
                            "type": "string",
                            "description": "Path to git repository",
                            "default": "."
                        },
                        "base": {
                            "type": "string",
                            "description": "Base branch for PR",
                            "default": "main"
                        },
                        "title": {
                            "type": "string",
                            "description": "PR title"
                        },
                        "body": {
                            "type": "string",
                            "description": "PR description"
                        },
                        "coverage_stats": {
                            "type": "object",
                            "description": "Coverage metrics to include in PR"
                        }
                    },
                    "required": ["title"]
                }
            )
        ]
    
    @server.call_tool()
    def call_tool(name: str, arguments: dict) -> Any:
        """Handle tool calls."""
        try:
            if name == "parse_jacoco_report":
                return handle_parse_report(arguments["report_path"])
            elif name == "generate_tests":
                return handle_generate_tests(
                    arguments["report_path"],
                    arguments.get("max_tests_per_gap", 3)
                )
            elif name == "get_coverage_summary":
                return handle_coverage_summary(
                    arguments["report_path"],
                    arguments.get("top_n", 10)
                )
            elif name == "git_status":
                return handle_git_status(arguments.get("repo_path", "."))
            elif name == "git_add_all":
                return handle_git_add_all(arguments.get("repo_path", "."))
            elif name == "git_commit":
                return handle_git_commit(
                    arguments.get("repo_path", "."),
                    arguments["message"],
                    arguments.get("coverage_stats")
                )
            elif name == "git_push":
                return handle_git_push(
                    arguments.get("repo_path", "."),
                    arguments.get("remote", "origin"),
                    arguments.get("branch")
                )
            elif name == "git_pull_request":
                return handle_git_pull_request(
                    arguments.get("repo_path", "."),
                    arguments.get("base", "main"),
                    arguments["title"],
                    arguments.get("body", ""),
                    arguments.get("coverage_stats")
                )
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}
    
    return server


def handle_parse_report(report_path: str) -> dict:
    """Handle parse_jacoco_report tool call."""
    try:
        report = JaCoCoParser.parse_report(report_path)
        
        gaps_data = []
        for gap in report.gaps[:20]:  # Return top 20 gaps
            gaps_data.append({
                "class_name": gap.class_name,
                "method_name": gap.method_name,
                "line_coverage": round(gap.line_coverage, 2),
                "branch_coverage": round(gap.branch_coverage, 2),
                "uncovered_lines": gap.uncovered_lines[:5]  # First 5 uncovered lines
            })
        
        return {
            "success": True,
            "total_line_coverage": round(report.total_line_coverage, 2),
            "total_branch_coverage": round(report.total_branch_coverage, 2),
            "total_gaps": len(report.gaps),
            "top_gaps": gaps_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_generate_tests(report_path: str, max_tests_per_gap: int) -> dict:
    """Handle generate_tests tool call."""
    try:
        # Parse report
        report = JaCoCoParser.parse_report(report_path)
        
        # Generate tests
        tests = JavaTestGenerator.generate_tests(report.gaps, max_tests_per_gap)
        
        tests_data = []
        for test in tests[:10]:  # Return first 10 generated tests
            tests_data.append({
                "test_class": test.class_name,
                "test_method": test.test_method_name,
                "target_class": test.target_class,
                "target_method": test.target_method,
                "test_code": test.test_code
            })
        
        return {
            "success": True,
            "tests_generated": len(tests),
            "tests": tests_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_coverage_summary(report_path: str, top_n: int) -> dict:
    """Handle get_coverage_summary tool call."""
    try:
        report = JaCoCoParser.parse_report(report_path)
        
        gaps_data = []
        for gap in report.gaps[:top_n]:
            gaps_data.append({
                "class_name": gap.class_name,
                "method_name": gap.method_name,
                "line_coverage_percent": round(gap.line_coverage, 2),
                "branch_coverage_percent": round(gap.branch_coverage, 2)
            })
        
        return {
            "success": True,
            "summary": {
                "total_line_coverage": round(report.total_line_coverage, 2),
                "total_branch_coverage": round(report.total_branch_coverage, 2),
                "coverage_gap": round(100 - report.total_line_coverage, 2),
                "total_methods_with_gaps": len(report.gaps)
            },
            "top_uncovered_methods": gaps_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_git_status(repo_path: str) -> dict:
    """Handle git_status tool call."""
    try:
        status = GitTools.git_status(repo_path)
        return {
            "success": True,
            "is_clean": status.is_clean,
            "current_branch": status.current_branch,
            "staged_changes": status.staged_changes,
            "unstaged_changes": status.unstaged_changes,
            "untracked_files": status.untracked_files,
            "conflicts": status.conflicts,
            "commits_ahead": status.commits_ahead
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_git_add_all(repo_path: str) -> dict:
    """Handle git_add_all tool call."""
    try:
        return GitTools.git_add_all(repo_path)
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_git_commit(repo_path: str, message: str, coverage_stats: dict = None) -> dict:
    """Handle git_commit tool call."""
    try:
        result = GitTools.git_commit(repo_path, message, coverage_stats)
        return {
            "success": result.success,
            "commit_hash": result.commit_hash,
            "message": result.message
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_git_push(repo_path: str, remote: str = "origin", branch: str = None) -> dict:
    """Handle git_push tool call."""
    try:
        return GitTools.git_push(repo_path, remote, branch)
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_git_pull_request(
    repo_path: str, 
    base: str = "main", 
    title: str = "", 
    body: str = "", 
    coverage_stats: dict = None
) -> dict:
    """Handle git_pull_request tool call."""
    try:
        result = GitTools.git_pull_request(repo_path, base, title, body, coverage_stats)
        return {
            "success": result.success,
            "url": result.url,
            "number": result.number,
            "message": result.message
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Entry point for the MCP server."""
    server = create_server()
    
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def run():
        async with stdio_server(server) as streams:
            await server.wait_for_shutdown()
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
