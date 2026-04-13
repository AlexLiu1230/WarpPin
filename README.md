# WarpPin

macOS 上的 iOS 虛擬定位工具。透過 USB 連線控制 iPhone 的 GPS 位置。

## 功能

- **地圖傳送** — 在地圖上點擊或輸入座標，一鍵傳送 iPhone 定位
- **地址搜尋** — 輸入地址或地名，自動轉換為座標
- **書籤管理** — 儲存常用地點，支援自訂分類
- **深色模式** — 淺色 / 深色主題切換
- **一鍵恢復** — 隨時恢復真實定位

## 截圖

> TODO: 加入截圖

## 系統需求

- macOS 10.15+
- iPhone（iOS 17+）
- USB 連接線
- iPhone 需開啟 Developer Mode

## 快速開始

### 開發模式

```bash
# 安裝依賴
pip3 install -r requirements.txt

# iPhone 用 USB 接上 Mac，然後啟動
sudo python3 app.py
```

### 打包版

```bash
# 打包成 .app
python3 build.py

# 產出在 dist/WarpPin.app
```

## 首次使用

1. iPhone 用 USB 接上 Mac
2. iPhone 上按「信任此電腦」
3. 如果 iPhone 設定裡看不到「開發者模式」，程式會自動幫你開啟選項
4. 到 **設定 → 隱私權與安全性 → 開發者模式** 開啟，iPhone 會重開機
5. 之後啟動 WarpPin 就能直接使用

## 技術架構

```
WarpPin/
├── app.py               # 啟動入口（pywebview 視窗）
├── backend/
│   ├── main.py          # FastAPI server
│   ├── tunnel.py        # pymobiledevice3 tunnel 管理
│   ├── device.py        # iPhone 裝置偵測
│   ├── location.py      # GPS 定位控制
│   └── bookmarks.py     # 書籤管理
├── frontend/
│   └── index.html       # 地圖 UI（Leaflet）
└── requirements.txt
```

| 層級 | 技術 |
|------|------|
| 核心 | pymobiledevice3 |
| 後端 | FastAPI + uvicorn |
| 前端 | Leaflet.js（單一 HTML） |
| 桌面 | pywebview |
| 地圖 | CartoDB / Stadia Maps |
| 搜尋 | Nominatim (OpenStreetMap) |

## 授權

MIT License
