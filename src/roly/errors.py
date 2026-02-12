"""Custom error types for Roly."""


class RolyError(Exception):
    """Base exception for user-facing Roly errors."""


class ConfigError(RolyError):
    """Raised when roly.config is missing or invalid."""


class RoleParseError(RolyError):
    """Raised when a role file cannot be parsed."""


class RoleNotFoundError(RolyError):
    """Raised when a requested role cannot be resolved."""


class ReviewApplyError(RolyError):
    """Raised when a review change cannot be applied safely."""
