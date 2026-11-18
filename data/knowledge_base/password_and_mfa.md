# Password Reset and Multi-Factor Authentication (MFA) Guide

## Overview
Procedures for managing passwords, recovering locked accounts, and resetting MFA authenticators (Microsoft Authenticator, Okta Verify, FIDO2 Security Keys).

---

## 1. Corporate Password Policy
- **Minimum Length**: 14 characters.
- **Complexity**: Must include at least 1 uppercase letter, 1 lowercase letter, 1 numeric digit, and 1 special symbol (`!@#$%^&*`).
- **History Rule**: Cannot reuse the last 12 passwords.
- **Lockout Policy**: Account is locked automatically for 15 minutes following 5 consecutive incorrect password attempts.

---

## 2. Self-Service Password Reset (SSPR)
If you know your secondary verification method (SMS, secondary email, or authenticator app):
1. Navigate to the identity portal: `https://passwordreset.microsoftonline.com` (or company SSO portal `https://sso.company.com/idp`).
2. Enter your work email address (`username@company.com`).
3. Complete the two verification steps requested by the portal.
4. Set a compliant new password.
5. Wait 60 seconds for Active Directory sync across domain controllers before logging in.

---

## 3. Account Locked Out
- If locked out, please wait **15 minutes** for the automated counter to reset.
- If immediate access is required for critical work:
  - An IT Service Desk Tier 1 technician can manually run:
    ```powershell
    Unlock-ADAccount -Identity "sjenkins"
    ```
  - Verify caller identity via HR employee ID and manager email before unlocking.

---

## 4. Resetting or Transferring Authenticator to a New Phone
When switching smartphones, old MFA pushes will not arrive on the new device automatically.
- **Standard Self-Service**:
  1. Access `https://mysignins.microsoft.com/security-info` from an already trusted corporate laptop.
  2. Click **+ Add sign-in method** -> Choose **Authenticator App**.
  3. Scan the QR code using the new phone's camera inside the app.
  4. Complete the 2-digit number challenge to activate.
  5. Delete the obsolete phone from the security info list.
- **When Locked Out of All Methods**:
  - Service Desk will issue a **Temporary Access Pass (TAP)**.
  - A TAP is a time-limited passcode (valid for 8 hours) enabling one-time sign-in to register new MFA methods.

