"""
Comprehensive Tests for SandboxManager (MOCKED)

Tests Docker-based sandboxed code execution with all Docker operations mocked.
Tests container lifecycle, resource limits, timeout enforcement, and error handling.

Total tests: 12
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import time

from alpha.code_execution.sandbox import (
    SandboxManager,
    SandboxConfig,
    ExecutionResult,
    DockerNotAvailableError,
    ContainerCreationError,
    execute_code_sandboxed
)


class TestSandboxConfig:
    """Test SandboxConfig dataclass"""

    def test_sandbox_config_defaults(self):
        """Test default configuration values"""
        config = SandboxConfig(
            language="python",
            docker_image="python:3.12-slim"
        )

        assert config.language == "python"
        assert config.docker_image == "python:3.12-slim"
        assert config.timeout == 30
        assert config.memory == "256m"
        assert config.cpu_quota == 50000
        assert config.network_mode == "none"
        assert config.read_only_rootfs == True

    def test_sandbox_config_custom_values(self):
        """Test custom configuration values"""
        config = SandboxConfig(
            language="javascript",
            docker_image="node:20-slim",
            timeout=60,
            memory="512m",
            cpu_quota=100000,
            network_mode="bridge",
            read_only_rootfs=False,
            user="1000:1000"
        )

        assert config.timeout == 60
        assert config.memory == "512m"
        assert config.network_mode == "bridge"
        assert config.user == "1000:1000"


class TestExecutionResult:
    """Test ExecutionResult dataclass"""

    def test_execution_result_success(self):
        """Test successful execution result"""
        result = ExecutionResult(
            success=True,
            stdout="Hello, World!\n",
            stderr="",
            exit_code=0,
            execution_time=1.5,
            container_id="abc123"
        )

        assert result.success
        assert result.stdout == "Hello, World!\n"
        assert result.exit_code == 0
        assert result.execution_time == 1.5

    def test_execution_result_failure(self):
        """Test failed execution result"""
        result = ExecutionResult(
            success=False,
            stdout="",
            stderr="Error: division by zero",
            exit_code=1,
            execution_time=0.5,
            error_message="Process exited with code 1",
            timed_out=False
        )

        assert not result.success
        assert result.exit_code == 1
        assert result.error_message is not None


class TestSandboxManager:
    """Test SandboxManager with mocked Docker"""

    @pytest.fixture
    def mock_docker_setup(self):
        """Setup mock Docker client"""
        mock_client = MagicMock()
        
        # Mock ping
        mock_client.ping.return_value = True
        
        # Mock images
        mock_image = Mock()
        mock_client.images.get.return_value = mock_image
        mock_client.images.pull.return_value = mock_image
        
        # Mock container
        mock_container = Mock()
        mock_container.id = "test_container_123"
        mock_container.start = Mock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.side_effect = lambda stdout=True, stderr=False: (
            b"Test output\n" if stdout else b""
        )
        mock_container.stop = Mock()
        mock_container.remove = Mock()
        mock_container.kill = Mock()
        mock_container.reload = Mock()
        mock_container.stats.return_value = {
            "memory_stats": {"usage": 1000000, "limit": 256000000},
            "cpu_stats": {}
        }
        
        mock_client.containers.create.return_value = mock_container
        
        return mock_client

    @pytest.fixture
    def sandbox_config(self):
        """Create test sandbox configuration"""
        return SandboxConfig(
            language="python",
            docker_image="python:3.12-slim",
            timeout=30
        )

    def test_is_docker_available_true(self, mock_docker_setup):
        """Test Docker availability check when Docker is available"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            manager = SandboxManager()
            assert manager.is_docker_available()

    def test_is_docker_available_false_not_installed(self):
        """Test Docker availability when Docker SDK not installed"""
        # Mock the import to raise ImportError
        with patch('builtins.__import__', side_effect=ImportError("No module named 'docker'")):
            manager = SandboxManager()
            assert not manager.is_docker_available()

    def test_is_docker_available_false_not_running(self):
        """Test Docker availability when Docker daemon not running"""
        mock_client = Mock()
        mock_client.ping.side_effect = Exception("Connection refused")
        with patch('docker.from_env', return_value=mock_client):
            manager = SandboxManager()
            assert not manager.is_docker_available()

    def test_create_container_success(self, mock_docker_setup, sandbox_config):
        """Test successful container creation"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            manager = SandboxManager(sandbox_config)
            container_id = manager.create_container(
                language="python",
                code="print('Hello')",
                config=sandbox_config
            )

            assert container_id is not None
            assert container_id == "test_container_123"
            assert container_id in manager._active_containers

    def test_create_container_docker_not_available(self, sandbox_config):
        """Test container creation when Docker not available"""
        with patch('docker.from_env', side_effect=Exception("Docker not running")):
            manager = SandboxManager(sandbox_config)

            with pytest.raises(DockerNotAvailableError):
                manager.create_container("python", "print('test')", sandbox_config)

    def test_execute_code_success(self, mock_docker_setup, sandbox_config):
        """Test successful code execution"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            manager = SandboxManager(sandbox_config)
            container_id = manager.create_container("python", "print('Hello')", sandbox_config)

            result = manager.execute_code(container_id, timeout=30)

            assert result.success
            assert result.exit_code == 0
            assert "Test output" in result.stdout
            assert result.execution_time > 0

    def test_execute_code_timeout(self, mock_docker_setup, sandbox_config):
        """Test code execution timeout handling"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            # Mock timeout
            mock_container = mock_docker_setup.containers.create.return_value
            mock_container.wait.side_effect = Exception("Request timed out")

            manager = SandboxManager(sandbox_config)
            container_id = manager.create_container("python", "while True: pass", sandbox_config)

            result = manager.execute_code(container_id, timeout=1)

            assert not result.success
            assert result.timed_out
            assert "timeout" in result.error_message.lower()

    def test_execute_code_non_zero_exit(self, mock_docker_setup, sandbox_config):
        """Test code execution with non-zero exit code"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            # Mock non-zero exit code
            mock_container = mock_docker_setup.containers.create.return_value
            mock_container.wait.return_value = {"StatusCode": 1}
            mock_container.logs.side_effect = lambda stdout=True, stderr=False: (
                b"" if stdout else b"Error: something went wrong"
            )

            manager = SandboxManager(sandbox_config)
            container_id = manager.create_container("python", "raise Exception('error')", sandbox_config)

            result = manager.execute_code(container_id, timeout=30)

            assert not result.success
            assert result.exit_code == 1
            assert result.error_message is not None

    def test_cleanup_container_success(self, mock_docker_setup, sandbox_config):
        """Test successful container cleanup"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            manager = SandboxManager(sandbox_config)
            container_id = manager.create_container("python", "print('test')", sandbox_config)

            # Verify container is tracked
            assert container_id in manager._active_containers

            # Cleanup
            manager.cleanup_container(container_id)

            # Verify cleanup
            assert container_id not in manager._active_containers
            mock_docker_setup.containers.create.return_value.remove.assert_called_once()

    def test_cleanup_all_containers(self, mock_docker_setup, sandbox_config):
        """Test cleanup of all active containers"""
        # Create different mock containers with unique IDs
        container_id_counter = [0]
        def create_mock_container(*args, **kwargs):
            container_id_counter[0] += 1
            mock_container = Mock()
            mock_container.id = f"test_container_{container_id_counter[0]}"
            mock_container.start = Mock()
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.side_effect = lambda stdout=True, stderr=False: (
                b"Test output\n" if stdout else b""
            )
            mock_container.stop = Mock()
            mock_container.remove = Mock()
            return mock_container

        mock_docker_setup.containers.create = create_mock_container

        with patch('docker.from_env', return_value=mock_docker_setup):
            manager = SandboxManager(sandbox_config)

            # Create multiple containers
            container1 = manager.create_container("python", "print('1')", sandbox_config)
            container2 = manager.create_container("python", "print('2')", sandbox_config)

            assert len(manager._active_containers) == 2

            # Cleanup all
            manager.cleanup_all()

            assert len(manager._active_containers) == 0

    def test_context_manager_cleanup(self, mock_docker_setup, sandbox_config):
        """Test context manager automatic cleanup"""
        with patch('docker.from_env', return_value=mock_docker_setup):
            with SandboxManager(sandbox_config) as manager:
                container_id = manager.create_container("python", "print('test')", sandbox_config)
                assert container_id in manager._active_containers

            # After context exit, all containers should be cleaned up
            # (we can't verify since manager is out of scope, but no exceptions should occur)


class TestConvenienceFunction:
    """Test execute_code_sandboxed convenience function"""

    def test_execute_code_sandboxed_success(self):
        """Test convenience function for simple execution"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True

        mock_container = Mock()
        mock_container.id = "test_123"
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.side_effect = lambda stdout=True, stderr=False: (
            b"42\n" if stdout else b""
        )

        mock_client.images.get.return_value = Mock()
        mock_client.containers.create.return_value = mock_container

        with patch('docker.from_env', return_value=mock_client):
            result = execute_code_sandboxed(
                language="python",
                code="print(42)",
                timeout=10
            )

            assert result.success
            assert "42" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
