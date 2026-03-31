# BriefKit — Safety Framework

**OFFTRACKMEDIA Studios** — ABN 84 290 819 896
**Applies to:** All use of the BriefKit software, templates, variants, and generated output

> **You are required to read and understand this safety documentation before using BriefKit to process directories containing sensitive, regulated, or third-party content.** This is a condition of use under the EULA (Section 3).

---

## Why This Document Exists

BriefKit reads markdown files and source PDFs from the local filesystem, extracts structured content, and generates PDF documents. While the tool itself does not connect to external services or process data beyond the local machine, the content it reads and the PDFs it produces may contain information subject to privacy law, copyright restrictions, or organizational confidentiality requirements.

This safety framework identifies the specific risks and legal obligations relevant to BriefKit use.

---

## Safety Categories

### Category C — Data Privacy and Filesystem Safety

**Applicable to:** All BriefKit operations that read input files or write output PDFs.

**Risks:** Privacy violations, unauthorized disclosure of personal or confidential data, regulatory penalties.

**Key obligations:**

- BriefKit reads all markdown files (`.md`) in the target directory and its subdirectories when using `briefkit batch`. Ensure input directories do not contain files with personal data (names, addresses, health records, financial data, government identifiers) unless you have lawful authority to process and distribute that data in PDF form.
- Output PDFs are written to the filesystem. You are responsible for access controls on output directories and any subsequent distribution of generated PDFs.
- Review the target path before running `briefkit batch` with a broad root directory to avoid processing unintended content.
- BriefKit does not transmit data externally. It operates fully offline. No telemetry, no analytics, no network requests.

**Applicable law:**

| Law | Jurisdiction | Key Provision |
|-----|-------------|---------------|
| Privacy Act 1988 (Cth) | Australia | Australian Privacy Principles — collection, use, and disclosure of personal information |
| GDPR | European Union | Data minimization, lawful basis for processing, data subject rights |
| CCPA | California, USA | Consumer right to know, delete, and opt-out of sale of personal information |

### Category D — Intellectual Property

**Applicable to:** All content processed through BriefKit and all generated PDF output.

**Risks:** Copyright infringement, unauthorized reproduction, attribution failures.

**Key obligations:**

- BriefKit does not assess the copyright status of input content. You are solely responsible for ensuring you have the right to reproduce, transform, and distribute content processed through the tool.
- Generated PDFs that incorporate third-party text, tables, figures, or structured data may require attribution or licensing compliance independent of BriefKit's own license.
- The bibliography extraction feature identifies citations in source material. It does not verify the accuracy or completeness of those citations. You remain responsible for proper attribution.
- If you process content licensed under restrictive terms (e.g., CC BY-ND, proprietary, All Rights Reserved), the generated PDF may constitute an unauthorized derivative work. Verify input content licenses before generation.

**Applicable law:**

| Law | Jurisdiction | Key Provision |
|-----|-------------|---------------|
| Copyright Act 1968 | Australia | Part III — copyright in original works; Part VAA — technological protection measures |
| DMCA (17 U.S.C. §512) | USA | Safe harbors, notice-and-takedown, anti-circumvention |
| EU Copyright Directive 2019/790 | European Union | Articles 3–4 (text and data mining exceptions); Article 17 (platform liability) |

### Category E — Low Risk (Reference Material)

**Applicable to:** BriefKit documentation, configuration files, example projects, color presets, and template definitions.

General reference material with no specific safety obligations beyond standard professional practice.

---

## Filesystem Operations Summary

| Operation | Reads | Writes | Deletes |
|-----------|:-----:|:------:|:-------:|
| `briefkit generate <path>` | Target directory | 1 PDF file | Never |
| `briefkit batch <root>` | All subdirectories recursively | 1 PDF per target directory | Never |
| `briefkit assign-ids <path>` | Target directory | Registry JSON file | Never |
| `briefkit init` | Nothing | 1 YAML config file | Never |
| `briefkit selftest` | Built-in fixtures | 1 temporary PDF | Never |

BriefKit never deletes files. It never modifies source markdown files. It only writes output PDFs and registry/config files.

---

## Incident Reporting

If you discover that BriefKit has processed content it should not have, or if generated output has been distributed in violation of applicable law:

1. **Stop distribution** of the affected PDFs immediately
2. **Report the incident** at https://github.com/otmof-ops/briefkit/issues
3. **Document** what content was processed, what output was generated, and how it was distributed

---

## Disclaimer

OFFTRACKMEDIA Studios accepts no liability for injury, damage, or loss arising from the use or misuse of BriefKit or content generated by BriefKit. Users are responsible for:

- Verifying the accuracy and applicability of all generated content
- Complying with all applicable laws and regulations in their jurisdiction
- Obtaining appropriate professional advice where required
- Maintaining access controls on generated output

See the EULA (Section 9 — Warranty Disclaimer, Section 10 — Limitation of Liability) for full terms.

---

(c) 2026 OFFTRACKMEDIA Studios · ABN 84 290 819 896
