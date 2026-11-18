# Enterprise Cybersecurity Incident & Threat Response Guide

## Overview
Standard procedures for responding to suspicious login alerts, phishing emails, malware detection, and unauthorized account access.

---

## 1. Suspicious Login Alerts & Unauthorized Access
If you receive an email or authenticator alert regarding "Unfamiliar sign-in detected" or login from an unknown location/IP:
1. Immediately open `https://mysignins.microsoft.com` from a verified corporate workstation.
2. Review the recent activity log for the suspicious timestamp.
3. Click **"This wasn't me"** to trigger automated session revocation.
4. Immediately change your corporate password using Self-Service Password Reset (SSPR).
5. Contact the Security Operations Center (SOC) hotline at `ext. 4444`.

---

## 2. Phishing Email Reporting
If you receive an email requesting urgent gift cards, password verification, or wire transfers:
1. Do NOT click any links, open attachments, or reply to the sender.
2. Click the **Report Phishing** button in the Outlook top ribbon.
3. The email will be automatically moved to Quarantine and analyzed in the SOC security sandbox.
4. If you already entered credentials on a link, disconnect network immediately and call Security.

---

## 3. Malware and Endpoint Virus Isolation
If Windows Defender or CrowdStrike alerts to malware or ransomware:
1. Disconnect Ethernet cable and toggle off Wi-Fi immediately to prevent lateral spread.
2. Do NOT reboot the computer (rebooting can trigger persistent rootkit execution or ransomware locking).
3. Notify IT Security immediately for remote forensic triage and endpoint re-imaging.

