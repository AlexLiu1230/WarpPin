"""Tunnel 管理 — 自動啟動/關閉 pymobiledevice3 tunnel"""

import subprocess
import sys
import signal
import time
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def _find_sudo():
    """找到 sudo 路徑"""
    return shutil.which("sudo") or "/usr/bin/sudo"


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

        # 檢查是否已經有 root 權限
        is_root = os.geteuid() == 0

        cmd = [
            sys.executable, "-m", "pymobiledevice3",
            "lockdown", "start-tunnel", "--script-mode",
        ]

        if not is_root:
            # 沒有 root 權限，用 sudo 提權
            # macOS 上如果是 GUI app，sudo 會透過系統提示要密碼
            cmd = [_find_sudo(), "--askpass"] + cmd

            # 設定 SUDO_ASKPASS 用 osascript 彈出密碼對話框
            askpass_script = self._create_askpass_script()
            env = {**os.environ, "SUDO_ASKPASS": askpass_script}
        else:
            env = None

        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
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

    def _create_askpass_script(self):
        """建立 macOS 密碼輸入腳本（osascript）"""
        import tempfile
        script = tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, prefix="warppin_askpass_"
        )
        script.write("""#!/bin/bash
osascript -e 'Tell application "System Events" to display dialog "WarpPin 需要管理者權限來建立裝置連線" default answer "" with hidden answer with title "WarpPin" buttons {"取消","確定"} default button "確定"' -e 'text returned of result' 2>/dev/null
""")
        script.close()
        os.chmod(script.name, 0o755)
        return script.name

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
