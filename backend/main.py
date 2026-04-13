"""WarpPin FastAPI Server"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import os as _os
_base = _os.environ.get("WARPPIN_BASE_DIR", str(Path(__file__).resolve().parent.parent))
FRONTEND_DIR = Path(_base) / "frontend"

import httpx

from backend.tunnel import TunnelManager
from backend.device import get_device_info
from backend.location import LocationController
from backend import bookmarks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全域狀態
tunnel = TunnelManager()
location = LocationController()


class TeleportRequest(BaseModel):
    lat: float
    lng: float

class BookmarkRequest(BaseModel):
    name: str
    lat: float
    lng: float
    category: str = "預設"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """啟動時嘗試連線，失敗也不阻止 server 啟動"""
    # 先快速檢查有沒有 USB 裝置，沒有就不嘗試建 tunnel（避免等 30 秒）
    try:
        info = await get_device_info()
        if info:
            address, port = tunnel.start(timeout=15)
            await location.connect(address, port)
            logger.info("WarpPin 啟動完成（裝置已連線）")
        else:
            logger.info("WarpPin 啟動完成（未偵測到裝置）")
    except Exception as e:
        logger.warning(f"裝置連線失敗：{e}")
        logger.info("WarpPin 啟動完成（等待裝置連線）")

    yield

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
    logger.info("WarpPin 已關閉")


app = FastAPI(title="WarpPin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/device")
async def api_device():
    """取得已連線裝置資訊"""
    info = await get_device_info()
    if info is None:
        return {"connected": False}
    return {"connected": True, **info}


@app.get("/api/status")
async def api_status():
    """取得連線狀態"""
    return {
        "tunnel_running": tunnel.is_running,
        "spoofing": location.is_spoofing,
        "position": location.current_position,
    }


@app.post("/api/connect")
async def api_connect():
    """手動連線裝置（接上 USB 後呼叫）"""
    if tunnel.is_running and location.is_connected:
        return {"status": "ok", "message": "已連線"}
    try:
        tunnel.stop()
        await location.disconnect()
        address, port = tunnel.start()
        await location.connect(address, port)
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/teleport")
async def api_teleport(req: TeleportRequest):
    """傳送到指定座標"""
    await location.set_location(req.lat, req.lng)
    return {"status": "ok", "lat": req.lat, "lng": req.lng}


@app.post("/api/restore")
async def api_restore():
    """恢復真實定位"""
    await location.clear_location()
    return {"status": "ok"}


# --- 書籤 API ---

@app.get("/api/bookmarks")
async def api_list_bookmarks():
    return bookmarks.list_bookmarks()


@app.post("/api/bookmarks")
async def api_add_bookmark(req: BookmarkRequest):
    bm = bookmarks.add_bookmark(req.name, req.lat, req.lng, req.category)
    return bm


@app.delete("/api/bookmarks/{bookmark_id}")
async def api_delete_bookmark(bookmark_id: str):
    bookmarks.delete_bookmark(bookmark_id)
    return {"status": "ok"}


@app.get("/api/bookmarks/categories")
async def api_list_categories():
    return bookmarks.list_categories()


# --- 地址搜尋 API ---

@app.get("/api/search")
async def api_search(q: str):
    """透過 Nominatim 搜尋地址"""
    async with httpx.AsyncClient() as client:
        res = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 5},
            headers={"User-Agent": "WarpPin/1.0"},
        )
        results = res.json()
        return [
            {
                "name": r.get("display_name", ""),
                "lat": float(r["lat"]),
                "lng": float(r["lon"]),
            }
            for r in results
        ]


@app.get("/")
async def index():
    """首頁 — 地圖 UI"""
    return FileResponse(FRONTEND_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
