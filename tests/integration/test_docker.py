"""Integration tests for Docker container functionality.

Tests Docker container builds, environment setup, and basic service functionality
following the testing standards from coding-standards.md.
"""

import pytest
import subprocess
import time
import requests
import os
from pathlib import Path
from typing import List, Dict, Any


class TestDockerBuild:
    """Test Docker container build process."""

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and is readable."""
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile should exist in project root"
        assert dockerfile_path.is_file(), "Dockerfile should be a file"

        # Verify Dockerfile is readable
        content = dockerfile_path.read_text()
        assert len(content) > 0, "Dockerfile should not be empty"
        assert "FROM python:" in content, "Dockerfile should use Python base image"

    def test_dockerignore_exists(self):
        """Test that .dockerignore exists and contains expected patterns."""
        dockerignore_path = Path(".dockerignore")
        assert dockerignore_path.exists(), ".dockerignore should exist"

        content = dockerignore_path.read_text()
        expected_patterns = [".git", "*.pyc", "__pycache__", ".pytest_cache", "*.md"]
        for pattern in expected_patterns:
            assert pattern in content, f".dockerignore should contain {pattern}"

    @pytest.mark.slow
    def test_docker_build_succeeds(self):
        """Test that Docker image builds successfully."""
        try:
            # Build the Docker image
            result = subprocess.run(
                ["docker", "build", "-t", "rag-insurance-chatbot:test", "."],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            assert result.returncode == 0, f"Docker build failed: {result.stderr}"
            assert (
                "Successfully tagged rag-insurance-chatbot:test" in result.stdout
                or result.stderr
            )

        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out after 5 minutes")
        except FileNotFoundError:
            pytest.skip("Docker not available in test environment")

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists for Docker build."""
        requirements_path = Path("requirements.txt")
        assert (
            requirements_path.exists()
        ), "requirements.txt should exist for Docker build"

        content = requirements_path.read_text()
        expected_deps = ["fastapi", "uvicorn", "openai", "python-dotenv"]
        for dep in expected_deps:
            assert any(
                dep in line for line in content.splitlines()
            ), f"requirements.txt should contain {dep}"


class TestDockerCompose:
    """Test Docker Compose configuration."""

    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists and is valid."""
        compose_path = Path("docker-compose.yml")
        assert compose_path.exists(), "docker-compose.yml should exist"

        content = compose_path.read_text()
        assert "version:" in content, "docker-compose.yml should specify version"
        assert "services:" in content, "docker-compose.yml should define services"
        assert (
            "rag-chatbot" in content or "app" in content
        ), "Should define main service"

    def test_docker_compose_syntax(self):
        """Test that docker-compose.yml has valid syntax."""
        try:
            result = subprocess.run(
                ["docker-compose", "config"], capture_output=True, text=True, timeout=30
            )

            # docker-compose config should succeed if syntax is valid
            assert (
                result.returncode == 0
            ), f"docker-compose.yml syntax error: {result.stderr}"

        except FileNotFoundError:
            pytest.skip("docker-compose not available in test environment")
        except subprocess.TimeoutExpired:
            pytest.fail("docker-compose config timed out")

    def test_environment_variables_configured(self):
        """Test that required environment variables are configured."""
        compose_path = Path("docker-compose.yml")
        content = compose_path.read_text()

        # Should reference environment file or have environment section
        assert (
            ".env" in content or "environment:" in content
        ), "Should configure environment variables"

        # Check for .env.example
        env_example_path = Path(".env.example")
        assert env_example_path.exists(), ".env.example should exist for Docker setup"

        env_content = env_example_path.read_text()
        assert (
            "OPENAI_API_KEY=" in env_content
        ), ".env.example should include OPENAI_API_KEY"


@pytest.mark.slow
@pytest.mark.integration
class TestDockerContainerRuntime:
    """Test Docker container runtime functionality."""

    @pytest.fixture(scope="class")
    def docker_container(self):
        """Fixture to build and run Docker container for testing."""
        container_name = "rag-test-container"
        image_name = "rag-insurance-chatbot:test"

        try:
            # Skip if Docker not available
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pytest.skip("Docker not available")

        try:
            # Clean up any existing container
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

            # Build image
            build_result = subprocess.run(
                ["docker", "build", "-t", image_name, "."],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if build_result.returncode != 0:
                pytest.skip(f"Docker build failed: {build_result.stderr}")

            # Run container in detached mode with environment
            run_result = subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    container_name,
                    "-p",
                    "8001:8000",  # Use different port to avoid conflicts
                    "-e",
                    "OPENAI_API_KEY=test-key-for-testing",
                    "-e",
                    "LOG_LEVEL=DEBUG",
                    image_name,
                ],
                capture_output=True,
                text=True,
            )

            if run_result.returncode != 0:
                pytest.skip(f"Docker run failed: {run_result.stderr}")

            # Wait for container to start
            time.sleep(5)

            yield container_name

        finally:
            # Cleanup
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)

    def test_container_starts_successfully(self, docker_container):
        """Test that container starts without errors."""
        container_name = docker_container

        # Check container status
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                f"name={container_name}",
                "--format",
                "{{.Status}}",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert (
            "Up" in result.stdout
        ), f"Container should be running, got: {result.stdout}"

    def test_container_logs_no_critical_errors(self, docker_container):
        """Test that container logs don't show critical errors."""
        container_name = docker_container

        # Get container logs
        result = subprocess.run(
            ["docker", "logs", container_name], capture_output=True, text=True
        )

        logs = result.stdout + result.stderr

        # Check for critical error patterns
        critical_errors = ["CRITICAL", "FATAL", "Exception", "Error:", "Traceback"]
        for error in critical_errors:
            assert error not in logs, f"Container logs contain critical error: {error}"

    def test_health_check_endpoint(self, docker_container):
        """Test that health check endpoint responds."""
        # Wait a bit more for service to be ready
        time.sleep(10)

        try:
            response = requests.get("http://localhost:8001/health", timeout=10)
            assert response.status_code == 200

            health_data = response.json()
            assert health_data["status"] == "healthy"

        except requests.ConnectionError:
            # Check if container is still running
            result = subprocess.run(
                ["docker", "ps", "--filter", f"name={docker_container}"],
                capture_output=True,
                text=True,
            )

            if docker_container not in result.stdout:
                pytest.fail("Container stopped unexpectedly")
            else:
                pytest.fail("Health endpoint not accessible - service may not be ready")
        except requests.Timeout:
            pytest.fail("Health endpoint timed out")

    def test_container_environment_variables(self, docker_container):
        """Test that environment variables are properly set in container."""
        container_name = docker_container

        # Check environment variables in container
        result = subprocess.run(
            ["docker", "exec", container_name, "env"], capture_output=True, text=True
        )

        assert result.returncode == 0
        env_output = result.stdout

        assert "OPENAI_API_KEY=test-key-for-testing" in env_output
        assert "LOG_LEVEL=DEBUG" in env_output
        assert "PYTHONPATH=" in env_output or "PATH=" in env_output

    def test_container_file_structure(self, docker_container):
        """Test that container has expected file structure."""
        container_name = docker_container

        # Check that source files exist in container
        expected_paths = [
            "/app/src",
            "/app/src/config.py",
            "/app/src/exceptions.py",
            "/app/requirements.txt",
        ]

        for path in expected_paths:
            result = subprocess.run(
                ["docker", "exec", container_name, "test", "-e", path],
                capture_output=True,
            )

            assert (
                result.returncode == 0
            ), f"Expected path {path} not found in container"

    def test_container_python_version(self, docker_container):
        """Test that container uses correct Python version."""
        container_name = docker_container

        result = subprocess.run(
            ["docker", "exec", container_name, "python", "--version"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        version_output = result.stdout.strip()

        # Should be Python 3.8 or higher
        assert "Python 3." in version_output
        version_parts = version_output.split(".")
        major_minor = f"{version_parts[0].split()[-1]}.{version_parts[1]}"
        assert (
            float(major_minor) >= 3.8
        ), f"Python version should be 3.8+, got {version_output}"


class TestDockerSecurity:
    """Test Docker security configurations."""

    def test_dockerfile_security_practices(self):
        """Test that Dockerfile follows security best practices."""
        dockerfile_path = Path("Dockerfile")
        content = dockerfile_path.read_text()

        # Should not run as root
        assert "USER " in content, "Dockerfile should create and use non-root user"
        assert "USER root" not in content, "Dockerfile should not run as root user"

        # Should use specific Python version, not latest
        assert (
            "python:latest" not in content
        ), "Should use specific Python version, not latest"

        # Should have proper file permissions
        lines = content.splitlines()
        copy_lines = [
            line for line in lines if line.strip().startswith(("COPY", "ADD"))
        ]
        assert len(copy_lines) > 0, "Should have COPY instructions"

    def test_docker_compose_security(self):
        """Test that docker-compose.yml follows security practices."""
        compose_path = Path("docker-compose.yml")
        content = compose_path.read_text()

        # Should not expose unnecessary ports
        if "ports:" in content:
            # If ports are exposed, they should be specific
            assert (
                "80:80" not in content or "443:443" not in content
            ), "Should not expose standard web ports unnecessarily"

        # Should not mount sensitive directories
        sensitive_mounts = ["/", "/etc", "/var", "/usr"]
        for mount in sensitive_mounts:
            assert (
                f"{mount}:" not in content
            ), f"Should not mount sensitive directory {mount}"

    def test_env_example_no_secrets(self):
        """Test that .env.example doesn't contain actual secrets."""
        env_example_path = Path(".env.example")
        content = env_example_path.read_text()

        # Should have placeholder values, not real secrets
        lines = content.splitlines()
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                if "KEY" in key or "SECRET" in key or "TOKEN" in key:
                    # Should be empty or placeholder
                    assert value in [
                        "",
                        "your_api_key_here",
                        "YOUR_API_KEY",
                        "sk-...",
                    ], f"Secret {key} should be placeholder, not real value"
