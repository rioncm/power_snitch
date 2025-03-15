#!/usr/bin/env python3
"""
Power Snitch Authentication Utilities
Handles API key authentication for the single-user system.
"""

from functools import wraps
from flask import request, jsonify
from web.models.system import SystemSettings

def api_key_required(f):
    """Decorator to require API key for endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({
                'success': False,
                'message': 'API key is required'
            }), 401
        
        if not validate_api_key(api_key):
            return jsonify({
                'success': False,
                'message': 'Invalid API key'
            }), 401
        
        return f(*args, **kwargs)
    return decorated

def validate_api_key(api_key):
    """Validate an API key against system settings."""
    settings = SystemSettings.get_settings()
    if not settings or not settings.api_key:
        return False
    return api_key == settings.api_key

def is_authenticated():
    """Check if the request is authenticated via API key."""
    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return False
    return validate_api_key(api_key)

def require_auth(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_authenticated():
            return jsonify({
                'success': False,
                'message': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated

def is_admin():
    """Check if the current user is an admin."""
    return current_user.is_authenticated and current_user.is_admin

def require_admin(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            return jsonify({
                'success': False,
                'message': 'Admin privileges required'
            }), 403
        return f(*args, **kwargs)
    return decorated 