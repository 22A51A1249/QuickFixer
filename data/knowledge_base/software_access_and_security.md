# Software Deployment, Permissions, and Security Policies

## Overview
Standard protocols for requesting software installations, elevated local administrator privileges, reporting phishing incidents, and BitLocker recovery.

---

## 1. Approved Software Installation (Company Portal / Intune)
- Employees must NOT download `.exe` / `.msi` installers from random web browsers.
- To install pre-approved IT catalog applications (VS Code, Slack, Zoom, Postman, Docker, Git):
  1. Open the Start menu and type **Company Portal**.
  2. Search for the required application in the catalog.
  3. Click **Install**. Intune will silently install with authorized system privileges.

---

## 2. Requesting Temporary Local Administrator Rights
- Standard employee accounts run as non-privileged users to prevent ransomware spread.
- If elevation is needed for debugging, driver updates, or development:
  1. Open **Make Me Admin** or **Endpoint Privilege Management (EPM)** from system tray.
  2. Enter the business justification and ticket ID.
  3. Elevation is automatically granted for 30 minutes, after which rights revert to standard user.

---

## 3. Reporting Suspicious Emails & Phishing
- If you receive an email asking for password verification, gift cards, or emergency wire transfers:
  1. Do NOT click links or open attachments.
  2. Click the **Report Phishing** (PhishAlarm / Defender) button in the Outlook top ribbon.
  3. The message is automatically moved to the Junk folder and sent to the SOC (Security Operations Center) team for sandbox analysis.
  4. If you already clicked a link or entered your credentials, immediately disconnect your PC from Wi-Fi / Ethernet and phone the IT Security Hotline at `ext. 4444`.

---

## 4. BitLocker Drive Encryption Recovery
If Windows boots into the blue "BitLocker recovery - Enter the recovery key for this drive" screen:
1. Access `https://aka.ms/myrecoverykey` on your smartphone using your corporate Microsoft account.
2. Match the 8-character Key ID shown on the laptop screen with the Key ID in the portal.
3. Type the 48-digit numerical recovery key and press Enter.

