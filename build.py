"""WarpPin 打包腳本 — 用 PyInstaller 打包成 macOS .app"""

import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"


def main():
    print("=== WarpPin 打包開始 ===\n")

    # 清理舊的 build
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"已清理 {d.name}/")

    # PyInstaller 指令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "WarpPin",
        "--windowed",                    # macOS .app bundle（不顯示終端機）
        "--onedir",                      # 目錄模式（比 onefile 啟動快）
        "--noconfirm",
        # 加入 frontend
        "--add-data", f"{PROJECT_DIR / 'frontend'}:frontend",
        # 加入 backend 模組
        "--add-data", f"{PROJECT_DIR / 'backend'}:backend",
        # hidden imports（PyInstaller 可能漏掉的）
        "--hidden-import", "pymobiledevice3",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "fastapi",
        "--hidden-import", "httpx",
        "--hidden-import", "webview",
        # 入口
        str(PROJECT_DIR / "app.py"),
    ]

    print("執行 PyInstaller ...\n")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))

    if result.returncode != 0:
        print("\n打包失敗！")
        sys.exit(1)

    app_path = DIST_DIR / "WarpPin.app"
    if app_path.exists():
        print(f"\n=== 打包成功！===")
        print(f"輸出：{app_path}")
        print(f"\n使用方式：")
        print(f"  open {app_path}")
    else:
        # onedir 模式可能不會直接產生 .app
        print(f"\n=== 打包完成 ===")
        print(f"輸出在 {DIST_DIR}/")


if __name__ == "__main__":
    main()
