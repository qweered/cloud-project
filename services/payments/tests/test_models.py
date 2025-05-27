"""
Unit tests for payment models
"""

import unittest
from datetime import datetime

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.models import (
    PaymentStatus, PaymentMethodType,
    PaymentCreate, PaymentResponse, PaymentUpdate,
    PaymentMethodCreate, PaymentMethodResponse
)


class TestPaymentModels(unittest.TestCase):
    """Test suite for payment model functionality."""
    
    def test_payment_status_enum(self):
        """Test payment status enum values."""
        self.assertEqual(PaymentStatus.PENDING, "pending")
        self.assertEqual(PaymentStatus.COMPLETED, "completed")
        self.assertEqual(PaymentStatus.REFUNDED, "refunded")
        self.assertEqual(PaymentStatus.FAILED, "failed")
    
    def test_payment_method_type_enum(self):
        """Test payment method type enum values."""
        self.assertEqual(PaymentMethodType.CREDIT_CARD, "credit_card")
        self.assertEqual(PaymentMethodType.DEBIT_CARD, "debit_card")
        self.assertEqual(PaymentMethodType.PAYPAL, "paypal")
    
    def test_payment_create_model(self):
        """Test payment create model."""
        payment = PaymentCreate(
            ride_id=1,
            passenger_id=2,
            driver_id=3,
            amount=25.50,
            payment_method="credit_card"
        )
        
        self.assertEqual(payment.ride_id, 1)
        self.assertEqual(payment.passenger_id, 2)
        self.assertEqual(payment.driver_id, 3)
        self.assertEqual(payment.amount, 25.50)
        self.assertEqual(payment.payment_method, "credit_card")
    
    def test_payment_update_model(self):
        """Test payment update model."""
        update = PaymentUpdate(status=PaymentStatus.COMPLETED, transaction_id="txn_123456")
        
        self.assertEqual(update.status, PaymentStatus.COMPLETED)
        self.assertEqual(update.transaction_id, "txn_123456")
        
        # Test optional fields
        empty_update = PaymentUpdate()
        self.assertIsNone(empty_update.status)
        self.assertIsNone(empty_update.transaction_id)
    
    def test_payment_method_create_model(self):
        """Test payment method create model."""
        payment_method = PaymentMethodCreate(
            user_id=1,
            type=PaymentMethodType.CREDIT_CARD,
            card_number="4111111111111111",
            card_holder="John Doe",
            expiry_date="12/25",
            is_default=True
        )
        
        self.assertEqual(payment_method.user_id, 1)
        self.assertEqual(payment_method.type, PaymentMethodType.CREDIT_CARD)
        self.assertEqual(payment_method.card_number, "4111111111111111")
        self.assertEqual(payment_method.card_holder, "John Doe")
        self.assertEqual(payment_method.expiry_date, "12/25")
        self.assertTrue(payment_method.is_default)


if __name__ == "__main__":
    unittest.main() 