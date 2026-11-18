# Access Control, Permissions, and Shared Drive Guide

## Overview
Procedures for requesting network file share permissions, resolving "Access Denied" errors, and managing SharePoint / OneDrive access.

---

## 1. Resolving "Access Denied" on Shared Folders
If you receive "Windows cannot access \\filesvr\folder - You do not have permission":
1. Confirm the complete UNC path:
   - Engineering: `\\filesvr01.corp.internal\engineering`
   - Finance: `\\filesvr01.corp.internal\finance`
   - General Shared: `\\filesvr02.corp.internal\shared`
2. Open PowerShell and check your Active Directory group memberships:
   ```cmd
   whoami /groups
   ```
3. If your manager recently granted access, your Kerberos ticket must be refreshed:
   ```cmd
   klist purge
   ```
4. Sign out of Windows (`Ctrl + Alt + Del` -> **Sign out**) and log back in to renew your security token with updated group SIDs.

---

## 2. Requesting Access to Restricted Network Shares
1. Navigate to the corporate identity portal: `https://access.company.com`.
2. Search for the target folder or security group name (e.g., `SG-Finance-ReadWrite`).
3. Enter your business justification and select your department manager for approval.
4. Once your manager approves, Active Directory replication completes within 30 minutes.

---

## 3. SharePoint and OneDrive Permission Errors
If a web link shows "You need permission to access this site":
1. Click **Request Access** directly on the Microsoft 365 page.
2. Ensure you are signed into the browser with your corporate email (`username@company.com`) rather than a personal Microsoft account.
3. If OneDrive client fails to sync, run:
   ```cmd
   %localappdata%\Microsoft\OneDrive\onedrive.exe /reset
   ```

