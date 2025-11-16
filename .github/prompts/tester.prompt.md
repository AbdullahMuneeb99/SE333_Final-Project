---
agent: "agent"
tools: ['jacoco_find_path', 'missing_coverage', 'jacoco_coverage', 'generate_tests', 'run_tests', 'fix_tests', 'parse_report', 'git_commit', 'git_push', 'git_pull_request', 'git_status', 'mvn test']
description: "tools to automate test generation and coverage improvement for Java projects using JaCoCo reports"
model: 'Claude-3.5-Sonnet'
---
##Follow Instructions below: ##

1. First find all the source code to test
2. Generate test
3. run test using 'mvn test'
4. If test has errors, fix it using 'fix tests' and run 'mvn test'
5. Find coverage using 'jacoco_find_path'
6. Then use the path and parse it using 'missing_coverage'
7. If there is missing coverage then generate more test using 'generate tests'
8. repeat 3-7 until 'jacoco_coverage' is 100% or 'missing_coverage' is zero