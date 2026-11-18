# Network Printer, Peripherals and Docking Station Guide

## Overview
How to map network printers, unfreeze stuck print queues, and troubleshoot USB-C docking stations and external monitors.

---

## 1. Connecting to Corporate Printers
1. Press `Win + R`, type the print server path:
   - NY Office: `\\printsvr01.corp.internal`
   - London Office: `\\printsvr02.corp.internal`
2. Press Enter. A window displaying available printers will open.
3. Locate your floor printer (e.g., `NYC-4F-Color-Printer`).
4. Right-click and select **Connect**. Windows will download drivers automatically.
5. Set as default printer in `Settings -> Bluetooth & devices -> Printers & scanners`.

---

## 2. Fixing "Printer Offline" or Stuck Print Queue
If print jobs are stuck in queue and cannot be cancelled:
1. Open PowerShell / Command Prompt as Administrator.
2. Run the following cleanup commands:
   ```cmd
   net stop spooler
   del /Q /F /S "%systemroot%\System32\Spool\Printers\*.*"
   net start spooler
   ```
3. Restart the printer using the physical power toggle switch on the front panel.
4. Verify the printer has not entered sleep mode or run out of paper in Tray 2.

---

## 3. External Monitor Not Detected via USB-C Dock (Thunderbolt / DisplayLink)
1. Unplug the USB-C / Thunderbolt cable from laptop, wait 10 seconds, and replug.
2. Power cycle the docking station by disconnecting its power adapter for 15 seconds.
3. On Windows, press `Win + Ctrl + Shift + B` to trigger an instant graphics driver restart (screen will flicker briefly and beep).
4. In Windows Display Settings, click **Detect** under Multiple displays.
5. Check if DisplayLink Manager software is running in system tray.
