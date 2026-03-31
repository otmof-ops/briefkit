# 1. Audit Methodology

## 1.1 Engagement Overview

ACME Corporation engaged the Infrastructure Assurance Division to conduct an
independent IT infrastructure audit spanning January 6 through March 14, 2026.
The engagement was authorized by the Chief Information Officer under internal
governance directive GOV-2025-041 and sponsored by the VP of Engineering
Operations. The audit was conducted in accordance with ISACA IT Audit Framework
standards and the Institute of Internal Auditors' International Standards for
the Professional Practice of Internal Auditing.

The primary objectives of the audit were threefold:

1. Assess the security posture of ACME's IT infrastructure against current
   threat models and regulatory requirements, with specific attention to
   public-facing attack surfaces and privileged access controls.
2. Evaluate operational resilience capabilities including disaster recovery
   preparedness, backup integrity, and incident response maturity across all
   three data center facilities.
3. Determine cloud migration readiness by assessing application dependencies,
   data classification completeness, and infrastructure modernization gaps that
   would impede a phased transition to hybrid cloud architecture.

## 1.2 Assessment Framework

The audit employed a dual-framework approach mapping controls and findings to
both the NIST Cybersecurity Framework (CSF) 2.0 and ISO 27001:2022 Annex A
controls. This approach was selected because ACME's regulatory obligations
span multiple compliance domains, and the dual mapping provides a unified view
of control effectiveness across both frameworks.

The NIST CSF 2.0 functions — Govern, Identify, Protect, Detect, Respond, and
Recover — served as the primary organizational taxonomy for findings. Each
finding was additionally mapped to the relevant ISO 27001:2022 Annex A control
clause to support ACME's planned ISO certification initiative scheduled for
Q4 2026.

Supplemental evaluation against CIS Benchmarks v8 was performed for all
host-level configurations, providing a granular technical baseline against
industry-accepted hardening standards. Network architecture was assessed against
the Purdue Enterprise Reference Architecture model and NIST SP 800-207 Zero
Trust Architecture principles.

## 1.3 Scope Definition

The audit scope was defined through a scoping workshop conducted on January 8,
2026, with representation from IT Operations, Information Security, Application
Development, and Facilities Management. The following assets and processes were
included in scope:

**Physical Infrastructure:**
- DC-SOUTH (Dallas, TX) — 22 production servers, 4 network cabinets, 1 SAN array
- DC-CENTRAL (Chicago, IL) — 15 production servers, 3 network cabinets, 1 SAN array
- DC-WEST (Portland, OR) — 10 production servers, 2 network cabinets, 1 NAS cluster

**Application Layer:**
- 12 SaaS applications (including Salesforce, ServiceNow, Microsoft 365, Workday,
  Slack, Datadog, PagerDuty, Jira, Confluence, GitHub Enterprise, Snowflake, and
  Cloudflare)
- 8 internally developed applications hosted across the three data centers
- 3 legacy applications running on end-of-life operating systems

**Operational Processes:**
- Disaster recovery planning and testing cadence
- Change management and release procedures
- Incident response playbooks and escalation paths
- Backup scheduling, verification, and restoration testing
- Privileged access management and credential rotation

The following areas were explicitly excluded from scope: end-user endpoint
devices, mobile device management, physical security controls beyond data center
access, and third-party vendor risk assessments (which are addressed under a
separate engagement, ACME-ENG-INF-003/2026).

## 1.4 Data Collection Methods

Data were collected through five complementary methods, each designed to capture
a distinct dimension of infrastructure health and control effectiveness.

### 1.4.1 Automated Vulnerability Scanning

Authenticated vulnerability scans were executed across all 47 production servers
using Tenable Nessus Professional 10.6. Scans were conducted during maintenance
windows (02:00-06:00 local time) to minimize production impact. Each server
received a full credentialed scan including operating system patch assessment,
application-level vulnerability detection, and configuration compliance checks
against CIS Benchmarks v8. External-facing assets received supplemental scanning
using Qualys WAS for web application vulnerability assessment.

### 1.4.2 Configuration Review

Manual configuration review was performed on all network devices (firewalls,
switches, load balancers), server operating systems, and database instances.
Configurations were exported and analyzed against documented baselines. Where
no documented baseline existed, CIS Benchmark Level 1 profiles were used as
the reference standard. Configuration drift was quantified as the percentage
of benchmark controls in a non-compliant state.

### 1.4.3 Staff Interviews

Semi-structured interviews were conducted with 23 staff members across four
functional areas: IT Operations (8), Information Security (5), Application
Development (6), and IT Management (4). Interview protocols were standardized
to ensure consistent coverage of topics including incident response awareness,
change management adherence, backup procedures, and security policy familiarity.
Each interview lasted 45-60 minutes and was documented in structured field notes.

### 1.4.4 Incident Log Analysis

Incident management records from ServiceNow were analyzed for the 18-month
period from July 2024 through December 2025. The analysis examined incident
volume, severity distribution, mean time to detect (MTTD), mean time to respond
(MTTR), root cause categorization, and recurrence patterns. A total of 1,247
incident records were analyzed, of which 89 were classified as severity 1 or
severity 2.

### 1.4.5 Documentation Review

Existing policy documents, procedures, architecture diagrams, and operational
runbooks were reviewed for currency, completeness, and alignment with actual
practice. The documentation inventory comprised 67 documents across 14 categories.
Each document was assessed for last-review date, owner assignment, version control,
and consistency with observed operational behavior.

## 1.5 Assessment Areas and Tools

| Assessment Area              | Tools and Methods                        | Standards Reference       | Assets in Scope    |
|------------------------------|------------------------------------------|---------------------------|--------------------|
| Vulnerability management     | Tenable Nessus 10.6, Qualys WAS          | NIST CSF PR.IP, CIS v8   | 47 servers, 8 apps |
| Configuration compliance     | Manual review, CIS-CAT Pro               | CIS Benchmarks v8         | 47 servers, 31 network devices |
| Access control               | AD audit, PAM review, MFA assessment     | ISO 27001 A.9, NIST PR.AC | All accounts       |
| Network architecture         | Topology mapping, firewall rule analysis  | NIST SP 800-207           | 3 data centers     |
| Disaster recovery            | DR plan review, tabletop exercise         | NIST CSF RC.RP            | All facilities     |
| Backup and restoration       | Backup log review, restoration testing    | ISO 27001 A.12.3          | All backup targets |
| Incident response            | Playbook review, ServiceNow log analysis  | NIST CSF RS.RP            | 1,247 incidents    |
| Change management            | Process audit, CAB meeting review         | ISO 27001 A.12.1.2        | 342 change records |
| SaaS application security    | Configuration audit, SSO/SCIM assessment  | CIS SaaS Benchmarks       | 12 SaaS apps       |
| Documentation and governance | Document inventory, currency assessment   | ISO 27001 A.5             | 67 documents       |

## 1.6 Risk Scoring Methodology

Findings were scored using a likelihood-by-impact risk matrix consistent with
NIST SP 800-30 Rev. 1 (Guide for Conducting Risk Assessments). Each finding
was assigned a likelihood rating and an impact rating on a five-point scale,
and the composite risk score determined the severity classification.

**Likelihood Scale:**
- 5 (Very High): Exploit code publicly available; active exploitation observed in the wild
- 4 (High): Known vulnerability with proof-of-concept; threat actors targeting similar environments
- 3 (Moderate): Vulnerability exists but exploitation requires specific conditions or insider access
- 2 (Low): Theoretical vulnerability; no known exploitation methods
- 1 (Very Low): Negligible probability under current threat models

**Impact Scale:**
- 5 (Very High): Complete loss of critical business function; regulatory penalty; data breach affecting >10,000 records
- 4 (High): Significant disruption to business operations (>24 hours); financial loss >$500K
- 3 (Moderate): Partial service degradation; financial loss $50K-$500K; limited data exposure
- 2 (Low): Minor operational inconvenience; financial loss <$50K; no data exposure
- 1 (Very Low): Negligible operational or financial impact

**Severity Classification:**

| Composite Score (L x I) | Severity    |
|--------------------------|-------------|
| 20-25                    | Critical    |
| 12-19                    | High        |
| 6-11                     | Medium      |
| 1-5                      | Low         |

Findings classified as Critical or High require remediation within defined SLA
timelines. Medium findings should be addressed within the next planning cycle.
Low findings are documented for awareness and tracked through standard change
management processes.

## 1.7 Compliance Mapping Approach

Each finding was mapped to the relevant NIST CSF 2.0 function and category and
to the corresponding ISO 27001:2022 Annex A control. This dual mapping serves
two purposes: it provides ACME leadership with a framework-aligned view of
organizational risk posture, and it generates a pre-assessment gap analysis for
the planned ISO 27001 certification.

Compliance status for each control area was classified as Implemented, Partially
Implemented, or Not Implemented based on the evidence collected during the audit.
A control was rated Implemented only if documentary evidence, technical evidence,
and interview evidence all confirmed consistent application. Partially Implemented
status was assigned where controls existed in policy but were inconsistently
applied in practice, or where technical controls were present but not monitored.

## 1.8 Limitations

This audit was conducted as a point-in-time assessment and reflects the state
of ACME's infrastructure during the January-March 2026 assessment window.
Changes made after March 14, 2026, are not reflected in this report. The audit
did not include penetration testing or red team exercises; findings are based on
vulnerability scanning, configuration review, and process assessment. Endpoint
devices and third-party vendor risk were excluded from scope as noted in Section
1.3. Staff interview responses are self-reported and may not fully represent
actual operational practice in all cases.
