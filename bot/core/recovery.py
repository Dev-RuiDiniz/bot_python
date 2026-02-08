class RecoveryManager:
    def __init__(self, adb):
        self.adb = adb

    def handle(self, reasons: list[str]) -> bool:
        if not reasons:
            return False

        # prioridade explícita
        if "vpn_error" in reasons:
            self.adb.stop_app("vpn")
            self.adb.start_app("vpn", "Main")
            return True

        return False
