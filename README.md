# JaCoCo Test Generator MCP Tool

A Python MCP tool that automatically generates Java tests from JaCoCo coverage reports and automates Git workflows.

## What It Does

1. Parses JaCoCo XML coverage reports
2. Identifies methods and lines with incomplete coverage
3. Generates JUnit 5 test templates for uncovered code
4. Automates Git operations: commit, push, create pull requests

## Installation

```bash
pip install -e .
```

This installs: mcp[cli], fastmcp, httpx, lxml, requests

## Quick Start

Run the demo to see it in action:
```bash
python demo.py
```

## MCP Tools Available

### Coverage Analysis Tools
- **parse_jacoco_report**: Analyzes a JaCoCo report and extracts coverage gaps with metrics
- **generate_tests**: Generates Java test templates for uncovered code paths
- **get_coverage_summary**: Returns coverage percentages and top uncovered methods

### Git Automation Tools
- **git_status**: Checks repository status (clean, staged changes, conflicts)
- **git_add_all**: Stages changes with intelligent filtering
- **git_commit**: Creates commits with coverage statistics appended
- **git_push**: Pushes to remote with upstream configuration
- **git_pull_request**: Creates pull requests via GitHub

## Typical Workflow

For a Java project:

1. Generate JaCoCo report in your Java project:
```bash
mvn clean jacoco:prepare-agent test jacoco:report
```

2. Use the tool to analyze coverage:
```bash
python demo.py
# Change report path to the name of your JaCoCo report after putting it in the project folder
```

3. Review generated test templates and implement test logic

4. Run tests and regenerate JaCoCo report

5. Repeat until coverage reaches your target

## Key Features

- Parses JaCoCo XML format and extracts coverage gaps
- Identifies uncovered lines by line number
- Generates multiple test scenarios per uncovered method
- JUnit 5 compatible test templates with TODO comments
- Intelligent file filtering for Git operations

## Architecture

The tool consists of:

1. **Coverage Parser**: Reads JaCoCo XML, extracts coverage gaps, calculates metrics
2. **Test Generator**: Creates Java test method templates with multiple scenarios
3. **Git Tools**: Manages repository operations with intelligent filtering
4. **MCP Server**: Exposes all tools to Claude and other MCP clients

## Testing

All features have been tested:
- XML parsing with sample JaCoCo report
- Coverage gap detection and sorting
- Test generation and file formatting
- Git operations (status, add, commit, push)
- MCP server tool registration and handlers

## Support

Run `python demo.py` to see working examples.

For specific use cases:
- Coverage analysis: See example_jacoco_report.xml and demo.py
- Test generation: See test_generator.py and demo.py output
- Git tools: See git_tools.py
- MCP integration: See server.py
