"""Tunnel 管理 — 自動啟動/關閉 pymobiledevice3 tunnel"""

import subprocess
import sys
import signal
import time
import logging

logger = logging.getLogger(__name__)


class TunnelManager:
    def __init__(self):
        self._proc = None
        self.address = None
        self.port = None

    @property
    def is_running(self):
        return self._proc is not None and self._proc.poll() is None

    def start(self, timeout=30):
        """啟動 tunnel，回傳 (address, port)"""
        if self.is_running:
            return self.address, self.port

        logger.info("正在建立 tunnel...")

        self._proc = subprocess.Popen(
            [
                sys.executable, "-m", "pymobiledevice3",
                "lockdown", "start-tunnel", "--script-mode",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._proc.stdout.readline().decode().strip()
            if line:
                parts = line.split()
                if len(parts) == 2:
                    self.address = parts[0]
                    self.port = int(parts[1])
                    logger.info(f"Tunnel 建立成功：{self.address}:{self.port}")
                    return self.address, self.port

            if self._proc.poll() is not None:
                err = self._proc.stderr.read().decode()
                raise RuntimeError(f"Tunnel 啟動失敗：{err}")

            time.sleep(0.5)

        self._proc.kill()
        raise TimeoutError("Tunnel 啟動逾時")

    def stop(self):
        """關閉 tunnel"""
        if self._proc and self._proc.poll() is None:
            self._proc.send_signal(signal.SIGTERM)
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
            logger.info("Tunnel 已關閉")

        self._proc = None
        self.address = None
        self.port = None
