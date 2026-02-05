"""Domain exceptions for automation flow control."""


class BotError(Exception):
    """Base exception for bot runtime errors."""


class SoftFail(BotError):
    """Recoverable error for a single step."""


class CriticalFail(BotError):
    """Non-recoverable error for an instance run."""
