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

Or use the quick start example:
```bash
python quick_start.py
```

## Three Ways to Use

### 1. Command Line
```bash
python demo.py          # Full demonstration
python quick_start.py   # Quick example
```

### 2. Python Library
```python
from jacoco_test_generator.coverage_parser import JaCoCoParser
from jacoco_test_generator.test_generator import JavaTestGenerator

report = JaCoCoParser.parse_report("path/to/jacoco.xml")
tests = JavaTestGenerator.generate_tests(report.gaps)
```

### 3. Claude Desktop (MCP)
Configure in `claude_desktop_config.json` and ask Claude to generate tests.

## MCP Tools Available

### Coverage Analysis Tools
- **parse_jacoco_report**: Analyzes a JaCoCo report and extracts coverage gaps with metrics
- **generate_tests**: Generates Java test templates for uncovered code paths
- **get_coverage_summary**: Returns coverage percentages and top uncovered methods

### Git Automation Tools
- **git_status**: Checks repository status (clean, staged changes, conflicts)
- **git_add_all**: Stages changes with intelligent filtering (excludes build artifacts)
- **git_commit**: Creates commits with coverage statistics appended
- **git_push**: Pushes to remote with upstream configuration
- **git_pull_request**: Creates pull requests via GitHub CLI (requires: `gh auth login`)

## Typical Workflow

For a Java project:

1. Generate JaCoCo report in your Java project:
```bash
mvn clean jacoco:prepare-agent test jacoco:report
```

2. Use the tool to analyze coverage:
```bash
python quick_start.py
# Or via Claude: "Generate tests from target/site/jacoco/jacoco.xml"
```

3. Review generated test templates and implement test logic

4. Run tests and regenerate JaCoCo report

5. Repeat until coverage reaches your target

## Git Automation Example

Automatically commit tests with coverage context and create PR:

```python
from jacoco_test_generator.git_tools import GitTools
from jacoco_test_generator.coverage_parser import JaCoCoParser
from jacoco_test_generator.test_generator import JavaTestGenerator

status = GitTools.git_status(".")
if status.is_clean:
    report = JaCoCoParser.parse_report("target/site/jacoco/jacoco.xml")
    tests = JavaTestGenerator.generate_tests(report.gaps)
    
    GitTools.git_add_all(".")
    GitTools.git_commit(".", "Add tests for coverage",
        {"line_coverage": report.total_line_coverage, "tests_generated": len(tests)})
    GitTools.git_push(".", "origin")
    
    pr = GitTools.git_pull_request(".", base="main", title="Improve coverage")
    print(f"PR created: {pr.url}")
```

## Project Structure

```
jacoco_test_generator/
├── coverage_parser.py      - Parse JaCoCo XML reports
├── test_generator.py       - Generate Java test templates
├── git_tools.py            - Git operations (commit, push, PR)
└── server.py               - MCP server implementation

demo.py                      - Full demonstration
quick_start.py               - Quick example
example_jacoco_report.xml    - Sample for testing
pyproject.toml               - Dependencies and configuration
```

## Key Features

- Parses JaCoCo XML format and extracts coverage gaps
- Identifies uncovered lines by line number
- Generates multiple test scenarios per uncovered method
- JUnit 5 compatible test templates with TODO comments
- Intelligent file filtering for Git operations (excludes build artifacts)
- Commit messages include coverage statistics
- Secure Git operations using system credential helpers
- Complete error handling and validation

## Requirements

### For coverage analysis and test generation
No additional setup needed.

### For Git operations
Standard git is required (already on most systems).

### For pull request creation
Install GitHub CLI:
- macOS: `brew install gh`
- Windows: `choco install gh`
- Linux: See https://cli.github.com

Then authenticate: `gh auth login`

## Common Tasks

### Analyze coverage only
```bash
python -c "
from jacoco_test_generator.coverage_parser import JaCoCoParser
r = JaCoCoParser.parse_report('example_jacoco_report.xml')
print(f'Coverage: {r.total_line_coverage:.1f}%')
"
```

### Generate and save tests
```bash
python -c "
from jacoco_test_generator.coverage_parser import JaCoCoParser
from jacoco_test_generator.test_generator import JavaTestGenerator

report = JaCoCoParser.parse_report('jacoco.xml')
tests = JavaTestGenerator.generate_tests(report.gaps)
test_file = JavaTestGenerator.format_test_file('TestClass', 'com.example', tests)
with open('TestClass.java', 'w') as f:
    f.write(test_file)
"
```

### Full automated workflow with Claude
Ask Claude: "Generate tests from my JaCoCo report until coverage reaches 80%, then commit and create a PR"

Claude will automatically use all tools in the correct sequence.

## Architecture

The tool consists of:

1. **Coverage Parser**: Reads JaCoCo XML, extracts coverage gaps, calculates metrics
2. **Test Generator**: Creates Java test method templates with multiple scenarios
3. **Git Tools**: Manages repository operations with intelligent filtering
4. **MCP Server**: Exposes all tools to Claude and other MCP clients

## Troubleshooting

- "ModuleNotFoundError": Run `pip install -e .`
- "File not found": Check JaCoCo report path is correct
- "Not a git repository": Ensure directory is a git repo or run `git init`
- "gh not found": Install GitHub CLI and authenticate with `gh auth login`
- "Permission denied" on push: Check SSH keys or credentials

## How to Use with Claude

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "jacoco-test-generator": {
      "command": "python",
      "args": ["-m", "jacoco_test_generator.server"],
      "cwd": "/path/to/Software-Testing-Class-Project"
    }
  }
}
```

Then in Claude, you can ask:
- "Analyze this coverage report and tell me the gaps"
- "Generate tests for the lowest coverage methods"
- "Create tests until we reach 75% coverage"
- "Generate tests and create a pull request with the results"

## Testing

All features have been tested:
- XML parsing with sample JaCoCo report
- Coverage gap detection and sorting
- Test generation and file formatting
- Git operations (status, add, commit, push)
- MCP server tool registration and handlers

## License

Part of SE 333 Software Testing Course

## Support

Run `python demo.py` to see working examples.

For specific use cases:
- Coverage analysis: See example_jacoco_report.xml and demo.py
- Test generation: See demo.py output
- Git automation: See git_tools.py documentation
- MCP integration: See server.py tool definitions
