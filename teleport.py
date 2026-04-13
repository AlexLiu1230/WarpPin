"""WarpPin Phase 1 - Step 3: 自動化 tunnel + 傳送定位"""

import asyncio
import subprocess
import sys
import signal
import time

from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider

# 東京鐵塔
LAT = 35.6586
LNG = 139.7454


def start_tunnel():
    """在背景啟動 tunnel，自動取得 address 和 port"""
    print("正在建立 tunnel（需要 sudo 權限）...")

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "pymobiledevice3",
            "lockdown", "start-tunnel", "--script-mode",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=None,
    )

    # 等待 tunnel 輸出 address 和 port
    # script mode 會印出一行：address port
    deadline = time.time() + 30
    while time.time() < deadline:
        line = proc.stdout.readline().decode().strip()
        if line:
            parts = line.split()
            if len(parts) == 2:
                address, port = parts[0], int(parts[1])
                print(f"Tunnel 建立成功！RSD {address}:{port}")
                return proc, address, port

        # 檢查 process 有沒有掛掉
        if proc.poll() is not None:
            err = proc.stderr.read().decode()
            print(f"Tunnel 啟動失敗：{err}")
            sys.exit(1)

        time.sleep(0.5)

    proc.kill()
    print("Tunnel 啟動逾時（30 秒）")
    sys.exit(1)


async def teleport(address, port, lat, lng):
    """傳送到指定座標"""
    rsd = RemoteServiceDiscoveryService((address, port))
    await rsd.connect()

    async with DvtProvider(rsd) as dvt:
        location = LocationSimulation(dvt)
        await location.connect()
        await location.set(lat, lng)
        print(f"\n已傳送到：{lat}, {lng}")
        print("打開 iPhone 的地圖 app 確認看看！")
        print("\n按 Enter 恢復真實定位...")
        input()

        await location.clear()
        print("已恢復真實定位")


def main():
    tunnel_proc = None
    try:
        tunnel_proc, address, port = start_tunnel()
        asyncio.run(teleport(address, port, LAT, LNG))
    finally:
        # 清理 tunnel process
        if tunnel_proc and tunnel_proc.poll() is None:
            tunnel_proc.send_signal(signal.SIGTERM)
            tunnel_proc.wait(timeout=5)
            print("Tunnel 已關閉")


if __name__ == "__main__":
    main()
