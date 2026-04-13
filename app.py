"""WarpPin — 啟動入口"""

import threading
import time
import sys
import os

# PyInstaller 打包後的路徑處理
if getattr(sys, 'frozen', False):
    # 打包模式：資源在 sys._MEIPASS
    BASE_DIR = sys._MEIPASS
else:
    # 開發模式
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

# 設定環境變數讓 backend 也能找到正確路徑
os.environ["WARPPIN_BASE_DIR"] = BASE_DIR

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

_server_started = False
_server_error = None


def start_server():
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
    try:
        from backend.main import tunnel, location
        import asyncio

        async def cleanup():
            try:
                if location.is_spoofing:
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
            window = webview.create_window(
                "WarpPin - 錯誤",
                html=f"""
                <html><body style="font-family:system-ui;padding:40px;background:#1e1e1e;color:#e0e0e0;">
                <h2>WarpPin 啟動失敗</h2>
                <p style="color:#ff453a;">{_server_error}</p>
                </body></html>
                """,
                width=500,
                height=300,
            )
            webview.start()
            os._exit(1)
            return

        if _server_started:
            time.sleep(1)
            break
    else:
        os._exit(1)
        return

    window = webview.create_window(
        "WarpPin",
        f"http://{SERVER_HOST}:{SERVER_PORT}",
        width=1200,
        height=800,
        min_size=(900, 600),
    )
    window.events.closing += on_closing
    webview.start()
    os._exit(0)


if __name__ == "__main__":
    main()
