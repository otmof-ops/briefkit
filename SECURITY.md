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

- The `briefkit` package as installed from this repository (there is no PyPI release yet)
- The source code in this repository
- Generated output behavior (for example PDF metadata injection, link actions, path traversal)

Out of scope:

- Third-party dependencies (report those to the relevant upstream project)
- Content accuracy in generated PDFs (content is a user responsibility)

---

## Security Standards

| Practice | Standard |
|----------|----------|
| Secrets in code | Prohibited; no hardcoded credentials |
| Input validation | Applied at all system boundaries: configuration values, output paths, registry path, Markdown and brand strings |
| Dependencies | Minimized: three runtime dependencies (ReportLab, PyYAML, Pillow); pypdf optional for read-back checks; pip-audit runs in CI |
| Offline operation | No external API calls, no update check, no telemetry during PDF generation |
| Network backstop | ReportLab is configured to trust no remote host and only inline `data:` URIs, so markup that slipped past escaping still cannot fetch anything |
| Filesystem access | Reads the source directory and the configuration; writes only the output PDF (through a sibling `.part` file), the document-ID registry and, for `init`, the configuration file |
| SQL / query injection | Not applicable; no database connections |
| Code execution | No `eval()` or `exec()` with user input |

---

## Untrusted content

briefkit is normally run over Markdown someone else wrote (a pull request to a
docs repository, a cloned tree). The boundaries it enforces:

- **Links.** Only `http`, `https`, `mailto` and in-document `#anchor` targets
  become PDF link actions. `javascript:`, `file:`, `smb:`, custom scheme
  handlers, UNC paths and relative file paths are rendered as their label
  text. An anchor that names no heading lands on page 1 instead of aborting
  the build.
- **Markup.** Document titles, directory names, organization strings and dates
  are escaped before they reach ReportLab's paragraph parser, so `<img>` or an
  unbalanced `<b>` in a README heading is printed, not interpreted.
- **Files.** Symlinks are not followed and files over 10 MB are skipped when
  sources are read; Markdown bodies are parsed with bounded regular
  expressions so a crafted document cannot stall the build.
- **Output paths.** `output.filename` must be a bare `.pdf` name;
  `output.output_dir` may not walk upwards; the resolved path must stay inside
  the output directory. The doc-ID registry must resolve inside the project
  root, whether its configured path is relative or absolute.
- **Atomic writes.** A PDF is rendered to a sibling `.part` file and moved into
  place only when the build succeeds; a failed build never truncates the
  previous output.

---

## Acknowledgments

Responsible disclosures are acknowledged in the changelog. Reporters who wish to remain anonymous will have their identity protected.

---

Copyright (c) 2026 Jay Taylor (https://github.com/otmof-ops/briefkit)
