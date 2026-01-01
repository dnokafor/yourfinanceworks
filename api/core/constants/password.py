"""
Password-related constants.
"""

# Minimum password length for all user creation and password reset operations
MIN_PASSWORD_LENGTH = 12

# Password complexity requirements
PASSWORD_COMPLEXITY = {
    "require_uppercase": True,
    "require_lowercase": True,
    "require_numbers": True,
    "require_special_chars": True,
    "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?"
}
