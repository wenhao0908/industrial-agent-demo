import json
import subprocess
import sys
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).parents[1]


class DemoSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen(
            [sys.executable, "app.py"], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            try:
                with urlopen("http://127.0.0.1:8000/health", timeout=0.3) as response:
                    if response.status == 200:
                        return
            except OSError:
                time.sleep(0.1)
        raise RuntimeError("demo server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        cls.proc.wait(timeout=3)

    def test_health(self):
        with urlopen("http://127.0.0.1:8000/health") as response:
            self.assertEqual(json.load(response)["status"], "ok")

    def test_investigation_contains_safety_boundary(self):
        payload = json.dumps({
            "question": "设备 SN:DVT-24017 在真空调试时触发 ALM-217，请分析根因。"
        }).encode("utf-8")
        request = Request(
            "http://127.0.0.1:8000/api/investigate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request) as response:
            result = json.load(response)
        self.assertEqual(len(result["tools"]), 4)
        self.assertEqual(result["metrics"]["tool_success"], "4/4")
        self.assertEqual(result["approval"]["status"], "draft")
        self.assertTrue(any(r["result"] == "需人工确认" for r in result["rules"]))


if __name__ == "__main__":
    unittest.main()
