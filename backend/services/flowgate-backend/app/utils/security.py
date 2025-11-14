"""Security utilities for token hashing and generation"""

import secrets
import hashlib
from passlib.context import CryptContext
from typing import Optional

# Use bcrypt for hashing registration tokens
# Note: bcrypt has a 72-byte limit, so we hash the token's SHA256 digest instead
# Use bcryptrypt backend explicitly to avoid detection issues
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Force backend initialization
    pwd_context.hash("test")
except Exception:
    # Fallback to pbkdf2_sha256 if bcrypt fails
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_token(token: str) -> str:
    """
    Hash a registration token using bcrypt.
    Since bcrypt has a 72-byte limit, we hash the SHA256 digest of the token.
    """
    # Create a deterministic hash of the token that fits within bcrypt's limit
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    return pwd_context.hash(token_hash)


def verify_token(plain_token: str, hashed_token: str) -> bool:
    """
    Verify a registration token against its hash.
    We compare the SHA256 digest of the plain token with the stored hash.
    """
    token_hash = hashlib.sha256(plain_token.encode('utf-8')).hexdigest()
    return pwd_context.verify(token_hash, hashed_token)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    # Generate URL-safe token
    return secrets.token_urlsafe(length)

