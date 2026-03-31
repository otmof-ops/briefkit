# 2. Key Findings

## 2.1 Overview

This section presents the findings of the infrastructure audit organized by
severity classification. The audit identified 14 discrete findings: 2 critical,
4 high, 5 medium, and 3 low. Severity ratings were assigned using the
likelihood-by-impact risk matrix described in Section 1.6. Each finding includes
a description, evidence references, affected assets, and mapping to the relevant
NIST CSF and ISO 27001 control domains.

## 2.2 Severity Distribution

| Severity | Count | Percentage | Remediation SLA          |
|----------|-------|------------|--------------------------|
| Critical | 2     | 14.3%      | Immediate (0-14 days)    |
| High     | 4     | 28.6%      | Urgent (15-30 days)      |
| Medium   | 5     | 35.7%      | Planned (31-90 days)     |
| Low      | 3     | 21.4%      | Tracked (next cycle)     |
| **Total**| **14**| **100%**   |                          |

## 2.3 Critical Findings

### Finding C-01: Unpatched Public-Facing Servers with Known Exploited Vulnerabilities

**Severity:** Critical (Likelihood 5, Impact 5, Score 25)
**NIST CSF:** PR.IP-12 (Vulnerability Management)
**ISO 27001:** A.12.6.1 (Management of Technical Vulnerabilities)
**Affected Assets:** 4 servers (WEB-PROD-01, WEB-PROD-02, API-GW-01, API-GW-03)

Four public-facing servers were identified with unpatched vulnerabilities listed
in CISA's Known Exploited Vulnerabilities (KEV) catalog. Two web servers
(WEB-PROD-01 and WEB-PROD-02 at DC-SOUTH) are running Apache HTTP Server 2.4.51,
which is affected by CVE-2024-38473 (CVSS 9.8, path traversal leading to remote
code execution). Two API gateway servers (API-GW-01 at DC-CENTRAL and API-GW-03
at DC-WEST) are running an unpatched version of NGINX with CVE-2024-31079
(CVSS 8.1, HTTP/3 request smuggling).

These vulnerabilities have active exploit code available in public repositories
and have been observed in active exploitation campaigns by multiple threat groups.
The affected servers are directly accessible from the internet with no web
application firewall in the traffic path. Automated vulnerability scans confirmed
the presence of these CVEs on January 22, 2026. Patch review indicated that
vendor patches have been available for more than 180 days.

**Evidence:** Nessus scan results (Scan ID: NS-2026-0122-A), CVE cross-reference
with CISA KEV catalog (accessed January 23, 2026).

### Finding C-02: No Multi-Factor Authentication on Administrative Accounts

**Severity:** Critical (Likelihood 4, Impact 5, Score 20)
**NIST CSF:** PR.AC-7 (Authentication)
**ISO 27001:** A.9.4.2 (Secure Log-on Procedures)
**Affected Assets:** 31 administrative accounts across Active Directory, VMware
vCenter, and network device management interfaces

Multi-factor authentication is not enforced on any of the 31 accounts with
domain administrator, server administrator, or network device administrator
privileges. Active Directory audit confirmed that the MFA conditional access
policy exists in Azure AD but is configured in "report-only" mode and has never
been enforced. VMware vCenter and network device management consoles (Cisco ISE,
Palo Alto Panorama) authenticate against local accounts with password-only
authentication.

Interview evidence confirmed that an MFA rollout was initiated in Q2 2025 but
was paused due to compatibility concerns with a legacy RADIUS integration.
The pause was documented in change record CHG-2025-0847 but no remediation
timeline was established. During the 18-month incident log analysis period,
three unauthorized access attempts targeting administrative accounts were
detected by the SIEM, two of which progressed to credential validation before
being blocked by IP-based restrictions.

**Evidence:** Azure AD conditional access policy export (January 28, 2026),
vCenter authentication configuration audit, ServiceNow incident records
INC-2025-4471, INC-2025-6203, INC-2025-8892.

## 2.4 High-Severity Findings

### Finding H-01: Disaster Recovery Plan Untested for 18 Months

**Severity:** High (Likelihood 3, Impact 5, Score 15)
**NIST CSF:** RC.RP-1 (Recovery Planning)
**ISO 27001:** A.17.1.3 (Verify, Review and Evaluate Information Security Continuity)
**Affected Assets:** All three data center facilities

The documented disaster recovery plan (DRP-2024-R3) specifies quarterly
tabletop exercises and annual full-failover tests. Review of testing records
confirmed that the last tabletop exercise was conducted on July 15, 2024, and
the last full-failover test was conducted on September 3, 2024. No DR testing
of any kind has been performed in the subsequent 18 months.

Interview evidence attributed the lapse to a reorganization of the IT Operations
team in Q4 2024, during which the DR testing coordinator role was vacated and
not reassigned. The DR plan itself has not been updated to reflect infrastructure
changes made since September 2024, including the decommissioning of two servers
at DC-WEST and the addition of three new production applications.

**Evidence:** DR testing log (last entry July 2024), interview with IT Operations
Manager (February 4, 2026), change records CHG-2024-1203 through CHG-2025-0156.

### Finding H-02: Three End-of-Life Operating Systems in Production

**Severity:** High (Likelihood 4, Impact 4, Score 16)
**NIST CSF:** PR.IP-12 (Vulnerability Management)
**ISO 27001:** A.12.6.1 (Management of Technical Vulnerabilities)
**Affected Assets:** APP-LEGACY-01 (Windows Server 2012 R2), APP-LEGACY-02
(CentOS 7), DB-LEGACY-01 (Red Hat Enterprise Linux 6)

Three production servers are running operating systems that have reached end of
life and no longer receive security patches from their respective vendors.
Windows Server 2012 R2 reached end of extended support on October 10, 2023.
CentOS 7 reached end of life on June 30, 2024. Red Hat Enterprise Linux 6
reached end of extended life-cycle support on June 30, 2024.

These servers host two legacy financial reporting applications and one legacy
database instance that collectively support month-end close processes. Nessus
scanning identified a combined 127 unpatched vulnerabilities across the three
servers, including 14 rated Critical and 38 rated High by CVSS scoring. The
servers are on internal network segments but are accessible from the corporate
LAN without additional segmentation controls.

**Evidence:** Nessus scan results (Scan IDs: NS-2026-0122-B, NS-2026-0122-C,
NS-2026-0122-D), vendor end-of-life announcements, asset inventory records.

### Finding H-03: No Centralized Log Management

**Severity:** High (Likelihood 3, Impact 4, Score 12)
**NIST CSF:** DE.AE-3 (Event Analysis)
**ISO 27001:** A.12.4.1 (Event Logging)
**Affected Assets:** All production servers and network devices

Log management is fragmented across the environment. Each data center stores
logs locally on individual servers, with no centralized aggregation, correlation,
or retention policy enforcement. DC-SOUTH forwards syslog to a Datadog instance,
but DC-CENTRAL and DC-WEST do not. Network device logs are stored locally with
a 7-day retention window, after which they are overwritten.

The absence of centralized logging directly impairs threat detection, incident
investigation, and forensic analysis capabilities. During the incident log
analysis, the audit team identified three incidents (INC-2025-3341, INC-2025-5567,
INC-2025-7102) where investigation was significantly hampered by the inability
to correlate events across systems. Mean time to resolve for incidents requiring
cross-system log analysis was 14.3 hours, compared with 3.7 hours for incidents
where relevant logs were available in Datadog.

**Evidence:** Log architecture review (February 11, 2026), Datadog configuration
export, interview with Security Operations Lead (February 6, 2026), incident
records with resolution timeline analysis.

### Finding H-04: Backup Verification Gaps

**Severity:** High (Likelihood 3, Impact 5, Score 15)
**NIST CSF:** PR.IP-4 (Backups)
**ISO 27001:** A.12.3.1 (Information Backup)
**Affected Assets:** Backup infrastructure at DC-CENTRAL and DC-WEST

Backup jobs are scheduled and completing successfully according to backup
software logs (Veeam Backup & Replication 12). However, restoration testing
has not been performed on a systematic basis. The backup operations team
confirmed that the last successful restoration test was conducted on August 12,
2025, and covered only 6 of the 47 production servers. No restoration test has
ever been performed for the 12 SaaS application backup sets (Microsoft 365
mailbox exports and Salesforce weekly data exports).

At DC-CENTRAL, the backup storage array is at 91 percent capacity, which has
caused 11 backup job failures in the past 90 days due to insufficient space.
These failures were logged in Veeam but not escalated to the operations team
because alerting thresholds were set at 95 percent. At DC-WEST, the NAS
cluster used for backup storage has a single controller with no redundancy,
representing a single point of failure for all DC-WEST backup data.

**Evidence:** Veeam backup job logs (90-day extract), storage capacity reports,
restoration test records, interview with Backup Operations Engineer
(February 7, 2026).

## 2.5 Medium-Severity Findings

### Finding M-01: Inconsistent Network Segmentation

**Severity:** Medium (Likelihood 3, Impact 3, Score 9)
**NIST CSF:** PR.AC-5 (Network Integrity)
**ISO 27001:** A.13.1.3 (Segregation in Networks)

Network segmentation is implemented at DC-SOUTH using VLANs with inter-VLAN
routing controlled by firewall policy. However, DC-CENTRAL and DC-WEST use
flat network architectures with no segmentation between production, development,
and management traffic. Firewall rule analysis at DC-CENTRAL identified 47
overly permissive rules, including 12 "any-any" rules that predate the current
IT Operations team and have no documented business justification.

**Evidence:** Network topology diagrams, firewall rule exports, Palo Alto
Panorama configuration audit (February 13, 2026).

### Finding M-02: Incomplete Asset Inventory

**Severity:** Medium (Likelihood 2, Impact 4, Score 8)
**NIST CSF:** ID.AM-1 (Asset Management)
**ISO 27001:** A.8.1.1 (Inventory of Assets)

The CMDB in ServiceNow contains records for 39 of the 47 production servers
identified during the audit. Eight servers were discovered through network
scanning that did not appear in the CMDB. Additionally, 4 of the 12 SaaS
applications have no CMDB record. Asset ownership is assigned for 71 percent
of recorded assets; the remainder have no designated owner.

**Evidence:** ServiceNow CMDB export cross-referenced with Nessus scan discovery
results (January 22, 2026).

### Finding M-03: Expired SSL/TLS Certificates on Internal Services

**Severity:** Medium (Likelihood 3, Impact 3, Score 9)
**NIST CSF:** PR.DS-2 (Data Security)
**ISO 27001:** A.10.1.1 (Cryptographic Controls)

Seven internal-facing services are using expired SSL/TLS certificates. Three
certificates expired more than 90 days prior to the audit. No automated
certificate lifecycle management tool is deployed. Certificate renewal is
performed manually on request, with no inventory or expiration tracking system
in place.

**Evidence:** SSL scan results across internal IP ranges (February 10, 2026).

### Finding M-04: Privileged Account Password Rotation Non-Compliance

**Severity:** Medium (Likelihood 3, Impact 3, Score 9)
**NIST CSF:** PR.AC-1 (Identity Management)
**ISO 27001:** A.9.4.3 (Password Management System)

ACME's password policy requires 90-day rotation for all privileged accounts.
Active Directory audit revealed that 14 of 31 privileged accounts have not
had passwords rotated within the required 90-day window. The oldest unreset
password is 247 days old. Service accounts are excluded from the rotation
policy with no compensating controls documented.

**Evidence:** Active Directory privileged account audit report (January 30, 2026).

### Finding M-05: Inadequate Change Management Documentation

**Severity:** Medium (Likelihood 2, Impact 3, Score 6)
**NIST CSF:** PR.IP-3 (Configuration Management)
**ISO 27001:** A.12.1.2 (Change Management)

Review of 342 change records from the past 12 months revealed that 23 percent
lacked a documented rollback plan, 18 percent had no post-implementation
verification record, and 9 percent were implemented without Change Advisory
Board approval. Emergency changes accounted for 31 percent of all changes,
significantly exceeding the industry benchmark of 10-15 percent.

**Evidence:** ServiceNow change management records (March 2025-February 2026),
CAB meeting minutes.

## 2.6 Low-Severity Findings

### Finding L-01: Outdated Network Architecture Documentation

**Severity:** Low (Likelihood 2, Impact 2, Score 4)
**NIST CSF:** ID.AM-3 (Asset Management)
**ISO 27001:** A.8.1.1 (Inventory of Assets)

Network architecture diagrams for DC-CENTRAL and DC-WEST have not been updated
since March 2024. Fourteen infrastructure changes affecting network topology
have been made since that date, rendering the diagrams inaccurate for incident
response and capacity planning purposes.

**Evidence:** Document version history, change records affecting network topology.

### Finding L-02: Non-Standard Server Naming Convention

**Severity:** Low (Likelihood 1, Impact 2, Score 2)
**NIST CSF:** ID.AM-1 (Asset Management)
**ISO 27001:** A.8.1.2 (Ownership of Assets)

Server naming conventions are inconsistent across data centers. DC-SOUTH uses
the format [ROLE]-[ENV]-[SEQ] (e.g., WEB-PROD-01), DC-CENTRAL uses
[LOCATION]-[ROLE]-[SEQ] (e.g., CHI-WEB-01), and DC-WEST uses ad hoc names
assigned by the provisioning engineer. This inconsistency complicates asset
tracking, log correlation, and operational communication.

**Evidence:** Asset inventory review, server hostname survey.

### Finding L-03: Missing Service Level Agreements for Internal IT Services

**Severity:** Low (Likelihood 1, Impact 3, Score 3)
**NIST CSF:** ID.GV-3 (Governance)
**ISO 27001:** A.15.1.2 (Addressing Security within Supplier Agreements)

Formal service level agreements exist for only 3 of the 12 SaaS applications
and 0 of the 8 internally hosted applications. Without documented SLAs, there
are no agreed-upon availability targets, response time expectations, or escalation
procedures for service degradation.

**Evidence:** SLA document inventory, interview with IT Service Management Lead
(February 12, 2026).

## 2.7 NIST CSF Compliance Gap Analysis

| NIST CSF Function | Category                  | Status                  | Gap Summary                                          |
|-------------------|---------------------------|-------------------------|------------------------------------------------------|
| Govern (GV)       | GV.OC Organizational Context | Partially Implemented | Governance framework exists but SLA coverage is incomplete |
| Identify (ID)     | ID.AM Asset Management    | Partially Implemented   | CMDB incomplete; 8 servers and 4 SaaS apps unregistered |
| Identify (ID)     | ID.RA Risk Assessment     | Implemented             | Annual risk assessment process is active and documented |
| Protect (PR)      | PR.AC Access Control      | Not Implemented         | MFA not enforced; password rotation non-compliant    |
| Protect (PR)      | PR.DS Data Security       | Partially Implemented   | Encryption in transit present but certificate management absent |
| Protect (PR)      | PR.IP Information Protection | Partially Implemented | Patching and change management have significant gaps |
| Protect (PR)      | PR.IP Backups             | Partially Implemented   | Backups scheduled but verification and capacity inadequate |
| Detect (DE)       | DE.AE Event Analysis      | Not Implemented         | No centralized logging across all facilities         |
| Detect (DE)       | DE.CM Continuous Monitoring | Partially Implemented | Monitoring active at DC-SOUTH only                   |
| Respond (RS)      | RS.RP Response Planning   | Implemented             | Incident response playbooks current and tested       |
| Recover (RC)      | RC.RP Recovery Planning   | Not Implemented         | DR plan untested for 18 months; not updated for infrastructure changes |

## 2.8 Summary

The audit identified a total of 14 findings across 4 severity levels. The two
critical findings — unpatched public-facing servers and absent MFA on
administrative accounts — represent immediate risk to ACME's security posture
and require urgent remediation. The four high-severity findings indicate
systemic gaps in operational resilience, particularly in disaster recovery
testing, end-of-life system management, log management, and backup verification.
Medium and low findings reflect control maturity gaps that, while not presenting
immediate risk, will impede ACME's planned ISO 27001 certification and cloud
migration initiatives if left unaddressed.

The NIST CSF compliance mapping reveals that the Protect and Detect functions
have the most significant gaps, with three control categories rated as Not
Implemented or Partially Implemented. The Recover function is similarly impaired
by the untested disaster recovery plan. Recommendations for remediation are
presented in Section 3.
