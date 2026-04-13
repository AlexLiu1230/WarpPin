"""定位控制 — 傳送和恢復 GPS 位置"""

import logging
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider

logger = logging.getLogger(__name__)


class LocationController:
    def __init__(self):
        self._rsd = None
        self._dvt = None
        self._location = None
        self._current_lat = None
        self._current_lng = None
        self._spoofing = False

    @property
    def is_connected(self):
        return self._location is not None

    @property
    def is_spoofing(self):
        return self._spoofing

    @property
    def current_position(self):
        if self._spoofing:
            return {"lat": self._current_lat, "lng": self._current_lng}
        return None

    async def connect(self, address, port):
        """連線到裝置的 DVT 服務"""
        self._rsd = RemoteServiceDiscoveryService((address, port))
        await self._rsd.connect()

        self._dvt = DvtProvider(self._rsd)
        await self._dvt.__aenter__()

        self._location = LocationSimulation(self._dvt)
        await self._location.connect()
        logger.info("DVT 定位服務已連線")

    async def set_location(self, lat, lng):
        """傳送到指定座標"""
        if not self.is_connected:
            raise RuntimeError("尚未連線到裝置")

        await self._location.set(lat, lng)
        self._current_lat = lat
        self._current_lng = lng
        self._spoofing = True
        logger.info(f"已傳送到 {lat}, {lng}")

    async def clear_location(self):
        """恢復真實定位"""
        if not self.is_connected:
            raise RuntimeError("尚未連線到裝置")

        await self._location.clear()
        self._spoofing = False
        self._current_lat = None
        self._current_lng = None
        logger.info("已恢復真實定位")

    async def disconnect(self):
        """關閉所有連線"""
        if self._dvt:
            await self._dvt.__aexit__(None, None, None)
        self._dvt = None
        self._location = None
        self._rsd = None
        self._spoofing = False
        logger.info("DVT 連線已關閉")
