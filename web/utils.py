"""
Utility functions for the application
"""

from flask import request
from flask_wtf.csrf import validate_csrf


def validate_csrf_token():
    """Validate CSRF token from form data or headers"""
    try:
        # Try to get token from form data first
        token = request.form.get('csrf_token')
        if not token:
            # Try to get token from headers
            token = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')

        if token:
            validate_csrf(token)
            return True
        return False
    except Exception as e:
        print(f"CSRF validation error: {e}")
        return False
