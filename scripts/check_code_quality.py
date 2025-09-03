#!/usr/bin/env python3
"""
Code Quality Validation Script

Runs all code quality checks for the RAG Insurance Chatbot project.
This script validates formatting, linting, type checking, and security.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse


class CodeQualityChecker:
    """Code quality validation orchestrator."""
    
    def __init__(self, fix_issues: bool = False, verbose: bool = False):
        """Initialize code quality checker.
        
        Args:
            fix_issues: Whether to automatically fix issues when possible.
            verbose: Whether to show detailed output.
        """
        self.fix_issues = fix_issues
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.results: List[Tuple[str, bool, str]] = []
    
    def run_command(self, command: List[str], description: str) -> bool:
        """Run a shell command and capture results.
        
        Args:
            command: Command to run as list of strings.
            description: Human-readable description of the command.
            
        Returns:
            True if command succeeded, False otherwise.
        """
        print(f"🔍 {description}...")
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            success = result.returncode == 0
            
            if self.verbose or not success:
                if result.stdout:
                    print(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    print(f"STDERR:\n{result.stderr}")
            
            status = "✅" if success else "❌"
            output = result.stdout + result.stderr
            
            print(f"{status} {description}: {'PASSED' if success else 'FAILED'}")
            self.results.append((description, success, output))
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"❌ {description}: TIMEOUT")
            self.results.append((description, False, "Command timed out"))
            return False
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")
            self.results.append((description, False, str(e)))
            return False
    
    def check_black_formatting(self) -> bool:
        """Check Python code formatting with Black."""
        command = ["python", "-m", "black"]
        
        if self.fix_issues:
            command.extend(["src/", "scripts/", "tests/"])
            description = "Formatting code with Black"
        else:
            command.extend(["--check", "--diff", "src/", "scripts/", "tests/"])
            description = "Checking code formatting with Black"
        
        return self.run_command(command, description)
    
    def check_isort_imports(self) -> bool:
        """Check import sorting with isort."""
        command = ["python", "-m", "isort"]
        
        if self.fix_issues:
            command.extend(["src/", "scripts/", "tests/"])
            description = "Sorting imports with isort"
        else:
            command.extend(["--check-only", "--diff", "src/", "scripts/", "tests/"])
            description = "Checking import sorting with isort"
        
        return self.run_command(command, description)
    
    def check_flake8_linting(self) -> bool:
        """Check code linting with Flake8."""
        command = [
            "python", "-m", "flake8", 
            "src/", "scripts/", "tests/"
        ]
        return self.run_command(command, "Running Flake8 linting")
    
    def check_mypy_types(self) -> bool:
        """Check type annotations with MyPy."""
        command = ["python", "-m", "mypy", "src/"]
        return self.run_command(command, "Checking types with MyPy")
    
    def check_security_bandit(self) -> bool:
        """Check security issues with Bandit."""
        command = [
            "python", "-m", "bandit", 
            "-r", "src/", 
            "-x", "tests/",
            "-f", "screen"
        ]
        return self.run_command(command, "Checking security with Bandit")
    
    def run_tests(self) -> bool:
        """Run pytest test suite."""
        command = [
            "python", "-m", "pytest", 
            "tests/", 
            "-v",
            "--tb=short"
        ]
        return self.run_command(command, "Running test suite")
    
    def validate_requirements(self) -> bool:
        """Validate requirements files."""
        requirements_files = [
            "requirements.txt", 
            "requirements-dev.txt"
        ]
        
        all_valid = True
        for req_file in requirements_files:
            req_path = self.project_root / req_file
            if not req_path.exists():
                print(f"❌ Missing requirements file: {req_file}")
                all_valid = False
                continue
            
            # Try to parse requirements
            command = ["python", "-m", "pip", "check"]
            if not self.run_command(command, f"Validating {req_file}"):
                all_valid = False
        
        return all_valid
    
    def run_all_checks(self) -> bool:
        """Run all code quality checks.
        
        Returns:
            True if all checks passed, False otherwise.
        """
        print("🚀 Running Code Quality Checks for RAG Insurance Chatbot\n")
        
        checks = [
            ("Requirements Validation", self.validate_requirements),
            ("Black Formatting", self.check_black_formatting),
            ("Import Sorting", self.check_isort_imports), 
            ("Flake8 Linting", self.check_flake8_linting),
            ("MyPy Type Checking", self.check_mypy_types),
            ("Bandit Security", self.check_security_bandit),
        ]
        
        # Only run tests if test files exist
        test_dir = self.project_root / "tests"
        if test_dir.exists() and any(test_dir.rglob("test_*.py")):
            checks.append(("Test Suite", self.run_tests))
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if not check_func():
                    all_passed = False
            except Exception as e:
                print(f"❌ {check_name} failed with exception: {e}")
                all_passed = False
            print()  # Add spacing between checks
        
        return all_passed
    
    def print_summary(self):
        """Print summary of all check results."""
        print("📊 Code Quality Check Summary")
        print("=" * 50)
        
        passed = sum(1 for _, success, _ in self.results if success)
        total = len(self.results)
        
        for description, success, _ in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {description}")
        
        print("=" * 50)
        print(f"Results: {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 All code quality checks passed!")
        else:
            print("⚠️  Some checks failed. Please review and fix issues.")
            if not self.fix_issues:
                print("💡 Run with --fix to automatically fix some issues.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run code quality checks for RAG Insurance Chatbot"
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Automatically fix issues when possible"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true", 
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    checker = CodeQualityChecker(
        fix_issues=args.fix, 
        verbose=args.verbose
    )
    
    try:
        success = checker.run_all_checks()
        checker.print_summary()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n🛑 Code quality check interrupted by user")
        return 130
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())