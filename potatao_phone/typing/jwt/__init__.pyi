"""
Custom JWT HS256 Module for MicroPython (Pico 2)
Provides hardware-accelerated JWT token creation and verification using mbedTLS.
"""

from typing import Union

def create_token(payload: str, secret_key: str) -> str:
    """
    Creates a signed JWT (JSON Web Token) using the HS256 algorithm.

    Args:
        payload: The JSON string or message data to sign.
        secret_key: The symmetric key used for HMAC-SHA256 signature calculation.

    Returns:
        A three-part Base64URL-encoded JWT string (header.payload.signature).
    """
    ...

def verify_token(token: str, secret_key: str) -> str:
    """
    Verifies a JWT's signature and decodes the payload if valid.

    Args:
        token: The full string token to check (header.payload.signature).
        secret_key: The symmetric key used to verify the HMAC-SHA256 signature.

    Returns:
        The decrypted payload text string on success. 
        On failure, returns an error description string starting with 'Invalid JWT', 
        'Signature verification failed', or 'ERROR: Base64URL decoding'.
    """
    ...

def error_string(status: int) -> str:
    """
    Retrieves the system message string corresponding to an internal JWT error code.

    Args:
        status: The numerical integer error code.

    Returns:
        The corresponding descriptive error message string.
    """
    ...