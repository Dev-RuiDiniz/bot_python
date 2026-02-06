from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from bot.config.loader import InstanceConfig
from bot.core.exceptions import CriticalFail, Reason, SoftFail
from bot.flow.step_base import Step
from bot.runner import instance_runner


class FakeADBForRunner:
    stop_failures_left = 0

    def __init__(self, serial: str, adb_bin: str = "adb") -> None:
        self.serial = serial
        self.calls = []

    def connect(self) -> None:
        self.calls.append(("connect", ()))

    def stop_app(self, package: str) -> None:
        self.calls.append(("stop_app", (package,)))
        if FakeADBForRunner.stop_failures_left > 0:
            FakeADBForRunner.stop_failures_left -= 1
            raise RuntimeError("stop falhou")

    def start_app(self, package: str, activity: str) -> None:
        self.calls.append(("start_app", (package, activity)))

    def screencap(self, output_path: str) -> Path:
        self.calls.append(("screencap", (output_path,)))
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("mock", encoding="utf-8")
        return path


class FakeVision:
    def __init__(self, *args, **kwargs) -> None:
        pass


class FakeLogger:
    def __init__(self) -> None:
        self.messages = []

    def info(self, msg, *args):
        self.messages.append(("info", msg % args if args else msg))

    def warning(self, msg, *args):
        self.messages.append(("warning", msg % args if args else msg))

    def error(self, msg, *args):
        self.messages.append(("error", msg % args if args else msg))

    def exception(self, msg, *args):
        self.messages.append(("exception", msg % args if args else msg))


class OkStep(Step):
    name = "ok_step"

    def run(self, context):
        return


class SoftStep(Step):
    name = "soft_step"

    def run(self, context):
        raise SoftFail("falha leve")


class CriticalVPNErrorStep(Step):
    name = "critical_vpn_step"

    def run(self, context):
        raise CriticalFail("vpn erro", reason=Reason.VPN_ERROR)


class RunnerDay7Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.instance = InstanceConfig("inst_test", "serial", "com.game", ".Main")
        self.bot_config = {
            "logs_dir": self.tmp.name,
            "breaker": {"softfails": 99, "criticals": 1},
            "shutdown_retries": 3,
            "shutdown_retry_delay_s": 0,
            "chrome_package": "com.android.chrome",
            "vpn_package": "com.vpn.app",
        }
        self._orig_adb = instance_runner.ADBClient
        self._orig_vision = instance_runner.Vision
        self._orig_steps = instance_runner.default_steps
        self._orig_logger = instance_runner.setup_instance_logger
        self.fake_logger = FakeLogger()
        instance_runner.ADBClient = FakeADBForRunner
        instance_runner.Vision = FakeVision
        instance_runner.setup_instance_logger = lambda *a, **k: self.fake_logger

    def tearDown(self) -> None:
        instance_runner.ADBClient = self._orig_adb
        instance_runner.Vision = self._orig_vision
        instance_runner.default_steps = self._orig_steps
        instance_runner.setup_instance_logger = self._orig_logger
        self.tmp.cleanup()

    def test_reasons_count_aggregates_and_vpn_error(self) -> None:
        instance_runner.default_steps = lambda: [SoftStep(), CriticalVPNErrorStep()]
        code = instance_runner.run_instance(self.instance, self.bot_config)
        self.assertEqual(code, 2)
        summary = [m for lvl, m in self.fake_logger.messages if "Resumo final" in m][-1]
        self.assertIn("Reason.UNKNOWN", summary)
        self.assertIn("Reason.VPN_ERROR", summary)

    def test_safe_shutdown_retries_until_success(self) -> None:
        instance_runner.default_steps = lambda: [OkStep()]
        FakeADBForRunner.stop_failures_left = 2
        code = instance_runner.run_instance(self.instance, self.bot_config)
        self.assertEqual(code, 0)
        warnings = [m for lvl, m in self.fake_logger.messages if lvl == "warning" and "Safe shutdown" in m]
        self.assertEqual(len(warnings), 2)

    def test_full_pipeline_fake_01_to_10_finished(self) -> None:
        class PipelineStep(Step):
            def __init__(self, name: str):
                self.name = name

            def run(self, context):
                if self.name == "step_10_finalize":
                    context.metrics["finished"] = True

        instance_runner.default_steps = lambda: [PipelineStep(f"step_{i:02d}") for i in range(1, 10)] + [PipelineStep("step_10_finalize")]
        code = instance_runner.run_instance(self.instance, self.bot_config)
        self.assertEqual(code, 0)
        summary = [m for lvl, m in self.fake_logger.messages if "Resumo final" in m][-1]
        self.assertIn("finished=True", summary)


if __name__ == "__main__":
    unittest.main()
