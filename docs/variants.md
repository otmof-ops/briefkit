# Variants

Variants add domain-specific sections to the `briefing`, `report`, `manual` and `academic` templates. The fixed-format templates (decks, certificates, invoices, resumes and the rest) never add them.

## Built-in variants

| Variant | Adds | Auto-detect keywords (examples) |
|---------|------|---------------------|
| `aiml` | Hyperparameter table, benchmark chart | neural, transformer, training, epoch, loss |
| `legal` | Jurisdiction reference, legislation index, case table | statute, jurisdiction, court, plaintiff, regulation |
| `medical` | Drug interaction table, dosage reference, contraindications | patient, dosage, clinical, diagnosis, treatment |
| `engineering` | Safety warnings, spec quick-ref, standards table | tolerance, specification, PSI, torque, assembly |
| `research` | Methodology summary, dataset description, reproducibility checklist | hypothesis, methodology, sample size, p-value, dataset |
| `api` | Endpoint table, auth reference | endpoint, REST, GET, POST, authentication, API |
| `gaming` | Engine architecture, file format table | engine, shader, mesh, texture, .pak, .bsa |
| `finance` | Key metrics dashboard, risk table, disclaimer | revenue, EBITDA, portfolio, risk, compliance |
| `species` | Taxonomy table, conservation status | species, genus, habitat, conservation, morphology |
| `historical` | Timeline, primary source table | century, dynasty, empire, reign, archaeological |
| `hardware` | Pin diagrams, register maps, electrical specs | register, GPIO, voltage, datasheet, pinout |
| `religion` | Tradition comparison, theological positions | theology, scripture, doctrine, worship, denomination |

## How a variant is chosen

1. `--variant NAME` on the command line (`--variant none` suppresses variants).
2. The first `variants.rules` entry whose pattern matches the directory's path relative to the project root.
3. Auto-detection, when `variants.auto_detect` is true (the default): keywords are counted as whole words, case-insensitively, and the variant with the most hits wins if it has at least two.

```yaml
variants:
  auto_detect: true
  rules:
    - pattern: "docs/api/**"
      variant: "api"
    - pattern: "docs/legal/**"
      variant: "legal"
```

```bash
briefkit generate docs/mixed-content/ --variant legal
briefkit generate docs/tax-pack/ --variant none
```

Variant sections are placed before the back cover. Writing your own: [custom-variants.md](custom-variants.md).
