#!/usr/bin/env python3
"""
Integration tests for NUT Service and Database interaction
"""

import os
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from services.nut_service import NUTService
from app.web.db import Database, UPSConfig

class TestNUTIntegration(unittest.TestCase):
    """Test cases for NUT service and database integration."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db = Database(self.temp_db.name)
        self.db.init_db()
        
        # Initialize NUT service
        self.nut_service = NUTService()
        
        # Test configuration
        self.test_config = {
            'device_name': 'test_ups',
            'driver': 'usbhid-ups',
            'port': 'auto',
            'password': 'test_password'
        }
    
    def tearDown(self):
        """Clean up test environment."""
        self.temp_db.close()
        os.unlink(self.temp_db.name)
    
    def test_config_sync(self):
        """Test synchronization between database and NUT configuration."""
        # Update database configuration
        self.db.update_ups_config(
            name='Test UPS',
            description='Test Description',
            nut_device_name='test_ups',
            nut_driver='usbhid-ups',
            nut_port='auto',
            nut_username='admin',
            nut_password='test_password'
        )
        
        # Get configuration from database
        db_config = self.db.get_ups_config()
        
        # Verify configuration matches
        self.assertEqual(db_config.nut_device_name, 'test_ups')
        self.assertEqual(db_config.nut_driver, 'usbhid-ups')
        self.assertEqual(db_config.nut_port, 'auto')
        self.assertEqual(db_config.nut_username, 'admin')
    
    @patch('services.nut_service.NUTService.update_config')
    def test_config_update_propagation(self, mock_update_config):
        """Test that database updates propagate to NUT configuration."""
        # Mock successful NUT configuration update
        mock_update_config.return_value = (True, [])
        
        # Update database configuration
        self.db.update_ups_config(
            nut_device_name='new_ups',
            nut_driver='new_driver'
        )
        
        # Verify NUT configuration was updated
        mock_update_config.assert_called_once()
        call_args = mock_update_config.call_args[0][0]
        self.assertEqual(call_args['device_name'], 'new_ups')
        self.assertEqual(call_args['driver'], 'new_driver')
    
    @patch('services.nut_service.NUTService.get_ups_status')
    def test_status_monitoring(self, mock_get_status):
        """Test UPS status monitoring integration."""
        # Mock UPS status
        mock_status = {
            'battery.charge': '100',
            'battery.runtime': '3600',
            'ups.status': 'OL'
        }
        mock_get_status.return_value = mock_status
        
        # Get status through NUT service
        status = self.nut_service.get_ups_status()
        
        # Verify status matches
        self.assertEqual(status['battery.charge'], '100')
        self.assertEqual(status['battery.runtime'], '3600')
        self.assertEqual(status['ups.status'], 'OL')
    
    @patch('services.nut_service.NUTService.test_connection')
    def test_connection_testing(self, mock_test_connection):
        """Test connection testing integration."""
        # Mock successful connection test
        mock_test_connection.return_value = (True, "Connection successful")
        
        # Test connection
        success, message = self.nut_service.test_connection()
        
        # Verify test results
        self.assertTrue(success)
        self.assertEqual(message, "Connection successful")
    
    def test_error_handling(self):
        """Test error handling in integration."""
        # Test invalid configuration
        with self.assertRaises(ValueError):
            self.db.update_ups_config(
                nut_device_name='',  # Invalid empty device name
                nut_driver=''  # Invalid empty driver
            )
        
        # Verify database wasn't updated
        db_config = self.db.get_ups_config()
        self.assertNotEqual(db_config.nut_device_name, '')
        self.assertNotEqual(db_config.nut_driver, '')

if __name__ == '__main__':
    unittest.main() 