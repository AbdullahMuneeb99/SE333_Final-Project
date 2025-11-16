"""Demonstration and testing of the JaCoCo Test Generator."""

from jacoco_test_generator.coverage_parser import JaCoCoParser
from jacoco_test_generator.test_generator import JavaTestGenerator


def demo():
    """Run a demonstration of the test generator."""
    
    print("=" * 70)
    print("JaCoCo Test Generator - Demo")
    print("=" * 70)
    
    # Using the example report
    report_path = "assignment3_jacoco_report.xml"
    
    print(f"\n1. Parsing coverage report: {report_path}")
    print("-" * 70)
    
    try:
        report = JaCoCoParser.parse_report(report_path)
        
        print(f"\nCoverage Summary:")
        print(f"  Line Coverage:      {report.total_line_coverage:.2f}%")
        print(f"  Branch Coverage:    {report.total_branch_coverage:.2f}%")
        print(f"  Methods with gaps:  {len(report.gaps)}")
        
        print(f"\nTop 5 Coverage Gaps:")
        for i, gap in enumerate(report.gaps[:5], 1):
            print(f"\n  {i}. {gap.class_name}.{gap.method_name}")
            print(f"     Line Coverage:    {gap.line_coverage:.2f}%")
            print(f"     Branch Coverage:  {gap.branch_coverage:.2f}%")
            print(f"     Uncovered lines:  {gap.uncovered_lines}")
        
        print("\n" + "=" * 70)
        print("2. Generating test cases")
        print("-" * 70)
        
        tests = JavaTestGenerator.generate_tests(report.gaps, max_tests_per_gap=2)
        
        print(f"\nGenerated {len(tests)} test cases")
        
        print("\nSample Generated Tests:")
        for i, test in enumerate(tests[:3], 1):
            print(f"\n  Test {i}: {test.class_name}.{test.test_method_name}")
            print(f"  Target: {test.target_class}.{test.target_method}")
            print("\n  Code:")
            for line in test.test_code.split("\n"):
                print(f"    {line}")
        
        print("\n" + "=" * 70)
        print("3. Formatting complete test file")
        print("-" * 70)
        
        # Formatting first test file
        target_gap = report.gaps[0]
        gap_tests = [t for t in tests if t.target_class == target_gap.class_name]
        
        if gap_tests:
            test_class_name = gap_tests[0].class_name
            package_name = target_gap.package_name
            
            test_file = JavaTestGenerator.format_test_file(test_class_name, package_name, gap_tests)
            
            print(f"\nGenerated test file: {package_name}.test.{test_class_name}")
            print("\nFirst 50 lines:")
            lines = test_file.split("\n")[:50]
            for line in lines:
                print(line)
        
        print("\n" + "=" * 70)
        print("Demo Complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo()
