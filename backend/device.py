"""裝置管理 — 偵測和讀取 iPhone 資訊"""

import logging
from pymobiledevice3.usbmux import list_devices
from pymobiledevice3.lockdown import create_using_usbmux

logger = logging.getLogger(__name__)


async def get_device_info():
    """取得第一台 USB 連線裝置的資訊，沒有裝置則回傳 None"""
    devices = await list_devices()
    if not devices:
        return None

    device = devices[0]
    lockdown = await create_using_usbmux(serial=device.serial)
    info = lockdown.all_values

    return {
        "name": info.get("DeviceName", "未知"),
        "model": info.get("ProductType", "未知"),
        "ios_version": info.get("ProductVersion", "未知"),
        "udid": device.serial,
    }
