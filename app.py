"""WarpPin — 啟動入口"""

import threading
import time
import sys
import os
import traceback

# 確保能找到 backend 模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

# 全域標記，防止無限重啟
_server_started = False
_server_error = None


def start_server():
    """在背景 thread 啟動 FastAPI server"""
    global _server_started, _server_error
    try:
        import uvicorn
        from backend.main import app
        _server_started = True
        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="warning")
    except Exception as e:
        _server_error = str(e)
        _server_started = False


def on_closing():
    """視窗關閉時清理"""
    try:
        from backend.main import tunnel, location
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

        asyncio.run(cleanup())
    except Exception:
        pass

    # 確保程式完全退出
    os._exit(0)


def main():
    try:
        import webview
    except ImportError:
        print("缺少 pywebview，請執行: pip3 install pywebview")
        sys.exit(1)

    # 啟動 server thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等 server 起來（最多 15 秒）
    for i in range(30):
        time.sleep(0.5)
        if _server_error:
            # server 啟動失敗，顯示錯誤視窗
            window = webview.create_window(
                "WarpPin - 錯誤",
                html=f"""
                <html><body style="font-family:system-ui;padding:40px;background:#1e1e1e;color:#e0e0e0;">
                <h2>WarpPin 啟動失敗</h2>
                <p style="color:#ff453a;">{_server_error}</p>
                <p style="color:#888;margin-top:20px;">請確認：</p>
                <ul style="color:#888;">
                <li>iPhone 已用 USB 接上 Mac</li>
                <li>iPhone 已解鎖並信任此電腦</li>
                <li>Developer Mode 已開啟</li>
                </ul>
                </body></html>
                """,
                width=500,
                height=400,
            )
            webview.start()
            os._exit(1)
            return

        if _server_started:
            # 再等一下讓 server 完全就緒
            time.sleep(1)
            break
    else:
        # 超時
        print("Server 啟動逾時")
        os._exit(1)
        return

    # 啟動 pywebview 視窗
    window = webview.create_window(
        "WarpPin",
        f"http://{SERVER_HOST}:{SERVER_PORT}",
        width=1200,
        height=800,
        min_size=(900, 600),
    )

    window.events.closing += on_closing

    # 啟動 GUI（block 直到視窗關閉）
    webview.start()

    # 視窗關閉後確保退出
    os._exit(0)


if __name__ == "__main__":
    main()
