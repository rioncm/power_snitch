#!/usr/bin/env python3
"""
Power Snitch UPS Utilities
Handles UPS monitoring and management functions.
"""

import subprocess
import json
import logging
from datetime import datetime
from web.models.ups import UPS, BatteryHistory, UPSConfig
from web.utils.notifications import send_ups_alert

# Configure logging
logger = logging.getLogger(__name__)

def get_ups_status():
    """Get current UPS status using NUT."""
    try:
        # Get UPS configuration
        config = UPSConfig.get_config()
        if not config:
            error_msg = 'UPS configuration not found'
            logger.error(error_msg)
            send_ups_alert('critical', error_msg)
            return None

        # Run upsc command to get status
        result = subprocess.run(
            ['upsc', config.nut_device_name],
            capture_output=True,
            text=True,
            timeout=10  # Add timeout to prevent hanging
        )
        
        if result.returncode != 0:
            error_msg = f'Failed to get UPS status: {result.stderr}'
            logger.error(error_msg)
            send_ups_alert('critical', error_msg)
            return None
        
        # Parse the output
        status = {}
        for line in result.stdout.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                status[key.strip()] = value.strip()
        
        logger.debug(f"Retrieved UPS status: {json.dumps(status, indent=2)}")
        return status
    except subprocess.TimeoutExpired:
        error_msg = 'UPS status check timed out'
        logger.error(error_msg)
        send_ups_alert('critical', error_msg)
        return None
    except Exception as e:
        error_msg = f'Error getting UPS status: {str(e)}'
        logger.error(error_msg)
        send_ups_alert('critical', error_msg)
        return None

def update_ups_status():
    """Update UPS status in the database."""
    status = get_ups_status()
    if not status:
        return None
    
    try:
        # Get or create UPS record
        ups = UPS.get_current_status()
        if not ups:
            ups = UPS(name=status.get('device.model', 'Unknown UPS'))
            ups.save()
            logger.info(f"Created new UPS record: {ups.name}")
        
        # Update status with safe type conversion
        ups.update_status({
            'status': status.get('ups.status'),
            'battery_charge': safe_float_to_int(status.get('battery.charge', 0)),
            'battery_runtime': safe_float_to_int(status.get('battery.runtime', 0)),
            'input_voltage': safe_float(status.get('input.voltage', 0)),
            'output_voltage': safe_float(status.get('output.voltage', 0)),
            'load': safe_float_to_int(status.get('ups.load', 0))
        })
        logger.info("Updated UPS status successfully")
        
        # Record battery history
        history = BatteryHistory(
            ups_id=ups.id,
            battery_charge=ups.battery_charge,
            battery_runtime=ups.battery_runtime,
            status=ups.status
        )
        history.save()
        logger.debug("Recorded battery history")
        
        # Check for alerts
        check_ups_alerts(ups)
        
        return ups
    except Exception as e:
        error_msg = f'Error updating UPS status: {str(e)}'
        logger.error(error_msg)
        send_ups_alert('critical', error_msg)
        return None

def check_ups_alerts(ups):
    """Check UPS status and send alerts if needed."""
    try:
        # Check battery charge
        if ups.battery_charge is not None:
            if ups.battery_charge <= ups.critical_battery_threshold:
                send_ups_alert('critical', f'Critical battery level: {ups.battery_charge}%')
            elif ups.battery_charge <= ups.low_battery_threshold:
                send_ups_alert('warning', f'Low battery level: {ups.battery_charge}%')
        
        # Check battery runtime
        if ups.battery_runtime is not None and ups.battery_runtime <= ups.battery_runtime_threshold:
            runtime = format_battery_runtime(ups.battery_runtime)
            send_ups_alert('warning', f'Low battery runtime: {runtime}')
        
        # Check status
        if ups.status:
            if ups.status == 'OB':  # On Battery
                send_ups_alert('warning', 'UPS is running on battery power')
            elif ups.status == 'OL':  # On Line
                send_ups_alert('info', 'UPS is back on line power')
            elif ups.status == 'LB':  # Low Battery
                send_ups_alert('critical', 'UPS battery is low')
    except Exception as e:
        logger.error(f'Error checking UPS alerts: {str(e)}')

def get_battery_history(limit=24):
    """Get battery history entries."""
    try:
        ups = UPS.get_current_status()
        if not ups:
            logger.warning("No UPS record found for battery history")
            return []
        return ups.get_battery_history(limit=limit)
    except Exception as e:
        logger.error(f'Error getting battery history: {str(e)}')
        return []

def format_battery_runtime(seconds):
    """Format battery runtime in a human-readable format."""
    try:
        if not isinstance(seconds, (int, float)):
            return 'unknown'
        
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f'{hours}h {minutes}m {seconds}s'
        elif minutes > 0:
            return f'{minutes}m {seconds}s'
        else:
            return f'{seconds}s'
    except Exception as e:
        logger.error(f'Error formatting battery runtime: {str(e)}')
        return 'unknown'

def safe_float(value, default=0.0):
    """Safely convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_float_to_int(value, default=0):
    """Safely convert float string to integer."""
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default 