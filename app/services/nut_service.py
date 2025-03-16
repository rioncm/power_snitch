#!/usr/bin/env python3
"""
NUT Service Module
Handles all NUT-related operations including configuration, validation, and monitoring.
"""

import os
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/power_snitch/nut_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NUTService:
    """Service class for managing NUT configuration and operations."""
    
    # NUT variable mappings to our database fields
    UPS_INFO_VARS = {
        'manufacturer': 'device.mfr',
        'model': 'device.model',
        'battery_type': 'battery.type',
        'serial_number': 'ups.serial',
        'firmware': 'ups.firmware',
        'driver': 'driver.name'
    }
    
    UPS_STATUS_VARS = {
        'status': 'ups.status',
        'battery_charge': 'battery.charge',
        'estimated_runtime': 'battery.runtime',
        'load': 'ups.load',
        'input_voltage': 'input.voltage',
        'output_voltage': 'output.voltage'
    }
    
    def __init__(self):
        """Initialize NUT service with default configuration paths."""
        self.nut_conf_dir = '/etc/nut'
        self.ups_conf = os.path.join(self.nut_conf_dir, 'ups.conf')
        self.upsd_conf = os.path.join(self.nut_conf_dir, 'upsd.conf')
        self.upsd_users = os.path.join(self.nut_conf_dir, 'upsd.users')
        self.connection = None
        logger.debug("NUTService initialized with configuration paths")
    
    def get_ups_info(self) -> Optional[Dict]:
        """
        Get static UPS information.
        
        Returns:
            Optional[Dict]: Dictionary containing UPS information or None if error
        """
        logger.debug("Getting UPS information")
        try:
            result = subprocess.run(
                ['upsc', 'ups@localhost'],
                capture_output=True,
                text=True,
                check=True
            )
            
            info = {}
            for line in result.stdout.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Map NUT variables to our database fields
                    for db_field, nut_var in self.UPS_INFO_VARS.items():
                        if key == nut_var:
                            info[db_field] = value
            
            logger.debug(f"UPS information retrieved: {info}")
            return info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting UPS information: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting UPS information: {str(e)}")
            return None
    
    def get_ups_status(self) -> Optional[Dict]:
        """
        Get current UPS status.
        
        Returns:
            Optional[Dict]: Dictionary containing UPS status or None if error
        """
        logger.debug("Getting UPS status")
        try:
            result = subprocess.run(
                ['upsc', 'ups@localhost'],
                capture_output=True,
                text=True,
                check=True
            )
            
            status = {}
            for line in result.stdout.splitlines():
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Map NUT variables to our database fields
                    for db_field, nut_var in self.UPS_STATUS_VARS.items():
                        if key == nut_var:
                            # Convert numeric values
                            if db_field in ['battery_charge', 'load', 'input_voltage', 'output_voltage']:
                                try:
                                    status[db_field] = float(value)
                                except ValueError:
                                    status[db_field] = 0.0
                            elif db_field == 'estimated_runtime':
                                try:
                                    status[db_field] = int(value)
                                except ValueError:
                                    status[db_field] = 0
                            else:
                                status[db_field] = value
            
            logger.debug(f"UPS status retrieved: {status}")
            return status
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting UPS status: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting UPS status: {str(e)}")
            return None
    
    def validate_config_files(self) -> Tuple[bool, List[str]]:
        """
        Validate NUT configuration files.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, error_messages)
        """
        errors = []
        logger.debug("Starting NUT configuration validation")
        
        # Check if configuration files exist
        for file_path in [self.ups_conf, self.upsd_conf, self.upsd_users]:
            if not os.path.exists(file_path):
                error_msg = f"Configuration file not found: {file_path}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        if errors:
            return False, errors
            
        # Validate ups.conf
        try:
            with open(self.ups_conf, 'r') as f:
                content = f.read()
                if '[ups]' not in content:
                    error_msg = "No UPS configuration found in ups.conf"
                    logger.error(error_msg)
                    errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error reading ups.conf: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Validate upsd.conf
        try:
            with open(self.upsd_conf, 'r') as f:
                content = f.read()
                if 'LISTEN 127.0.0.1' not in content:
                    error_msg = "UPSD not configured to listen on localhost"
                    logger.error(error_msg)
                    errors.append(error_msg)
        except Exception as e:
            error_msg = f"Error reading upsd.conf: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        is_valid = len(errors) == 0
        if is_valid:
            logger.info("NUT configuration validation successful")
        else:
            logger.error(f"NUT configuration validation failed with {len(errors)} errors")
        
        return is_valid, errors
    
    def update_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """
        Update NUT configuration files.
        
        Args:
            config (Dict): Configuration dictionary containing NUT settings
            
        Returns:
            Tuple[bool, List[str]]: (success, error_messages)
        """
        errors = []
        logger.debug(f"Starting NUT configuration update with settings: {config}")
        
        try:
            # Update ups.conf
            ups_conf_content = f"""[{config['device_name']}]
driver = {config['driver']}
port = {config['port']}
"""
            with open(self.ups_conf, 'w') as f:
                f.write(ups_conf_content)
            logger.debug("Updated ups.conf")
            
            # Update upsd.conf
            upsd_conf_content = """LISTEN 127.0.0.1 3493
MAXAGE 15
"""
            with open(self.upsd_conf, 'w') as f:
                f.write(upsd_conf_content)
            logger.debug("Updated upsd.conf")
            
            # Update upsd.users
            upsd_users_content = f"""[admin]
password = {config['password']}
actions = SET
instcmds = ALL
"""
            with open(self.upsd_users, 'w') as f:
                f.write(upsd_users_content)
            logger.debug("Updated upsd.users")
            
            # Set proper permissions
            for file_path in [self.ups_conf, self.upsd_conf, self.upsd_users]:
                os.chmod(file_path, 0o640)
            
            # Restart NUT services
            self._restart_services()
            
            logger.info("NUT configuration updated successfully")
            return True, []
            
        except Exception as e:
            error_msg = f"Error updating NUT configuration: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return False, errors
    
    def _restart_services(self) -> None:
        """Restart NUT services."""
        logger.debug("Restarting NUT services")
        try:
            subprocess.run(['systemctl', 'restart', 'nut-server'], check=True)
            subprocess.run(['systemctl', 'restart', 'nut-driver'], check=True)
            logger.info("NUT services restarted successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error restarting NUT services: {str(e)}")
            raise
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test NUT connection.
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        logger.debug("Testing NUT connection")
        try:
            result = subprocess.run(
                ['upsc', 'ups@localhost'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("NUT connection test successful")
            return True, "Connection successful"
        except subprocess.CalledProcessError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error during connection test: {str(e)}"
            logger.error(error_msg)
            return False, error_msg 