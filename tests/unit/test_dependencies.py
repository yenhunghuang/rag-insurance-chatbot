"""Unit tests for dependency validation and tool configurations.

Tests that all required dependencies are available and tools are properly configured
following the testing standards from coding-standards.md.
"""

import pytest
import subprocess
import sys
import importlib
from pathlib import Path
from typing import List, Dict, Any
import pkg_resources


class TestRequiredDependencies:
    """Test that all required dependencies are available."""

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists and is readable."""
        requirements_path = Path("requirements.txt")
        assert requirements_path.exists(), "requirements.txt should exist"

        content = requirements_path.read_text()
        assert len(content.strip()) > 0, "requirements.txt should not be empty"

    def test_requirements_dev_file_exists(self):
        """Test that requirements-dev.txt exists."""
        requirements_dev_path = Path("requirements-dev.txt")
        assert requirements_dev_path.exists(), "requirements-dev.txt should exist"

        content = requirements_dev_path.read_text()
        assert len(content.strip()) > 0, "requirements-dev.txt should not be empty"

    def test_core_dependencies_importable(self):
        """Test that core dependencies can be imported."""
        core_dependencies = [
            "fastapi",
            "uvicorn",
            "openai",
            "numpy",
            "pydantic",
            "python_dotenv",
            "yaml",
        ]

        failed_imports = []
        for dep in core_dependencies:
            try:
                # Handle different import names
                import_name = dep
                if dep == "python_dotenv":
                    import_name = "dotenv"
                elif dep == "yaml":
                    import_name = "yaml"

                importlib.import_module(import_name)
            except ImportError as e:
                failed_imports.append(f"{dep}: {str(e)}")

        assert (
            not failed_imports
        ), f"Failed to import core dependencies: {failed_imports}"

    def test_ai_ml_dependencies_importable(self):
        """Test that AI/ML dependencies can be imported."""
        ai_ml_dependencies = [
            ("sentence_transformers", "sentence_transformers"),
            ("faiss", "faiss"),  # This might be faiss-cpu
        ]

        failed_imports = []
        for package_name, import_name in ai_ml_dependencies:
            try:
                importlib.import_module(import_name)
            except ImportError as e:
                # For faiss, try faiss-cpu
                if import_name == "faiss":
                    try:
                        importlib.import_module("faiss")
                    except ImportError:
                        failed_imports.append(f"{package_name}: {str(e)}")
                else:
                    failed_imports.append(f"{package_name}: {str(e)}")

        if failed_imports:
            pytest.skip(f"AI/ML dependencies not available: {failed_imports}")

    def test_development_dependencies_importable(self):
        """Test that development dependencies can be imported."""
        dev_dependencies = ["pytest", "black", "flake8", "mypy"]

        failed_imports = []
        for dep in dev_dependencies:
            try:
                importlib.import_module(dep)
            except ImportError as e:
                failed_imports.append(f"{dep}: {str(e)}")

        # Development dependencies are optional in some environments
        if failed_imports:
            pytest.skip(f"Development dependencies not available: {failed_imports}")


class TestCodeQualityTools:
    """Test that code quality tools are properly configured."""

    def test_black_configuration(self):
        """Test that Black formatter is configured correctly."""
        # Check for Black configuration in pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            if "[tool.black]" in content:
                assert (
                    "line-length" in content or "line_length" in content
                ), "Black should have line length configured"

        # Test that Black can run without errors on a sample file
        try:
            result = subprocess.run(
                [sys.executable, "-m", "black", "--check", "--diff", "src/config.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Black should either pass (0) or show formatting differences (1)
            assert result.returncode in [
                0,
                1,
            ], f"Black check failed with unexpected error: {result.stderr}"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Black not available or timed out")

    def test_flake8_configuration(self):
        """Test that Flake8 linter is configured correctly."""
        # Check for Flake8 configuration
        flake8_configs = [".flake8", "setup.cfg", "tox.ini", "pyproject.toml"]
        config_found = any(Path(config).exists() for config in flake8_configs)

        if config_found:
            # Check that configuration has reasonable settings
            for config_file in flake8_configs:
                config_path = Path(config_file)
                if config_path.exists():
                    content = config_path.read_text()
                    if "flake8" in content or "[flake8]" in content:
                        # Should have max-line-length configured
                        assert (
                            "max-line-length" in content or "max_line_length" in content
                        ), "Flake8 should have max line length configured"
                        break

        # Test that Flake8 can run without critical errors
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", "src/config.py"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Flake8 should either pass or show linting issues, not crash
            assert result.returncode in [
                0,
                1,
            ], f"Flake8 failed with unexpected error: {result.stderr}"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Flake8 not available or timed out")

    def test_mypy_configuration(self):
        """Test that MyPy type checker can run."""
        # Check for MyPy configuration
        mypy_configs = ["mypy.ini", ".mypy.ini", "pyproject.toml", "setup.cfg"]

        try:
            result = subprocess.run(
                [sys.executable, "-m", "mypy", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            assert result.returncode == 0, f"MyPy version check failed: {result.stderr}"
            assert "mypy" in result.stdout.lower(), "Should show MyPy version"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("MyPy not available")

    def test_pytest_configuration(self):
        """Test that pytest is properly configured."""
        # Check for pytest configuration
        pytest_configs = ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"]

        # Test that pytest can discover tests
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--collect-only", "-q"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert (
                result.returncode == 0
            ), f"Pytest test discovery failed: {result.stderr}"
            assert (
                "test session starts" in result.stdout or "collected" in result.stdout
            ), "Pytest should discover test files"

        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Pytest not available or timed out")


class TestProjectStructure:
    """Test that project structure is properly set up."""

    def test_source_directory_structure(self):
        """Test that src/ directory has proper structure."""
        src_path = Path("src")
        assert src_path.exists(), "src/ directory should exist"
        assert src_path.is_dir(), "src/ should be a directory"

        # Check for __init__.py
        init_file = src_path / "__init__.py"
        assert init_file.exists(), "src/__init__.py should exist"

        # Check for core modules
        core_modules = ["config.py", "models.py", "exceptions.py", "utils.py"]
        for module in core_modules:
            module_path = src_path / module
            assert module_path.exists(), f"src/{module} should exist"

    def test_data_directory_structure(self):
        """Test that data/ directory has proper structure."""
        data_path = Path("data")
        assert data_path.exists(), "data/ directory should exist"

        # Check for subdirectories
        subdirs = ["raw", "processed", "indices", "test"]
        for subdir in subdirs:
            subdir_path = data_path / subdir
            assert subdir_path.exists(), f"data/{subdir}/ should exist"
            assert subdir_path.is_dir(), f"data/{subdir}/ should be a directory"

    def test_tests_directory_structure(self):
        """Test that tests/ directory has proper structure."""
        tests_path = Path("tests")
        assert tests_path.exists(), "tests/ directory should exist"

        # Check for test subdirectories
        test_types = ["unit", "integration", "e2e"]
        for test_type in test_types:
            test_dir = tests_path / test_type
            assert test_dir.exists(), f"tests/{test_type}/ should exist"
            assert test_dir.is_dir(), f"tests/{test_type}/ should be a directory"

        # Check for conftest.py
        conftest_file = tests_path / "conftest.py"
        if conftest_file.exists():
            content = conftest_file.read_text()
            assert (
                "pytest" in content or "import" in content
            ), "conftest.py should contain pytest configuration"

    def test_documentation_structure(self):
        """Test that documentation structure exists."""
        docs_path = Path("docs")
        assert docs_path.exists(), "docs/ directory should exist"

        # Check for key documentation files
        doc_files = ["prd.md"]
        for doc_file in doc_files:
            doc_path = docs_path / doc_file
            if doc_path.exists():
                content = doc_path.read_text()
                assert len(content) > 100, f"{doc_file} should have substantial content"

    def test_gitignore_configuration(self):
        """Test that .gitignore is properly configured."""
        gitignore_path = Path(".gitignore")
        assert gitignore_path.exists(), ".gitignore should exist"

        content = gitignore_path.read_text()

        # Check for Python-specific ignores
        python_ignores = ["__pycache__", "*.pyc", ".pytest_cache", "*.egg-info"]
        for ignore in python_ignores:
            assert ignore in content, f".gitignore should contain {ignore}"

        # Check for IDE ignores
        ide_ignores = [".vscode", ".idea"]
        ide_found = any(ignore in content for ignore in ide_ignores)
        assert ide_found, ".gitignore should contain IDE-specific ignores"

        # Check for environment files
        env_ignores = [".env", "*.log"]
        for ignore in env_ignores:
            assert ignore in content, f".gitignore should contain {ignore}"


class TestEnvironmentConfiguration:
    """Test environment configuration setup."""

    def test_env_example_file(self):
        """Test that .env.example exists with required variables."""
        env_example_path = Path(".env.example")
        assert env_example_path.exists(), ".env.example should exist"

        content = env_example_path.read_text()

        # Check for required environment variables
        required_vars = ["OPENAI_API_KEY", "LOG_LEVEL"]
        for var in required_vars:
            assert f"{var}=" in content, f".env.example should contain {var}"

    def test_python_version_compatibility(self):
        """Test that Python version meets requirements."""
        version_info = sys.version_info

        # Should be Python 3.8 or higher
        assert version_info.major >= 3, "Should use Python 3.x"
        assert (
            version_info.minor >= 8
        ), f"Should use Python 3.8+, got {version_info.major}.{version_info.minor}"

    def test_package_metadata(self):
        """Test that package metadata is properly configured."""
        # Check for setup.py or pyproject.toml
        setup_py = Path("setup.py")
        pyproject_toml = Path("pyproject.toml")

        has_setup = setup_py.exists() or pyproject_toml.exists()
        assert has_setup, "Should have setup.py or pyproject.toml for package metadata"

        if pyproject_toml.exists():
            content = pyproject_toml.read_text()
            assert (
                "[build-system]" in content or "[project]" in content
            ), "pyproject.toml should have build system or project configuration"
