#!/usr/bin/env python3
"""
Power Snitch Notification Utilities
Handles sending notifications through various channels.
"""

import logging
from datetime import datetime
from web.models.alert import Alert
from web.models.notification import (
    get_webhook_config,
    get_email_config,
    get_sms_config
)

# Configure logging
logger = logging.getLogger(__name__)

def send_notification(level, message, source='system'):
    """Send a notification through all enabled channels."""
    if level not in ('info', 'warning', 'critical'):
        logger.error(f"Invalid notification level: {level}")
        level = 'info'  # Default to info for invalid levels
    
    if not message:
        logger.error("Empty notification message")
        return None
    
    try:
        # Create alert
        alert = Alert(level=level, message=message, source=source)
        alert.save()
        logger.info(f"Created {level} alert from {source}: {message}")
        
        # Prepare notification data
        data = {
            'type': 'alert',
            'level': level,
            'message': message,
            'source': source,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        notification_results = {'alert_id': alert.id, 'channels': {}}
        
        # Send through webhook
        webhook_config = get_webhook_config()
        if webhook_config and webhook_config.enabled:
            try:
                success = webhook_config.send_notification(data)
                notification_results['channels']['webhook'] = success
                if not success:
                    logger.warning("Failed to send webhook notification")
            except Exception as e:
                logger.error(f"Error sending webhook notification: {str(e)}")
                notification_results['channels']['webhook'] = False
        
        # Send through email
        email_config = get_email_config()
        if email_config and email_config.enabled:
            try:
                subject = f'Power Snitch Alert: {level.upper()}'
                body = f"""
Alert Level: {level.upper()}
Source: {source}
Message: {message}
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""
                success = email_config.send_notification(subject, body)
                notification_results['channels']['email'] = success
                if not success:
                    logger.warning("Failed to send email notification")
            except Exception as e:
                logger.error(f"Error sending email notification: {str(e)}")
                notification_results['channels']['email'] = False
        
        # Send through SMS
        sms_config = get_sms_config()
        if sms_config and sms_config.enabled:
            try:
                sms_message = f'Power Snitch Alert ({level.upper()}): {message}'
                success = sms_config.send_notification(sms_message)
                notification_results['channels']['sms'] = success
                if not success:
                    logger.warning("Failed to send SMS notification")
            except Exception as e:
                logger.error(f"Error sending SMS notification: {str(e)}")
                notification_results['channels']['sms'] = False
        
        return notification_results
    except Exception as e:
        logger.error(f"Error in send_notification: {str(e)}")
        return None

def send_ups_alert(level, message):
    """Send a UPS-related alert."""
    return send_notification(level, message, source='ups')

def send_system_alert(level, message):
    """Send a system-related alert."""
    return send_notification(level, message, source='system')

def send_notification_alert(level, message):
    """Send a notification-related alert."""
    return send_notification(level, message, source='notification')

def test_notifications():
    """Test all notification channels."""
    logger.info("Starting notification channel tests")
    results = {
        'webhook': False,
        'email': False,
        'sms': False
    }
    
    try:
        # Test webhook
        webhook_config = get_webhook_config()
        if webhook_config and webhook_config.enabled:
            results['webhook'] = webhook_config.test()
            logger.info(f"Webhook test {'successful' if results['webhook'] else 'failed'}")
        
        # Test email
        email_config = get_email_config()
        if email_config and email_config.enabled:
            results['email'] = email_config.test()
            logger.info(f"Email test {'successful' if results['email'] else 'failed'}")
        
        # Test SMS
        sms_config = get_sms_config()
        if sms_config and sms_config.enabled:
            results['sms'] = sms_config.test()
            logger.info(f"SMS test {'successful' if results['sms'] else 'failed'}")
        
        return results
    except Exception as e:
        logger.error(f"Error testing notifications: {str(e)}")
        return results 