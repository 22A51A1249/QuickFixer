# Windows System Crash, Freezing, and Unexpected Shutdown Remediation

## Overview
Diagnostic protocols for unexpected computer shutdown, system freezing, Blue Screen of Death (BSOD) crashes, and Kernel-Power stop events on enterprise workstations.

---

## 1. Unexpected Computer Shutdown & System Freezing
When a computer or laptop abruptly freezes and powers off while in operation:
1. **Power & Battery Verification**:
   - Verify whether the laptop was running on battery or connected to an authorized AC power charger.
   - Check if the charging status LED is illuminated (amber = charging, white = full).
2. **Thermal Safety Cut-off (Overheating)**:
   - Sudden shutdowns during active work are most commonly triggered by the motherboard's thermal protection circuit when CPU/GPU temperature exceeds 100°C.
   - Verify that cooling air vents, fan exhaust ports, and bottom intake grills are completely unobstructed.
   - Ensure the laptop is used on a hard, flat surface rather than soft fabric or lap.
3. **Hard EC Power Drain**:
   - Disconnect the AC adapter, USB-C docking station, and all external devices.
   - Press and hold the physical power button continuously for **30 seconds** to drain residual capacitive charge from the motherboard.
   - Reconnect only the AC power adapter and attempt to power on.
4. **Kernel-Power Event Inspection**:
   - Open Event Viewer (`eventvwr.msc`) -> **Windows Logs** -> **System**.
   - Filter for **Event ID 41 (Kernel-Power)** and **Event ID 6008 (Unexpected Shutdown)** to identify bugcheck parameters.
5. **Run Hardware Diagnostics**:
   - Restart the system and immediately tap `F12` (Dell) or `F2` (HP/Lenovo) to access hardware diagnostics.
   - Execute self-tests on CPU, Motherboard, and Battery Health.

---

## 2. Top Blue Screen (BSOD) Stop Codes
- **`IRQL_NOT_LESS_OR_EQUAL`**:
  - Faulty device driver accessing an invalid memory address. Update Wi-Fi and display drivers.
- **`MEMORY_MANAGEMENT`**:
  - Physical RAM stick defect, failing memory channel, or corrupted pagefile.
- **`CRITICAL_PROCESS_DIED`**:
  - Essential Windows background subsystem (`csrss.exe` or `wininit.exe`) terminated unexpectedly.
- **`INACCESSIBLE_BOOT_DEVICE`**:
  - Storage drive controller driver missing after BIOS update or BitLocker storage controller mismatch.

---

## 3. Standard Windows File Integrity Scans
Run PowerShell or cmd as Administrator:
```powershell
# 1. Scan and repair protected system files
sfc /scannow

# 2. Repair Windows Component Store image
DISM /Online /Cleanup-Image /RestoreHealth

# 3. Check disk file system integrity
chkdsk C: /f /r
```

---

## 4. Running Windows Memory Diagnostic
1. Press `Win + R`, type `mdsched.exe` and press Enter.
2. Choose **"Restart now and check for problems (recommended)"**.
3. The computer will reboot into the memory diagnostic tool and perform two test passes.
4. Any detected hardware memory faults indicate the laptop must be scheduled for IT depot motherboard/RAM replacement.

---

## 5. Collecting Minidump Files
When escalating a recurring crash ticket to Tier 3 Engineering:
- Crash dumps are saved to: `C:\Windows\Minidump\*.dmp`
- Copy the latest `.dmp` file and attach it to the IT support ticket for WinDbg stack trace analysis.
