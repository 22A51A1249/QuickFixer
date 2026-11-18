# Office Wi-Fi and Local Network Connectivity

## Overview
Guidelines for connecting corporate laptops and mobile devices to enterprise Wi-Fi networks (`Corp-Secure` and `Corp-Guest`), and resolving common network drops.

---

## 1. Network SSIDs
- **`Corp-Secure`**: 
  - Uses 802.1X EAP-TLS authentication with corporate machine certificate.
  - No password prompt should be shown. If prompted for password, select PEAP and use domain credentials (`CORP\username`).
- **`Corp-Guest`**: 
  - For visitors and personal mobile phones.
  - Requires accepting terms on captive portal popup at `http://guest.wifi.local`.

---

## 2. Resolving "No Internet, Secured" on Windows
1. Verify IP configuration:
   - Run `ipconfig /all` in cmd.
   - If IPv4 starts with `169.254.x.x`, APIPA is assigned because DHCP server did not respond.
2. Renew IP lease and DNS cache:
   ```cmd
   netsh winsock reset
   netsh int ip reset
   ipconfig /release
   ipconfig /renew
   ipconfig /flushdns
   ```
3. Restart the machine to apply Winsock reset.

---

## 3. Wi-Fi Adapter Disconnecting Intermittently
- **Root Cause**: Power Management disabling the wireless adapter during idle periods.
- **Fix**:
  1. Open Device Manager (`devmgmt.msc`).
  2. Expand **Network adapters** -> Right-click Wi-Fi adapter (e.g. Intel Wi-Fi 6E AX211) -> **Properties**.
  3. Go to the **Power Management** tab.
  4. Uncheck **"Allow the computer to turn off this device to save power"**.
  5. Click OK.

