# Variants

Variants add domain-specific sections to the body of any template. They are auto-detected from content or configured per path.

## Built-in Variants

| Variant | Adds | Auto-detect Keywords |
|---------|------|---------------------|
| `aiml` | Hyperparameter table, benchmark chart | neural, transformer, training, epoch, loss |
| `legal` | Jurisdiction reference, legislation index, case table | statute, jurisdiction, court, plaintiff, regulation |
| `medical` | Drug interaction table, dosage reference, contraindications | patient, dosage, clinical, diagnosis, treatment |
| `engineering` | Safety warnings, spec quick-ref, standards table | tolerance, specification, PSI, torque, assembly |
| `research` | Methodology summary, dataset description, reproducibility checklist | hypothesis, methodology, sample size, p-value, dataset |
| `api` | Endpoint table, auth reference | endpoint, REST, GET, POST, authentication, API |
| `gaming` | Engine architecture, file format table | engine, shader, mesh, texture, .pak, .bsa |
| `finance` | Key metrics dashboard, risk table | revenue, EBITDA, portfolio, risk, compliance |
| `species` | Taxonomy table, conservation status | species, genus, habitat, conservation, morphology |
| `historical` | Timeline, primary source table | century, dynasty, empire, reign, archaeological |
| `hardware` | Pin diagrams, register maps, electrical specs | register, GPIO, voltage, datasheet, pinout |
| `religion` | Tradition comparison, theological positions | theology, scripture, doctrine, worship, denomination |

## Auto-detection

When `variants.auto_detect: true` (default), BriefKit scans the content for keyword matches. A variant activates when 2+ of its keywords appear in the text.

## Manual Configuration

```yaml
variants:
  rules:
    - pattern: "docs/api/**"
      variant: "api"
    - pattern: "docs/legal/**"
      variant: "legal"
  auto_detect: true    # still falls back to auto-detection for unmatched paths
```

## CLI Override

```bash
briefkit generate docs/mixed-content/ --variant legal
```
