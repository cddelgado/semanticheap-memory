"""Custom exceptions for semantic heap memory."""


class SemanticHeapError(Exception):
    """Base exception for semantic heap errors."""


class InvalidDomainError(SemanticHeapError):
    """Raised when a domain is invalid."""


class InvalidTemporalExpressionError(SemanticHeapError):
    """Raised when a temporal expression cannot be parsed."""
