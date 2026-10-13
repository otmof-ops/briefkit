# Document IDs

BriefKit assigns a persistent document ID to every generated briefing. The ID is recorded in a registry, printed on the cover, and stored in the PDF's `/Keywords`.

## Format

```
DOC-BRF-GET-30001/26
```

| Part | Meaning | Setting |
|---|---|---|
| `DOC` | prefix | `doc_ids.prefix` |
| `BRF` | document type | `doc_ids.type` |
| `GET` | group code | `doc_ids.group_codes`, else the first three letters of the directory's own name, upper-cased |
| `3` | briefing level | from the hierarchy (see below) |
| `0001` | sequence, per group and level | `doc_ids.sequence_digits` |
| `26` | year of first assignment | `doc_ids.year_format` (`short` or `full`) |

```yaml
doc_ids:
  enabled: true
  format: "{prefix}-{type}-{group}-{level}{seq}/{year}"   # only these six placeholders are allowed
  prefix: "DOC"
  type: "BRF"
  year_format: "short"
  sequence_digits: 4
  registry_path: ".briefkit/registry.json"
  group_codes:
    api: "API"
    backend: "BE"
```

A corporate example: `prefix: ACME-ENG` with `group_codes: {api: API}` gives `ACME-ENG-BRF-API-30001/26` for a documentation set under `api/`.

## Level

The level comes from the project hierarchy: `hierarchy.depth_to_level` maps the directory's depth below the project root (`{0: 1, 1: 2, 2: 3}` by default), and a directory that holds numbered documents is a documentation set (level 3) whatever its depth. Without a project root the tree itself decides (children that are documentation sets make a subject, grandchildren a division; otherwise `root_level`, 4).

## Group codes

`group_codes` keys are matched against every component of the directory's path, from the root down; the first match wins. Without a match the code is the first three characters of the directory's own name, upper-cased, with `-` replaced by `X`.

## Rules

1. IDs are permanent: a briefing keeps its ID across regenerations (the registry key is the directory's resolved path plus the output file name).
2. Sequences count per group and per level and are never reused.
3. The year is the year of first assignment, not of regeneration. With `SOURCE_DATE_EPOCH` set, that date is the one used.
4. The registry is written under a lock, so concurrent `batch` runs never issue the same ID twice.
5. An unreadable or corrupt registry is an error, never a silent reset (a reset would renumber every document).

## Registry

`.briefkit/registry.json` is anchored at the project root that owns the directory being generated (the `briefkit.yml`, `briefkit.yaml` or `.briefkit/` found walking upward from it), or at the current directory when there is none. A relative path stays inside the root by construction; an absolute path, or one with `..`, must resolve inside the root or the configuration is rejected. Commit the registry: it is the record of every ID issued.

## Commands

```bash
briefkit generate docs/my-topic/          # assigns (or reuses) the ID
briefkit generate docs/my-topic/ --no-ids # no ID
briefkit assign-ids docs/                 # registers IDs for directories whose PDF already exists; Markdown is never modified
briefkit assign-ids docs/ --dry-run       # what would be assigned
```
