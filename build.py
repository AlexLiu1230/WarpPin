"""WarpPin 打包腳本 — 打包成 macOS 可執行檔"""

import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"


def main():
    print("=== WarpPin 打包開始 ===\n")

    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)
            print(f"已清理 {d.name}/")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "WarpPin",
        "--onedir",
        "--noconfirm",
        # 不用 --windowed，避免 macOS app bundle 自動重啟問題
        "--add-data", f"{PROJECT_DIR / 'frontend'}:frontend",
        "--add-data", f"{PROJECT_DIR / 'backend'}:backend",
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
        str(PROJECT_DIR / "app.py"),
    ]

    print("執行 PyInstaller ...\n")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))

    if result.returncode != 0:
        print("\n打包失敗！")
        sys.exit(1)

    warppin_dir = DIST_DIR / "WarpPin"
    if not warppin_dir.exists():
        print("\n找不到輸出目錄")
        sys.exit(1)

    # 建立啟動腳本
    launcher = DIST_DIR / "WarpPin.command"
    launcher.write_text("""#!/bin/bash
# WarpPin 啟動腳本
DIR="$(cd "$(dirname "$0")" && pwd)"
"$DIR/WarpPin/WarpPin"
""")
    launcher.chmod(0o755)

    size_mb = sum(f.stat().st_size for f in warppin_dir.rglob('*') if f.is_file()) / 1024 / 1024

    print(f"\n=== 打包成功！===")
    print(f"輸出：{warppin_dir}")
    print(f"啟動腳本：{launcher}")
    print(f"大小：{size_mb:.1f} MB")
    print(f"\n使用方式：")
    print(f"  {warppin_dir / 'WarpPin'}")
    print(f"  或雙擊 {launcher}")


if __name__ == "__main__":
    main()
