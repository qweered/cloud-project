"""
Common RabbitMQ messaging utilities for microservices
"""

import pika
import json
import logging
import os
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import threading
import time


class MessageBroker:
    """RabbitMQ message broker for microservices communication"""
    
    def __init__(self, host: str = None, port: int = 5672, max_retries: int = 10):
        self.host = host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = port
        self.max_retries = max_retries
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self.running = False
        self.callbacks = {}
        
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host, port=self.port)
                )
                self.channel = self.connection.channel()
                logging.info(f"Connected to RabbitMQ at {self.host}:{self.port} on attempt {attempt + 1}")
                return
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff, max 30 seconds
                    logging.warning(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{self.max_retries}): {e}")
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"Failed to connect to RabbitMQ after {self.max_retries} attempts: {e}")
                    raise
    
    def _reconnect(self):
        """Reconnect to RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass
        
        time.sleep(5)  # Wait before reconnecting
        self._connect()
    
    def declare_exchange(self, exchange_name: str, exchange_type: str = 'topic'):
        """Declare an exchange"""
        try:
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True
            )
        except Exception as e:
            logging.error(f"Failed to declare exchange {exchange_name}: {e}")
            self._reconnect()
            self.channel.exchange_declare(
                exchange=exchange_name,
                exchange_type=exchange_type,
                durable=True
            )
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        """Declare a queue"""
        try:
            self.channel.queue_declare(queue=queue_name, durable=durable)
        except Exception as e:
            logging.error(f"Failed to declare queue {queue_name}: {e}")
            self._reconnect()
            self.channel.queue_declare(queue=queue_name, durable=durable)
    
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Bind queue to exchange with routing key"""
        try:
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=queue_name,
                routing_key=routing_key
            )
        except Exception as e:
            logging.error(f"Failed to bind queue {queue_name}: {e}")
            self._reconnect()
            self.channel.queue_bind(
                exchange=exchange_name,
                queue=queue_name,
                routing_key=routing_key
            )
    
    def publish_message(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """Publish a message to an exchange"""
        try:
            # Add metadata to message
            enriched_message = {
                **message,
                'timestamp': datetime.utcnow().isoformat(),
                'routing_key': routing_key
            }
            
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(enriched_message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logging.info(f"Published message to {exchange_name}/{routing_key}")
            
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")
            self._reconnect()
            # Retry once
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(enriched_message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
    
    def add_consumer(self, queue_name: str, callback: Callable):
        """Add a message consumer for a queue"""
        self.callbacks[queue_name] = callback
        
        def wrapper(ch, method, properties, body):
            try:
                message = json.loads(body.decode('utf-8'))
                logging.info(f"Received message from {queue_name}: {message}")
                
                # Call the user-defined callback
                result = callback(message)
                
                # Acknowledge message if processed successfully
                if result is not False:  # Allow None or True as success
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    # Reject and requeue if callback returns False
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    
            except Exception as e:
                logging.error(f"Error processing message from {queue_name}: {e}")
                # Reject and requeue on error
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapper
        )
    
    def start_consuming(self):
        """Start consuming messages in a separate thread"""
        if self.running:
            return
            
        self.running = True
        
        def consume():
            while self.running:
                try:
                    self.channel.start_consuming()
                except Exception as e:
                    logging.error(f"Consumer error: {e}")
                    if self.running:
                        self._reconnect()
                        # Re-setup consumers
                        for queue_name, callback in self.callbacks.items():
                            self.add_consumer(queue_name, callback)
        
        self.consumer_thread = threading.Thread(target=consume, daemon=True)
        self.consumer_thread.start()
        logging.info("Started message consumer thread")
    
    def stop_consuming(self):
        """Stop consuming messages"""
        self.running = False
        if self.channel:
            self.channel.stop_consuming()
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)
    
    def close(self):
        """Close connection"""
        self.stop_consuming()
        if self.connection and not self.connection.is_closed:
            self.connection.close()


# Message schemas
class RideMessage:
    """Standard ride message format"""
    
    @staticmethod
    def ride_created(ride_id: int, driver_id: int, pickup_location: Dict, 
                    dropoff_location: Dict, departure_time: str, max_passengers: int) -> Dict:
        return {
            'event_type': 'ride_created',
            'ride_id': ride_id,
            'driver_id': driver_id,
            'pickup_location': pickup_location,
            'dropoff_location': dropoff_location,
            'departure_time': departure_time,
            'max_passengers': max_passengers,
            'current_passengers': 0
        }
    
    @staticmethod
    def ride_updated(ride_id: int, status: str, current_passengers: int) -> Dict:
        return {
            'event_type': 'ride_updated',
            'ride_id': ride_id,
            'status': status,
            'current_passengers': current_passengers
        }
    
    @staticmethod
    def passenger_joined(ride_id: int, passenger_id: int) -> Dict:
        return {
            'event_type': 'passenger_joined',
            'ride_id': ride_id,
            'passenger_id': passenger_id
        }


class PaymentMessage:
    """Standard payment message format"""
    
    @staticmethod
    def payment_completed(payment_id: int, user_id: int, amount: float, ride_id: int) -> Dict:
        return {
            'event_type': 'payment_completed',
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'ride_id': ride_id
        }
    
    @staticmethod
    def payment_failed(payment_id: int, user_id: int, amount: float, reason: str) -> Dict:
        return {
            'event_type': 'payment_failed',
            'payment_id': payment_id,
            'user_id': user_id,
            'amount': amount,
            'reason': reason
        }


# Exchange and routing key constants
EXCHANGES = {
    'RIDES': 'carpool.rides',
    'PAYMENTS': 'carpool.payments',
    'USERS': 'carpool.users',
    'NOTIFICATIONS': 'carpool.notifications'
}

ROUTING_KEYS = {
    'RIDE_CREATED': 'ride.created',
    'RIDE_UPDATED': 'ride.updated', 
    'RIDE_CANCELLED': 'ride.cancelled',
    'PASSENGER_JOINED': 'passenger.joined',
    'PAYMENT_COMPLETED': 'payment.completed',
    'PAYMENT_FAILED': 'payment.failed',
    'USER_UPDATED': 'user.updated'
}

QUEUES = {
    'MATCHING_RIDES': 'matching.rides',
    'PAYMENTS_NOTIFICATIONS': 'payments.notifications',
    'USER_PAYMENT_UPDATES': 'users.payment_updates'
} 