import bcrypt
import jwt
import secrets
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from app.config import settings


class SecurityError(Exception):
    """Base exception for authentication and token validation errors."""
    pass


class TokenExpiredError(SecurityError):
    """Raised when an access token has expired."""
    pass


class TokenInvalidError(SecurityError):
    """Raised when an access token signature or payload is invalid."""
    pass


def hash_password(password: str) -> str:
    """
    Hash a plain-text password securely using bcrypt with auto-generated salt.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token containing arbitrary payload data.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": now,
        "exp": expire,
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token's signature and expiration.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise TokenExpiredError("Access token has expired") from e
    except (jwt.InvalidTokenError, jwt.PyJWTError) as e:
        raise TokenInvalidError("Invalid access token") from e


PREFIX_WORDS = [
    "Solar", "Power", "Volt", "Watt", "Panel", "Amber", "Bright", "Ray",
    "Spark", "Peak", "Energy", "Lumen", "Photon", "Sky", "Clean", "Helios",
    "Aurora", "Zenith", "Prism", "Beacon", "River", "Summit", "Haven",
    "Breeze", "Cedar", "Orbit", "Optic", "Nova", "Pulse", "Onyx",
]

SUFFIX_WORDS = [
    "Sun", "Grid", "Volt", "Watt", "Ray", "Beam", "Star", "Flow",
    "Core", "Peak", "Base", "Link", "Wave", "Nova", "Dawn", "Sky",
    "Glow", "Spark", "Pure", "Rise", "Zone", "Hub", "Line", "Gate",
]

SEPARATORS = ["@", "#", "$", "!", "%", "&"]


def generate_human_friendly_password() -> str:
    """
    Generate a cryptographically secure, human-friendly temporary password.
    Format: <PrefixWord><Separator><4Digits><SuffixWord>
    Example: Solar@4821Sun, Volt#7392Peak
    Satisfies complexity requirements:
    - Uppercase and lowercase letters
    - Numbers (4 digits)
    - Special characters (@, #, $, !, %, &)
    - Length >= 12 characters (exceeds min 8 chars requirement)
    - Easy to read, remember, and communicate
    """
    prefix = secrets.choice(PREFIX_WORDS)
    separator = secrets.choice(SEPARATORS)
    digits = f"{secrets.randbelow(9000) + 1000}"  # 1000 - 9999
    suffix = secrets.choice(SUFFIX_WORDS)
    while suffix.lower() == prefix.lower():
        suffix = secrets.choice(SUFFIX_WORDS)
    return f"{prefix}{separator}{digits}{suffix}"


def normalize_name_for_email(name: str) -> str:
    """
    Normalize a name component for email address generation:
    - Lowercase
    - Strip diacritics / accents (e.g. é -> e)
    - Remove all non-alphanumeric characters (spaces, hyphens, apostrophes, etc.)
    """
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name.strip())
    ascii_text = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r"[^a-z0-9]", "", ascii_text.lower())


def generate_unique_work_email(
    db: Any,
    first_name: str,
    last_name: str,
    domain: Optional[str] = None,
) -> str:
    """
    Generate a professional work email in the format:
    firstname.lastname@domain
    If duplicate exists, append incremental numeric suffix:
    firstname.lastname2@domain, firstname.lastname3@domain, etc.
    """
    from sqlalchemy import select, func
    from app.models.auth import User

    if not domain:
        domain = getattr(settings, "COMPANY_EMAIL_DOMAIN", "sunpower.com")
        if getattr(settings, "COMPANY_EMAIL", None):
            parts = settings.COMPANY_EMAIL.split("@")
            if len(parts) == 2 and parts[1].strip():
                domain = parts[1].strip()

    fn = normalize_name_for_email(first_name)
    ln = normalize_name_for_email(last_name)

    if fn and ln:
        base_prefix = f"{fn}.{ln}"
    elif fn:
        base_prefix = fn
    elif ln:
        base_prefix = ln
    else:
        base_prefix = "employee"

    candidate = f"{base_prefix}@{domain}"

    # Check if base candidate already exists in database
    existing = db.execute(
        select(User.id).where(func.lower(User.email) == candidate.lower())
    ).scalar_one_or_none()
    if not existing:
        return candidate

    # Incremental duplicate resolution: 2, 3, 4, ...
    counter = 2
    while True:
        candidate = f"{base_prefix}{counter}@{domain}"
        existing = db.execute(
            select(User.id).where(func.lower(User.email) == candidate.lower())
        ).scalar_one_or_none()
        if not existing:
            return candidate
        counter += 1


