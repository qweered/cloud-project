"""
Unit tests for user models
"""

import unittest
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.models import UserRole, UserCreate, UserResponse, UserUpdate
from app.auth import get_password_hash, verify_password, create_access_token


class TestUserModels(unittest.TestCase):
    """Test suite for user model functionality."""
    
    def test_user_role_enum(self):
        """Test user role enum values."""
        self.assertEqual(UserRole.PASSENGER, "passenger")
        self.assertEqual(UserRole.DRIVER, "driver")
        self.assertEqual(UserRole.ADMIN, "admin")
    
    def test_user_create_model(self):
        """Test user create model validation."""
        user = UserCreate(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            phone_number="+1234567890",
            password="securepass123",
            role=UserRole.PASSENGER
        )
        
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.password, "securepass123")
        self.assertEqual(user.role, UserRole.PASSENGER)
        self.assertIsNone(user.vehicle_model)
        self.assertIsNone(user.license_plate)
        self.assertIsNone(user.max_passengers)
    
    def test_driver_user_create_model(self):
        """Test driver-specific fields in user create model."""
        driver = UserCreate(
            email="driver@example.com",
            first_name="Jane",
            last_name="Driver",
            phone_number="+1987654321",
            password="driverpass123",
            role=UserRole.DRIVER,
            vehicle_model="Tesla Model 3",
            license_plate="ABC123",
            max_passengers=4
        )
        
        self.assertEqual(driver.role, UserRole.DRIVER)
        self.assertEqual(driver.vehicle_model, "Tesla Model 3")
        self.assertEqual(driver.license_plate, "ABC123")
        self.assertEqual(driver.max_passengers, 4)
    
    def test_user_update_model(self):
        """Test user update model."""
        update = UserUpdate(first_name="Updated", last_name="Name")
        
        self.assertEqual(update.first_name, "Updated")
        self.assertEqual(update.last_name, "Name")
        self.assertIsNone(update.phone_number)
        self.assertIsNone(update.password)
        
        # Test optional fields
        empty_update = UserUpdate()
        self.assertIsNone(empty_update.first_name)
        self.assertIsNone(empty_update.last_name)
        self.assertIsNone(empty_update.phone_number)
    
    def test_password_hashing(self):
        """Test password hashing functionality."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Verify hash is different from original
        self.assertNotEqual(password, hashed)
        self.assertTrue(len(hashed) > 10)
        
        # Verify password verification works
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrongpassword", hashed))
    
    def test_access_token_creation(self):
        """Test JWT access token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 50)  # JWT tokens are typically long
        
        # Verify it contains expected parts (header.payload.signature)
        parts = token.split('.')
        self.assertEqual(len(parts), 3)


if __name__ == "__main__":
    unittest.main() 