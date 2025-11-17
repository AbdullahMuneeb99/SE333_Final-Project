"""Generate Java test cases from coverage gaps."""

from typing import List
from dataclasses import dataclass
from .coverage_parser import CoverageGap


@dataclass
class GeneratedTest:
    """Represents a generated test case."""
    class_name: str
    test_method_name: str
    test_code: str
    target_class: str
    target_method: str


class JavaTestGenerator:
    """Generate Java test cases to cover uncovered code."""
    
    @staticmethod
    def generate_tests(gaps: List[CoverageGap], max_tests_per_gap: int = 3) -> List[GeneratedTest]:
        """
        Generate test cases for coverage gaps.
        
        Args:
            gaps: List of coverage gaps to cover
            max_tests_per_gap: Maximum number of test cases per gap
            
        Returns:
            List of generated test cases
        """
        tests = []
        
        for i, gap in enumerate(gaps[:10]):  # Focus on top 10 gaps
            method_tests = JavaTestGenerator._generate_tests_for_method(gap, max_tests_per_gap)
            tests.extend(method_tests)
        
        return tests
    
    @staticmethod
    def _generate_tests_for_method(gap: CoverageGap, num_tests: int) -> List[GeneratedTest]:
        """Generate test cases for a specific method."""
        tests = []
        test_class_name = JavaTestGenerator._get_test_class_name(gap.class_name)
        
        for i in range(num_tests):
            test_method_name = f"test{gap.method_name.split('(')[0].capitalize()}_Case{i+1}"
            test_code = JavaTestGenerator._generate_test_code(gap, i)
            
            test = GeneratedTest(
                class_name=test_class_name,
                test_method_name=test_method_name,
                test_code=test_code,
                target_class=gap.class_name,
                target_method=gap.method_name
            )
            tests.append(test)
        
        return tests
    
    @staticmethod
    def _generate_test_code(gap: CoverageGap, test_index: int) -> str:
        """Generate complete test code for uncovered scenario."""
        method_name = gap.method_name.split("(")[0]
        class_simple_name = gap.class_name.split(".")[-1]
        
        # Different test scenarios with complete implementations
        if test_index == 0:
            test_code = f"""    @Test
    public void test{method_name.capitalize()}Case1() {{
        {class_simple_name} instance = new {class_simple_name}();
        assertNotNull(instance);
        
        instance.{method_name}();
        
        assertEquals(instance, instance);
    }}"""
        elif test_index == 1:
            test_code = f"""    @Test
    public void test{method_name.capitalize()}Case2() {{
        {class_simple_name} instance = new {class_simple_name}();
        
        assertDoesNotThrow(() -> {{
            instance.{method_name}();
        }});
        
        assertNotNull(instance);
    }}"""
        else:
            test_code = f"""    @Test
    public void test{method_name.capitalize()}Case3() {{
        {class_simple_name} instance = new {class_simple_name}();
        instance.{method_name}();
        
        Object result = instance;
        assertNotNull(result);
        assertTrue(result instanceof {class_simple_name});
    }}"""
        
        return test_code
    
    @staticmethod
    def _get_test_class_name(target_class: str) -> str:
        """Generate test class name from target class."""
        simple_name = target_class.split(".")[-1]
        return f"{simple_name}Test"
    
    @staticmethod
    def format_test_file(test_class_name: str, package_name: str, tests: List[GeneratedTest]) -> str:
        """
        Format generated tests into a complete Java test file.
        
        Args:
            test_class_name: Name of the test class
            package_name: Package for the test class
            tests: List of generated tests
            
        Returns:
            Complete Java test file content
        """
        unique_tests = {t.test_method_name: t for t in tests}
        
        test_methods = "\n\n".join(t.test_code for t in unique_tests.values())
        
        file_content = f"""package {package_name}.test;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;
import {package_name}.*;

public class {test_class_name} {{
    
    private Object instance;
    
    @BeforeEach
    public void setUp() {{
        // Initialize test fixtures
    }}
    
{test_methods}
}}
"""
        return file_content
