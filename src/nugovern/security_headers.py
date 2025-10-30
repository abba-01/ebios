"""
security_headers.py

Security headers middleware for eBIOS API.

Implements OWASP recommended security headers:
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Content-Security-Policy
- Referrer-Policy
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Get HSTS configuration from environment
        hsts_enabled = os.getenv('SECURITY_HSTS_ENABLED', 'true').lower() == 'true'
        hsts_max_age = int(os.getenv('SECURITY_HSTS_MAX_AGE', '31536000'))  # 1 year default

        # HSTS: Force HTTPS
        if hsts_enabled:
            response.headers['Strict-Transport-Security'] = f'max-age={hsts_max_age}; includeSubDomains; preload'

        # X-Content-Type-Options: Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # X-Frame-Options: Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # X-XSS-Protection: Enable XSS filtering (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Content-Security-Policy: Restrict resource loading
        csp = os.getenv('SECURITY_CSP', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        response.headers['Content-Security-Policy'] = csp

        # Referrer-Policy: Control referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy: Control browser features
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

        return response
