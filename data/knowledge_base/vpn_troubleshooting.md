# Corporate VPN Troubleshooting Guide

## Overview
This guide provides remediation steps for remote employees experiencing connectivity issues with corporate VPN clients (Cisco AnyConnect / GlobalProtect).

## Common Symptoms and Error Messages
1. "The VPN client agent was unable to create the interprocess communication depot."
2. "Connection attempt has failed due to server certificate issues."
3. "Secure Gateway connection timed out at 85%."
4. "Login failed: Authentication credentials or MFA token invalid."

---

## Step-by-Step Diagnostic & Resolution Procedures

### Issue 1: Gateway Connection Timed Out (Hang at 85% or 93%)
- **Root Cause**: MTU (Maximum Transmission Unit) packet fragmentation caused by home ISP routers or IPv6 tunneling conflicts.
- **Remediation Steps**:
  1. Open Command Prompt (cmd) as Administrator.
  2. Flush DNS cache and release IP configuration:
     ```cmd
     ipconfig /flushdns
     ipconfig /release
     ipconfig /renew
     ```
  3. Disable IPv6 on your active Wi-Fi / Ethernet adapter:
     - Open `ncpa.cpl` (Network Connections).
     - Right-click your network adapter -> Properties.
     - Uncheck **Internet Protocol Version 6 (TCP/IPv6)**.
     - Click OK and reconnect to VPN.
  4. If problem persists, switch gateway from primary `vpn-global.company.com` to secondary `vpn-east.company.com`.

---

### Issue 2: MFA Push Notification Not Received During VPN Login
- **Root Cause**: Authenticator app out of sync or cellular/Wi-Fi background data disabled.
- **Remediation Steps**:
  1. Ensure phone has an active internet connection.
  2. Open the Microsoft Authenticator / Duo Mobile app manually.
  3. Instead of waiting for a push prompt, enter the 6-digit one-time passcode (OTP) directly into the VPN password prompt appending it as: `Password123,123456`.
  4. If device was recently replaced, contact IT Support to issue a Temporary Access Pass (TAP).

---

### Issue 3: Virtual Network Adapter Missing or Corrupt
- **Symptoms**: Error message: "Unable to contact VPN adapter" or virtual adapter not showing in Network Connections.
- **Remediation Steps**:
  1. Press `Win + X` and select **Device Manager**.
  2. Expand **Network adapters**.
  3. Locate "Cisco AnyConnect Virtual Adapter" or "PANGP Virtual Ethernet Adapter".
  4. Right-click and choose **Uninstall device** (do NOT check delete driver files).
  5. In the top menu, click **Action -> Scan for hardware changes**.
  6. Reboot your computer.

---

### Issue 4: Split-Tunneling and Subnet Conflict
- **Symptoms**: Unable to reach internal corporate sites (e.g. `jira.corp.internal`) or local printer stops responding when VPN is active.
- **Remediation**:
  - Ensure your home router local subnet is NOT using `10.0.0.0/8` or `172.16.0.0/12`.
  - Corporate networks utilize `10.x.x.x`. If your home router assigns `10.0.0.x`, change your home router DHCP range to `192.168.1.x` to avoid IP address overlap.

