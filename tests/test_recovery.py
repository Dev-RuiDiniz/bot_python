import pytest

from bot.core.recovery import RecoveryManager
from bot.core.fake_adb import FakeADB


class TestRecoveryManager:

    def test_recovery_from_vpn_error(self):
        adb = FakeADB()
        recovery = RecoveryManager(adb)

        reasons = ["vpn_error"]

        result = recovery.handle(reasons)

        assert result is True
        assert adb.actions == [
            "disable_vpn",
            "enable_vpn",
            "retry"
        ]

    def test_recovery_from_unknown_error_fails_cleanly(self):
        adb = FakeADB()
        recovery = RecoveryManager(adb)

        reasons = ["alien_invasion"]

        result = recovery.handle(reasons)

        assert result is False
        assert adb.actions == []

    def test_recovery_with_multiple_errors_prioritizes_vpn(self):
        adb = FakeADB()
        recovery = RecoveryManager(adb)

        reasons = ["timeout", "vpn_error", "something_else"]

        result = recovery.handle(reasons)

        assert result is True
        assert adb.actions[0] == "disable_vpn"
