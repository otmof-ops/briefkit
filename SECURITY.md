# Security Policy

**OFFTRACKMEDIA Studios** — ABN 84 290 819 896

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x (latest) | Yes |
| < 1.0 | No |

---

## Reporting a Vulnerability

**Do not file public GitHub issues for security vulnerabilities.**

To report a vulnerability responsibly:

1. Email the maintainers at the contact address listed on the [OFFTRACKMEDIA Studios GitHub profile](https://github.com/otmof-ops).
2. Include in your report:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested mitigations (optional)
3. Allow up to 7 business days for an initial response.
4. Allow up to 90 days for remediation before public disclosure.

---

## Scope

This policy covers:

- The `briefkit` Python package published to PyPI
- The source code in this repository
- Generated output behavior (e.g., PDF metadata injection, path traversal)

Out of scope:

- Third-party dependencies (report those to the relevant upstream project)
- Content accuracy in generated PDFs (content is a user responsibility)

---

## Security Standards

| Practice | Standard |
|----------|----------|
| Secrets in code | Prohibited — no hardcoded credentials |
| Input validation | Applied at all system boundaries |
| Dependencies | Minimized — two runtime dependencies (ReportLab, PyYAML) |
| Offline operation | No external API calls during PDF generation |
| Filesystem access | Read-only on source files; write-only for output PDFs and registry |
| SQL / query injection | Not applicable — no database connections |
| Code execution | No `eval()` or `exec()` with user input |

---

## Acknowledgments

Responsible disclosures are acknowledged in the changelog. Reporters who wish to remain anonymous will have their identity protected.

---

(c) 2026 OFFTRACKMEDIA Studios · ABN 84 290 819 896
