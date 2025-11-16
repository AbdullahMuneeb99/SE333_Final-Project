---
mode: "agent"
tools: ['tool1']
description: "description of the tool"
model: 'Gpt-5 mini'
---
##Follow Instructions below: ##
1. First find all the source code to test  
2. Generate test 
3. run test using 'mvn test'
4. if test has errors, fix it and run 'mvn test' 
5. Find coverage using 'jacoco_find_path' 
6. Then we use the path and parse it using 'missing_coverage' 
7. if there is missing coverage then generate more test
8. repeat 3-7 until 'jacoco_coverage' is 100% or 'missing_coverage' is zero 
