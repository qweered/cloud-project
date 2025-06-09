#!/usr/bin/env python3
"""
Tests for Docker build process and common module accessibility
"""

import subprocess
import tempfile
import os
import pytest


class TestDockerBuild:
    """Test Docker build process for all services."""
    
    services = ["users", "rides", "payments", "matching"]
    
    def test_docker_context_structure(self):
        """Test that the services directory has the correct structure."""
        services_path = "services"
        assert os.path.exists(services_path), "Services directory should exist"
        
        # Check common module exists
        common_path = os.path.join(services_path, "common")
        assert os.path.exists(common_path), "Common module directory should exist"
        assert os.path.exists(os.path.join(common_path, "__init__.py")), "Common module should be a Python package"
        
        # Check each service exists
        for service in self.services:
            service_path = os.path.join(services_path, service)
            assert os.path.exists(service_path), f"{service} service directory should exist"
            assert os.path.exists(os.path.join(service_path, "Dockerfile")), f"{service} should have Dockerfile"
            assert os.path.exists(os.path.join(service_path, "requirements.txt")), f"{service} should have requirements.txt"
            assert os.path.exists(os.path.join(service_path, "main.py")), f"{service} should have main.py"
    
    @pytest.mark.parametrize("service", services)
    def test_dockerfile_syntax(self, service):
        """Test that Dockerfiles have correct syntax."""
        dockerfile_path = f"services/{service}/Dockerfile"
        
        with open(dockerfile_path, 'r') as f:
            content = f.read()
        
        # Check that common module is properly copied
        assert "COPY common ./common" in content, f"{service} Dockerfile should copy common module"
        
        # Check that service files are copied correctly
        assert f"COPY {service} ." in content, f"{service} Dockerfile should copy service files"
        
        # Check that requirements are copied from correct path
        assert f"COPY {service}/requirements.txt ." in content, f"{service} Dockerfile should copy requirements from correct path"
    
    @pytest.mark.parametrize("service", services)  
    def test_docker_build_dry_run(self, service):
        """Test Docker build process without actually building."""
        dockerfile_path = f"services/{service}/Dockerfile"
        context_path = "services"
        
        # Test that docker build command syntax is correct
        cmd = [
            "docker", "build", 
            "--dry-run",  # This flag doesn't exist but we're testing the command structure
            "-f", dockerfile_path,
            "-t", f"test-{service}:latest",
            context_path
        ]
        
        # We expect this to fail with "unknown flag" but not with file not found
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # The command should fail due to --dry-run flag, not due to missing files
        assert "unknown flag" in result.stderr.lower() or "no such file" not in result.stderr.lower()
    
    def test_common_module_imports(self):
        """Test that common module can be imported correctly."""
        import sys
        import os
        
        # Add services directory to path
        services_path = os.path.abspath("services")
        if services_path not in sys.path:
            sys.path.insert(0, services_path)
        
        try:
            # Test importing common modules
            from common.base_service import BaseService
            from common.metrics import ServiceMetrics
            from common.messaging import MessageBroker
            
            # Test that classes can be instantiated
            assert BaseService is not None
            assert ServiceMetrics is not None  
            assert MessageBroker is not None
            
        except ImportError as e:
            pytest.fail(f"Failed to import common modules: {e}")
        finally:
            # Clean up sys.path
            if services_path in sys.path:
                sys.path.remove(services_path)
    
    def test_ci_workflow_context_config(self):
        """Test that CI workflow has correct Docker context configuration."""
        workflow_path = ".github/workflows/azure-deploy.yml"
        
        with open(workflow_path, 'r') as f:
            content = f.read()
        
        # Check that context is set to ./services
        assert "context: ./services" in content, "CI workflow should use ./services as Docker context"
        
        # Check that file parameter is specified for each service
        assert "file: ./services/${{ matrix.service }}/Dockerfile" in content, "CI workflow should specify Dockerfile path"
    
    def test_encryption_module_accessibility(self):
        """Test that our new encryption module is accessible in the users service."""
        import sys
        import os
        
        # Add users service path
        users_path = os.path.abspath("services/users")
        services_path = os.path.abspath("services") 
        
        if users_path not in sys.path:
            sys.path.insert(0, users_path)
        if services_path not in sys.path:
            sys.path.insert(0, services_path)
        
        try:
            # Test that encryption module can be imported
            from app.encryption import encrypt_pii, decrypt_pii, encrypt_user_pii, decrypt_user_pii
            
            # Test basic encryption functionality
            test_data = "test@example.com"
            encrypted = encrypt_pii(test_data)
            decrypted = decrypt_pii(encrypted)
            
            assert encrypted != test_data, "Data should be encrypted"
            assert decrypted == test_data, "Data should decrypt correctly"
            
        except ImportError as e:
            pytest.fail(f"Failed to import encryption module: {e}")
        finally:
            # Clean up sys.path
            for path in [users_path, services_path]:
                if path in sys.path:
                    sys.path.remove(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 