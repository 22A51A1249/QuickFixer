# Cloud Infrastructure and Corporate Database Access Guide

## Overview
Protocols for troubleshooting Azure/AWS cloud services, database connectivity errors, and SQL query timeouts.

---

## 1. Corporate Database Connection Failures
If client applications report "Cannot connect to SQL Server" or "Connection Timeout Expired":
1. Check VPN connectivity: Corporate databases are restricted behind private VPC subnets. Ensure your VPN client is connected.
2. Verify TCP port reachability:
   ```cmd
   Test-NetConnection -ComputerName sqlsvr01.corp.internal -Port 1433
   ```
3. If port test fails with `TcpTestSucceeded: False`, check with Network Operations for security group firewall rules.

---

## 2. Cloud Services & Virtual Machine Errors
If your Azure Virtual Machine or AWS workspace is unresponsive:
1. Access the Cloud Self-Service Console: `https://cloud.company.com`.
2. Check VM instance status (Running / Stopped / Deallocated).
3. If CPU is pegged at 100%, trigger a **Restart** from the cloud portal action menu.
4. Verify your assigned IAM role in Okta Cloud Management.

