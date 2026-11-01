import subprocess
import unittest
from unittest.mock import patch

from manguito.system_info import get_system_info


class SystemInfoTests(unittest.TestCase):
    @patch("manguito.system_info.subprocess.run")
    def test_gpu_telemetry(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["nvidia-smi"], returncode=0,
            stdout="NVIDIA GeForce RTX 5060, 37, 1205, 8192, 52\n",
            stderr="",
        )
        data = get_system_info()
        self.assertEqual(data["gpu"]["utilization_percent"], 37)
        self.assertEqual(data["gpu"]["memory_used_mb"], 1205)
        self.assertEqual(data["gpu"]["memory_total_mb"], 8192)
        self.assertEqual(data["gpu"]["temperature_celsius"], 52)
        self.assertFalse(run.call_args.kwargs["shell"])

    @patch("manguito.system_info.subprocess.run", side_effect=FileNotFoundError)
    def test_not_installed(self, run):
        self.assertIsNone(get_system_info()["gpu"])

    @patch("manguito.system_info.subprocess.run")
    def test_bad_result_does_not_crash(self, run):
        run.return_value = subprocess.CompletedProcess(
            args=["nvidia-smi"], returncode=1, stdout="", stderr="no GPU"
        )
        self.assertIsNone(get_system_info()["gpu"])


if __name__ == "__main__":
    unittest.main()
