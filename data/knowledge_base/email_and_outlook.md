# Microsoft 365 Outlook & Teams Troubleshooting

## Overview
Remediation procedures for common Microsoft 365 desktop client failures, indexing problems, shared mailbox synchronization issues, and Microsoft Teams cache corruption.

---

## 1. Outlook Crashes or Freezes on Startup
- **Safe Mode Test**:
  - Press `Win + R`, type `outlook.exe /safe` and press Enter.
  - If Outlook opens normally in Safe Mode, a COM Add-in is causing the crash.
  - Go to `File -> Options -> Add-ins -> Manage: COM Add-ins -> Go`.
  - Uncheck non-Microsoft add-ins (e.g. Acrobat PDF maker, legacy CRM plugins).

- **Corrupted OST Cache File**:
  1. Close Outlook completely.
  2. Press `Win + R`, enter `%localappdata%\Microsoft\Outlook`.
  3. Rename your email data file (e.g., `user@company.com.ost` to `user@company.com.ost.old`).
  4. Launch Outlook. A clean `.ost` file will download from Microsoft 365 Exchange Online.

---

## 2. Shared Mailbox Issues (Not Updating or Crashing)
When users have permission to high-volume shared mailboxes (e.g., `support@company.com`):
1. In Outlook, click **File -> Account Settings -> Account Settings**.
2. Select your account and click **Change**.
3. Click **More Settings -> Advanced tab**.
4. Uncheck **"Download shared folders"** (this switches shared mailboxes to Online Mode and prevents local cache bloat).
5. Click Apply -> OK, and restart Outlook.

---

## 3. Microsoft Teams Audio, Video, or Cache Glitches
If Teams is stuck loading, fails to detect webcam/microphone, or fails to join meetings:
1. Quit Microsoft Teams completely (right-click Teams icon in tray -> Quit).
2. For New Teams (Work or School):
   - Open Windows Settings -> Apps -> Installed Apps -> Microsoft Teams.
   - Click the three dots -> **Advanced options** -> Click **Reset**.
3. For Classic Teams:
   - Run `rmdir /s /q "%appdata%\Microsoft\Teams"` in Command Prompt.
4. Restart Microsoft Teams.

