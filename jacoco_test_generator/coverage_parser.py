"""Parse JaCoCo coverage reports and extract coverage information."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class CoverageGap:
    """Represents a method or class with incomplete coverage."""
    class_name: str
    method_name: Optional[str]
    package_name: str
    line_coverage: float  # percentage 0-100
    branch_coverage: float  # percentage 0-100
    uncovered_lines: List[int]


@dataclass
class CoverageReport:
    """JaCoCo coverage report summary."""
    total_line_coverage: float
    total_branch_coverage: float
    gaps: List[CoverageGap]


class JaCoCoParser:
    """Parser for JaCoCo XML coverage reports."""
    
    @staticmethod
    def parse_report(xml_path: str) -> CoverageReport:
        """
        Parse a JaCoCo XML coverage report.
        
        Args:
            xml_path: Path to the JaCoCo XML report file
            
        Returns:
            CoverageReport with coverage summary and gaps
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        gaps = []
        total_line_coverage = 0.0
        total_branch_coverage = 0.0
        
        # Parse packages
        for package in root.findall(".//package"):
            package_name = package.get("name", "")
            
            # Parse classes
            for cls in package.findall(".//class"):
                class_name = cls.get("name", "")
                full_class = f"{package_name}.{class_name}".replace("/", ".")
                
                # Parse methods
                for method in cls.findall(".//method"):
                    method_name = method.get("name", "")
                    signature = method.get("desc", "")
                    
                    # Get line and branch coverage
                    line_coverage = JaCoCoParser._get_coverage_percent(method, "line")
                    branch_coverage = JaCoCoParser._get_coverage_percent(method, "branch")
                    
                    # If not fully covered, add as gap
                    if line_coverage < 100:
                        uncovered_lines = JaCoCoParser._get_uncovered_lines(method)
                        gap = CoverageGap(
                            class_name=full_class,
                            method_name=f"{method_name}{signature}",
                            package_name=package_name,
                            line_coverage=line_coverage,
                            branch_coverage=branch_coverage,
                            uncovered_lines=uncovered_lines
                        )
                        gaps.append(gap)
                
                # Also track class-level coverage
                class_line_coverage = JaCoCoParser._get_coverage_percent(cls, "line")
                class_branch_coverage = JaCoCoParser._get_coverage_percent(cls, "branch")
                
                if class_line_coverage > total_line_coverage:
                    total_line_coverage = class_line_coverage
                if class_branch_coverage > total_branch_coverage:
                    total_branch_coverage = class_branch_coverage
        
        # Get overall coverage
        for counter in root.findall(".//counter"):
            counter_type = counter.get("type", "")
            if counter_type == "LINE":
                covered = int(counter.get("covered", 0))
                missed = int(counter.get("missed", 0))
                total = covered + missed
                if total > 0:
                    total_line_coverage = (covered / total) * 100
            elif counter_type == "BRANCH":
                covered = int(counter.get("covered", 0))
                missed = int(counter.get("missed", 0))
                total = covered + missed
                if total > 0:
                    total_branch_coverage = (covered / total) * 100
        
        # Sort gaps by coverage (lowest first)
        gaps.sort(key=lambda g: g.line_coverage)
        
        return CoverageReport(
            total_line_coverage=total_line_coverage,
            total_branch_coverage=total_branch_coverage,
            gaps=gaps
        )
    
    @staticmethod
    def _get_coverage_percent(element, counter_type: str) -> float:
        """Extract coverage percentage for a specific counter type."""
        for counter in element.findall("counter"):
            if counter.get("type") == counter_type.upper():
                covered = int(counter.get("covered", 0))
                missed = int(counter.get("missed", 0))
                total = covered + missed
                if total > 0:
                    return (covered / total) * 100
        return 0.0
    
    @staticmethod
    def _get_uncovered_lines(method_element) -> List[int]:
        """Extract line numbers that are not covered."""
        uncovered = []
        for line in method_element.findall("line"):
            line_num = int(line.get("nr", 0))
            ci = int(line.get("ci", 0))  # covered instructions
            if ci == 0:
                uncovered.append(line_num)
        return uncovered
