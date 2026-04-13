"""WarpPin Phase 1 - Step 1: 偵測 iPhone 裝置"""

import asyncio
from pymobiledevice3.usbmux import list_devices
from pymobiledevice3.lockdown import create_using_usbmux

async def main():
    # 列出所有 USB 連線的裝置
    devices = await list_devices()

    if not devices:
        print("找不到任何裝置，請確認：")
        print("  1. iPhone 已用 USB 接上 Mac")
        print("  2. iPhone 已解鎖並信任這台電腦")
        return

    print(f"偵測到 {len(devices)} 台裝置：\n")

    for device in devices:
        # 建立 lockdown 連線，讀取裝置資訊
        lockdown = await create_using_usbmux(serial=device.serial)
        info = lockdown.all_values

        print(f"  裝置名稱：{info.get('DeviceName', '未知')}")
        print(f"  型號：    {info.get('ProductType', '未知')}")
        print(f"  iOS 版本：{info.get('ProductVersion', '未知')}")
        print(f"  UDID：    {device.serial}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
