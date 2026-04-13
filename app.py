"""WarpPin — 啟動入口"""

import threading
import time
import signal
import sys
import os

# 確保能找到 backend 模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
import webview

from backend.main import app, tunnel, location

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


def start_server():
    """在背景 thread 啟動 FastAPI server"""
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="warning")


def on_closing():
    """視窗關閉時清理"""
    import asyncio

    async def cleanup():
        if location.is_spoofing:
            try:
                await location.clear_location()
            except Exception:
                pass
        try:
            await location.disconnect()
        except Exception:
            pass
        tunnel.stop()

    try:
        asyncio.run(cleanup())
    except Exception:
        pass


def main():
    # 啟動 server thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等 server 起來
    time.sleep(2)

    # 啟動 pywebview 視窗
    window = webview.create_window(
        "WarpPin",
        f"http://{SERVER_HOST}:{SERVER_PORT}",
        width=1200,
        height=800,
        min_size=(900, 600),
    )

    # 視窗關閉事件
    window.events.closing += on_closing

    # 啟動 GUI（會 block 直到視窗關閉）
    webview.start()


if __name__ == "__main__":
    main()
