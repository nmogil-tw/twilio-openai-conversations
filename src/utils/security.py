"""
Security utilities for webhook validation, authentication, and data protection.
Provides functions for validating Twilio webhooks and securing sensitive data.
"""

import hashlib
import hmac
import base64
from typing import Dict, Any, Optional
from urllib.parse import quote

from config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


def validate_webhook_signature(
    request_body: str,
    signature: str,
    url: str,
    auth_token: Optional[str] = None
) -> bool:
    """
    Validate Twilio webhook signature for security.
    
    Twilio signs webhooks with HMAC-SHA1 using your auth token as the key.
    The signature is computed from the full URL (including query parameters)
    and the POST body.
    
    Args:
        request_body: Raw POST body as string
        signature: X-Twilio-Signature header value
        url: Full URL of the webhook endpoint
        auth_token: Twilio auth token (uses settings if not provided)
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        if not signature:
            logger.warning("No signature provided for webhook validation")
            return False
        
        # Use provided auth token or get from settings
        token = auth_token or settings.twilio.auth_token
        if not token:
            logger.warning("No auth token available for webhook validation")
            return False
        
        # Create the signature
        expected_signature = compute_twilio_signature(url, request_body, token)
        
        # Compare signatures using constant-time comparison
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        logger.error(f"Error validating webhook signature: {e}")
        return False


def compute_twilio_signature(url: str, body: str, auth_token: str) -> str:
    """
    Compute Twilio webhook signature.
    
    The signature is computed as:
    1. Sort the POST parameters by key (if body is form-encoded)
    2. Concatenate the full URL and parameters
    3. Compute HMAC-SHA1 with auth token as key
    4. Base64 encode the result
    
    Args:
        url: Full webhook URL
        body: POST body
        auth_token: Twilio auth token
        
    Returns:
        Base64-encoded HMAC-SHA1 signature
    """
    try:
        # Parse POST parameters if body is form-encoded
        params = ""
        if body and "=" in body:
            # Parse form data
            pairs = []
            for pair in body.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    pairs.append((key, value))
            
            # Sort by key and reconstruct
            pairs.sort(key=lambda x: x[0])
            params = "".join(f"{key}{value}" for key, value in pairs)
        
        # Create the string to sign
        data_to_sign = url + params
        
        # Compute HMAC-SHA1
        signature = hmac.new(
            auth_token.encode('utf-8'),
            data_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Base64 encode
        return base64.b64encode(signature).decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error computing Twilio signature: {e}")
        return ""


def sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize data for logging by removing or masking sensitive information.
    
    Args:
        data: Dictionary of data to sanitize
        
    Returns:
        Sanitized dictionary safe for logging
    """
    sensitive_keys = {
        'password', 'passwd', 'pwd',
        'token', 'auth_token', 'access_token', 'refresh_token',
        'key', 'api_key', 'secret', 'secret_key',
        'credential', 'credentials',
        'authorization', 'auth',
        'ssn', 'social_security_number',
        'credit_card', 'cc_number', 'card_number',
        'phone', 'phone_number', 'mobile',
        'email', 'email_address',
        'address', 'street_address',
        'account_sid', 'auth_token'  # Twilio-specific
    }
    
    def sanitize_value(key: str, value: Any) -> Any:
        """Sanitize individual value based on key name."""
        key_lower = key.lower()
        
        # Check if key contains sensitive information
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            if isinstance(value, str):
                if len(value) <= 4:
                    return "[REDACTED]"
                else:
                    # Show first 2 and last 2 characters
                    return f"{value[:2]}...{value[-2:]}"
            else:
                return "[REDACTED]"
        
        # Truncate very long strings
        if isinstance(value, str) and len(value) > 200:
            return value[:197] + "..."
        
        return value
    
    def sanitize_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    sanitize_dict(item) if isinstance(item, dict) else sanitize_value(key, item)
                    for item in value
                ]
            else:
                result[key] = sanitize_value(key, value)
        return result
    
    try:
        return sanitize_dict(data)
    except Exception as e:
        logger.error(f"Error sanitizing log data: {e}")
        return {"error": "Failed to sanitize data"}


def mask_sensitive_string(value: str, show_chars: int = 4) -> str:
    """
    Mask sensitive string values for logging.
    
    Args:
        value: String value to mask
        show_chars: Number of characters to show at start and end
        
    Returns:
        Masked string
    """
    if not value or len(value) <= show_chars:
        return "[REDACTED]"
    
    if len(value) <= show_chars * 2:
        return "*" * len(value)
    
    show_each = show_chars // 2
    return f"{value[:show_each]}{'*' * (len(value) - show_chars)}{value[-show_each:]}"


def validate_conversation_sid(conversation_sid: str) -> bool:
    """
    Validate Twilio Conversation SID format.
    
    Args:
        conversation_sid: Conversation SID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        # Twilio Conversation SIDs start with 'CH' and are 34 characters long
        return (
            isinstance(conversation_sid, str) and
            conversation_sid.startswith('CH') and
            len(conversation_sid) == 34 and
            conversation_sid[2:].isalnum()
        )
    except Exception:
        return False


def validate_service_sid(service_sid: str) -> bool:
    """
    Validate Twilio Service SID format.
    
    Args:
        service_sid: Service SID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        # Twilio Service SIDs start with 'IS' and are 34 characters long
        return (
            isinstance(service_sid, str) and
            service_sid.startswith('IS') and
            len(service_sid) == 34 and
            service_sid[2:].isalnum()
        )
    except Exception:
        return False


def validate_message_sid(message_sid: str) -> bool:
    """
    Validate Twilio Message SID format.
    
    Args:
        message_sid: Message SID to validate
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        # Twilio Message SIDs start with 'IM' and are 34 characters long
        return (
            isinstance(message_sid, str) and
            message_sid.startswith('IM') and
            len(message_sid) == 34 and
            message_sid[2:].isalnum()
        )
    except Exception:
        return False


def rate_limit_key(
    identifier: str, 
    window: str = "minute", 
    prefix: str = "rate_limit"
) -> str:
    """
    Generate rate limiting key for Redis or other storage.
    
    Args:
        identifier: Unique identifier (IP, user ID, conversation SID, etc.)
        window: Time window ("minute", "hour", "day")
        prefix: Key prefix
        
    Returns:
        Rate limiting key
    """
    import datetime
    
    now = datetime.datetime.utcnow()
    
    if window == "minute":
        time_key = now.strftime("%Y%m%d%H%M")
    elif window == "hour":
        time_key = now.strftime("%Y%m%d%H")
    elif window == "day":
        time_key = now.strftime("%Y%m%d")
    else:
        raise ValueError(f"Invalid window: {window}")
    
    # Hash the identifier to prevent key enumeration
    identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()[:16]
    
    return f"{prefix}:{window}:{time_key}:{identifier_hash}"


def is_safe_redirect_url(url: str, allowed_hosts: Optional[list] = None) -> bool:
    """
    Check if a redirect URL is safe (prevents open redirect vulnerabilities).
    
    Args:
        url: URL to validate
        allowed_hosts: List of allowed host names (optional)
        
    Returns:
        True if URL is safe for redirect, False otherwise
    """
    try:
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        
        # Relative URLs are generally safe
        if not parsed.netloc:
            return True
        
        # Check allowed hosts if provided
        if allowed_hosts:
            return parsed.netloc.lower() in [host.lower() for host in allowed_hosts]
        
        # Default: only allow same-origin redirects
        return False
        
    except Exception:
        return False


def generate_session_token() -> str:
    """
    Generate a secure session token.
    
    Returns:
        Base64-encoded random token
    """
    import secrets
    
    # Generate 32 random bytes and encode as base64
    token_bytes = secrets.token_bytes(32)
    return base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')


def hash_password(password: str, salt: Optional[str] = None) -> tuple:
    """
    Hash a password using PBKDF2 with SHA-256.
    
    Args:
        password: Plain text password
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    import secrets
    
    if salt is None:
        salt = secrets.token_hex(16)
    elif isinstance(salt, str):
        salt = salt.encode('utf-8')
    
    # Use PBKDF2 with 100,000 iterations
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt if isinstance(salt, bytes) else salt.encode('utf-8'),
        100000
    )
    
    return base64.b64encode(hashed).decode('utf-8'), salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Base64-encoded hashed password
        salt: Password salt
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        expected_hash, _ = hash_password(password, salt)
        return hmac.compare_digest(expected_hash, hashed_password)
    except Exception:
        return False