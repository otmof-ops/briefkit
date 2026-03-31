# Document IDs

BriefKit assigns unique, persistent document IDs to every generated briefing. IDs are stored in a registry and embedded in PDF metadata and on the cover page.

## Default Format

```
DOC-BRF-30001/26
```

- `DOC` — prefix (configurable)
- `BRF` — document type (configurable)
- `3` — hierarchy level (1=top, 2=mid, 3=leaf, 4=special)
- `0001` — sequence number (per group per level)
- `26` — year of first assignment

## Configuration

```yaml
# Minimal (default)
doc_ids:
  enabled: true
# Produces: DOC-BRF-30001/26

# Corporate style
doc_ids:
  prefix: "ACME-ENG"
  group_codes:
    api: "API"
    backend: "BE"
    frontend: "FE"
# Produces: ACME-ENG-BRF-API-30001/26

# Disabled
doc_ids:
  enabled: false
```

## Rules

1. IDs are permanent — a briefing keeps its ID across regenerations
2. Sequences are per-group, per-level, never reused
3. Year is year of first assignment, not regeneration
4. Group codes are auto-generated from top-level directory names unless overridden

## Registry

The registry is stored at `.briefkit/registry.json` (configurable). It tracks all assigned IDs, paths, and metadata.

## CLI

```bash
# Assign IDs without regenerating
briefkit assign-ids docs/

# Generate with IDs disabled
briefkit generate docs/ --no-ids
```
