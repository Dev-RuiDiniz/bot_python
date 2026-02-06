"""Domain exceptions for automation flow control."""

from __future__ import annotations

from enum import Enum


class Reason(str, Enum):
    """Reason codes padronizados para falhas soft/critical."""

    VPN_TIMEOUT = "VPN_TIMEOUT"
    VPN_ERROR = "VPN_ERROR"
    CAPTCHA_DETECTED = "CAPTCHA_DETECTED"
    BONUS_PAGE_NOT_FOUND = "BONUS_PAGE_NOT_FOUND"
    HOME_NOT_FOUND = "HOME_NOT_FOUND"
    UNKNOWN = "UNKNOWN"


class BotError(Exception):
    """Base exception for bot runtime errors."""

    def __init__(self, message: str, reason: Reason | str | None = None) -> None:
        self.message = message
        self.reason = Reason(reason) if reason is not None else Reason.UNKNOWN
        super().__init__(f"{self.reason}: {message}")


class SoftFail(BotError):
    """Recoverable error for a single step."""


class CriticalFail(BotError):
    """Non-recoverable error for an instance run."""
