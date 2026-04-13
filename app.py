"""WarpPin — 啟動入口"""

import threading
import time
import sys
import os
import webbrowser
import urllib.request

# PyInstaller 打包後的路徑處理
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)
os.environ["WARPPIN_BASE_DIR"] = BASE_DIR

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

_server_error = None


def start_server():
    global _server_error
    try:
        import uvicorn
        from backend.main import app
        uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")
    except Exception as e:
        _server_error = str(e)


def wait_for_server(timeout=60):
    """等 server 能回應 HTTP"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _server_error:
            return False
        try:
            urllib.request.urlopen(f"http://{SERVER_HOST}:{SERVER_PORT}/")
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    if not wait_for_server():
        print(f"啟動失敗：{_server_error or '逾時'}")
        sys.exit(1)

    url = f"http://{SERVER_HOST}:{SERVER_PORT}"
    print(f"\nWarpPin 已啟動！")
    print(f"瀏覽器開啟中：{url}")
    print(f"按 Ctrl+C 關閉\n")
    webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在關閉...")
        from backend.main import tunnel, location
        import asyncio

        async def cleanup():
            try:
                if location.is_spoofing:
                    await location.clear_location()
                await location.disconnect()
            except Exception:
                pass
            tunnel.stop()

        asyncio.run(cleanup())


if __name__ == "__main__":
    main()
