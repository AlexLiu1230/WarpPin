"""Tunnel 管理 — 用 subprocess 啟動 pymobiledevice3 tunnel"""

import subprocess
import shutil
import signal
import time
import logging
import os

logger = logging.getLogger(__name__)


def _find_python():
    """找到系統的 Python（不是打包後的）"""
    # 常見路徑
    candidates = [
        "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3",
        "/Library/Frameworks/Python.framework/Versions/3.13/bin/python3.13",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p

    # 用 which 找
    result = shutil.which("python3")
    if result:
        return result

    return "python3"


def _find_sudo():
    return shutil.which("sudo") or "/usr/bin/sudo"


class TunnelManager:
    def __init__(self):
        self._proc = None
        self.address = None
        self.port = None

    @property
    def is_running(self):
        return self._proc is not None and self._proc.poll() is None

    def start(self, timeout=15):
        """啟動 tunnel，回傳 (address, port)"""
        if self.is_running:
            return self.address, self.port

        logger.info("正在建立 tunnel...")

        python_path = _find_python()
        is_root = os.geteuid() == 0

        cmd = [
            python_path, "-m", "pymobiledevice3",
            "lockdown", "start-tunnel", "--script-mode",
        ]

        env = {**os.environ}

        if not is_root:
            askpass = self._create_askpass_script()
            env["SUDO_ASKPASS"] = askpass
            cmd = [_find_sudo(), "--askpass"] + cmd

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
        """macOS 密碼輸入對話框"""
        import tempfile
        script = tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False, prefix="warppin_askpass_"
        )
        script.write('#!/bin/bash\n'
            'osascript -e \'Tell application "System Events" to display dialog '
            '"WarpPin 需要管理者權限來建立裝置連線" default answer "" '
            'with hidden answer with title "WarpPin" '
            'buttons {"取消","確定"} default button "確定"\' '
            '-e \'text returned of result\' 2>/dev/null\n')
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
