# 3. Recommendations

## 3.1 Overview

This section presents a prioritized remediation roadmap addressing all 14 findings
identified during the audit. Recommendations are organized into three phases based
on risk severity, implementation complexity, and dependency relationships. The
total estimated investment across all phases is $340,000 over six months, with an
expected aggregate risk reduction of 73 percent upon full implementation as
measured by the weighted risk score methodology described in Section 1.6.

Each recommendation identifies the findings it addresses, the responsible party,
estimated cost, and expected risk reduction contribution. Cost estimates include
tooling, labor (internal and contractor), and licensing but exclude ongoing
operational costs, which are noted separately where material.

## 3.2 Phase 1: Immediate Remediation (0-30 Days)

### Recommendation 1.1: Patch All Public-Facing Servers

**Addresses:** Finding C-01
**Responsible Party:** Infrastructure Operations Team
**Estimated Cost:** $15,000 (emergency change labor, testing, rollback preparation)
**Risk Reduction:** 18%

Apply all outstanding security patches to the four public-facing servers
(WEB-PROD-01, WEB-PROD-02, API-GW-01, API-GW-03) within 14 days. Patching
should follow the emergency change process with abbreviated CAB approval. Prior
to patching, deploy a web application firewall (Cloudflare WAF, already licensed
under ACME's existing Cloudflare Enterprise contract) as an interim mitigation
to provide virtual patching while the production patch cycle is prepared and
tested.

Establish a standing policy requiring that any vulnerability listed in the CISA
KEV catalog be patched within 14 days of catalog publication, consistent with
CISA Binding Operational Directive 22-01 timelines. Integrate KEV catalog
monitoring into the existing Datadog alerting pipeline.

### Recommendation 1.2: Enforce Multi-Factor Authentication on All Administrative Accounts

**Addresses:** Finding C-02
**Responsible Party:** Identity and Access Management Team
**Estimated Cost:** $25,000 (Azure AD P2 licensing uplift, configuration, testing, training)
**Risk Reduction:** 16%

Transition the existing Azure AD MFA conditional access policy from report-only
mode to enforced mode for all 31 administrative accounts within 14 days. Resolve
the legacy RADIUS integration compatibility issue identified in CHG-2025-0847 by
deploying the Azure AD NPS Extension, which provides MFA capability for
RADIUS-authenticated sessions without requiring replacement of the legacy
RADIUS infrastructure.

For VMware vCenter and network device management consoles that authenticate
against local accounts, implement SAML-based SSO federation to Azure AD within
30 days, eliminating local account authentication and bringing these systems
under the centralized MFA policy. Where SAML integration is not technically
feasible within the 30-day window, implement hardware security keys (YubiKey 5
series) as an interim MFA mechanism for local administrative access.

### Recommendation 1.3: Rotate All Non-Compliant Privileged Account Passwords

**Addresses:** Finding M-04
**Responsible Party:** Identity and Access Management Team
**Estimated Cost:** $5,000 (labor)
**Risk Reduction:** 4%

Immediately rotate passwords for all 14 privileged accounts identified as
non-compliant with the 90-day rotation policy. Implement automated password
rotation using CyberArk Privileged Access Manager (already deployed but
under-utilized) for all domain administrator, server administrator, and network
device administrator accounts. Configure automated alerts for rotation
policy violations.

## 3.3 Phase 2: Short-Term Remediation (30-90 Days)

### Recommendation 2.1: Deploy Centralized Log Management

**Addresses:** Finding H-03
**Responsible Party:** Security Operations Team
**Estimated Cost:** $85,000 (SIEM licensing, integration labor, storage infrastructure)
**Risk Reduction:** 12%

Extend the existing Datadog log aggregation to DC-CENTRAL and DC-WEST within
60 days. Configure syslog forwarding from all production servers and network
devices to the centralized Datadog instance. Establish a minimum 90-day log
retention policy for security-relevant events and a 30-day retention policy for
operational logs, consistent with ISO 27001 A.12.4.1 requirements.

Deploy correlation rules for the three incident scenarios previously identified
as investigation-impaired (cross-site authentication anomalies, lateral movement
indicators, and backup job failure sequences). The expected reduction in mean
time to resolve for cross-system incidents is from 14.3 hours to under 4 hours,
based on the performance observed at DC-SOUTH where centralized logging is
already operational.

### Recommendation 2.2: Conduct Disaster Recovery Testing

**Addresses:** Finding H-01
**Responsible Party:** IT Operations Manager
**Estimated Cost:** $20,000 (tabletop exercise facilitation, failover test execution, contractor support)
**Risk Reduction:** 8%

Conduct a tabletop disaster recovery exercise within 45 days, followed by a
full-failover test for DC-SOUTH (primary site) within 90 days. Update the
disaster recovery plan (DRP-2024-R3) to reflect all infrastructure changes made
since September 2024 prior to the tabletop exercise. Assign a permanent DR
Testing Coordinator role within IT Operations to prevent future lapses in
testing cadence.

Establish a DR testing calendar with quarterly tabletop exercises and
semi-annual failover tests, with testing completion tracked as a KPI in the
IT Operations dashboard. Each test should produce a documented lessons-learned
report with action items tracked to closure.

### Recommendation 2.3: Remediate Backup Verification Gaps

**Addresses:** Finding H-04
**Responsible Party:** Backup Operations Engineer
**Estimated Cost:** $30,000 (storage expansion, automation tooling, SaaS backup solution)
**Risk Reduction:** 7%

Expand backup storage at DC-CENTRAL to reduce utilization from 91 percent to
below 70 percent, eliminating capacity-related backup failures. Lower the
alerting threshold from 95 percent to 80 percent. Add redundant controller
to the DC-WEST NAS cluster to eliminate the single point of failure.

Implement automated monthly restoration testing for a rotating subset of
production servers (minimum 12 servers per quarter, ensuring full coverage
within each annual cycle). Deploy a dedicated SaaS backup solution (e.g.,
OwnBackup or Spanning) for Microsoft 365 and Salesforce backup verification,
with automated weekly restoration validation of a sample mailbox and Salesforce
object set.

## 3.4 Phase 3: Medium-Term Remediation (90-180 Days)

### Recommendation 3.1: Migrate End-of-Life Operating Systems

**Addresses:** Finding H-02
**Responsible Party:** Application Development Team and Infrastructure Operations
**Estimated Cost:** $120,000 (application migration, server provisioning, testing, parallel operation)
**Risk Reduction:** 9%

Migrate the three legacy applications running on end-of-life operating systems
to supported platforms within 180 days. The recommended target platforms are
Windows Server 2022 for the financial reporting application currently on
Windows Server 2012 R2, and Red Hat Enterprise Linux 9 for the two applications
currently on CentOS 7 and RHEL 6.

Migration should follow a parallel-operation model with a minimum 30-day
validation period during which both legacy and target environments operate
simultaneously. Application compatibility testing should commence within 30 days,
with migration execution scheduled to complete before the Q3 2026 month-end
close cycle to avoid disruption to financial reporting processes.

### Recommendation 3.2: Implement Network Segmentation and Backup Automation

**Addresses:** Findings M-01, M-02, M-03, M-05
**Responsible Party:** Network Engineering and IT Operations
**Estimated Cost:** $40,000 (network reconfiguration, certificate management tooling, CMDB remediation)
**Risk Reduction:** 6%

Implement VLAN-based network segmentation at DC-CENTRAL and DC-WEST consistent
with the architecture already deployed at DC-SOUTH. Remove all undocumented
"any-any" firewall rules and replace with least-privilege rules with documented
business justification. Deploy automated certificate lifecycle management
(e.g., HashiCorp Vault PKI or Let's Encrypt with certbot) for all internal
services. Remediate the CMDB to achieve 100 percent coverage of production
assets with designated owners.

## 3.5 Implementation Roadmap

| Phase | Timeline     | Recommendation                              | Findings Addressed | Estimated Cost | Risk Reduction |
|-------|-------------|---------------------------------------------|-------------------|----------------|----------------|
| 1     | Days 0-14   | Patch public-facing servers                 | C-01              | $15,000        | 18%            |
| 1     | Days 0-14   | Enforce MFA on admin accounts               | C-02              | $25,000        | 16%            |
| 1     | Days 0-30   | Rotate non-compliant privileged passwords   | M-04              | $5,000         | 4%             |
| 2     | Days 30-90  | Deploy centralized log management           | H-03              | $85,000        | 12%            |
| 2     | Days 30-90  | Conduct DR testing and plan update          | H-01              | $20,000        | 8%             |
| 2     | Days 30-90  | Remediate backup verification gaps          | H-04              | $30,000        | 7%             |
| 3     | Days 90-180 | Migrate EOL operating systems               | H-02              | $120,000       | 9%             |
| 3     | Days 90-180 | Network segmentation and operational fixes  | M-01, M-02, M-03, M-05 | $40,000  | 6%             |
|       |             | **Total**                                   | **All 14 findings** | **$340,000** | **73% (cumulative, weighted)** |

Remaining low-severity findings (L-01, L-02, L-03) are addressed as part of
the operational improvements in Phase 3 and through standard change management
processes. Network documentation updates (L-01) are a prerequisite for the
segmentation work in Recommendation 3.2. Server naming standardization (L-02)
should be incorporated into the EOL migration effort. SLA development (L-03)
should be assigned to the IT Service Management team for completion within the
next quarterly planning cycle.

## 3.6 Investment Summary

| Category                    | Phase 1   | Phase 2   | Phase 3    | Total     |
|-----------------------------|-----------|-----------|------------|-----------|
| Tooling and licensing       | $12,000   | $55,000   | $18,000    | $85,000   |
| Internal labor              | $18,000   | $40,000   | $72,000    | $130,000  |
| Contractor and consulting   | $10,000   | $30,000   | $50,000    | $90,000   |
| Hardware and infrastructure | $5,000    | $10,000   | $20,000    | $35,000   |
| **Phase total**             | **$45,000** | **$135,000** | **$160,000** | **$340,000** |

The $340,000 total investment represents approximately 4.2 percent of ACME's
annual IT operating budget. The expected return is a 73 percent reduction in
aggregate weighted risk score, elimination of all critical and high-severity
findings, and establishment of the control maturity baseline required for ISO
27001 certification. Phase 1 alone addresses 38 percent of total risk at a cost
of $45,000, representing the highest-leverage investment and should be treated
as non-discretionary.

## 3.7 Governance and Tracking

The Chief Information Officer should designate a Remediation Program Manager
to track implementation progress against the roadmap timelines. Weekly status
reporting should be provided to the CIO and VP of Engineering Operations for
the duration of the remediation program. Each recommendation should be tracked
as a discrete work package in Jira with defined acceptance criteria, and
completion should be verified by the Infrastructure Assurance Division through
targeted re-assessment.

A formal re-assessment of all critical and high-severity findings should be
scheduled at the 90-day mark (approximately April 2026) to confirm remediation
effectiveness and to identify any implementation gaps requiring course correction
before the Phase 3 work commences. A comprehensive follow-up audit should be
scheduled for Q4 2026, aligned with the ISO 27001 certification preparation
timeline.
