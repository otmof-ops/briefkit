# Customization

BriefKit works with zero configuration, but every aspect of the output can be customized through a `briefkit.yml` file in your project root.

## Color Presets

Switch the entire visual theme with a single line:

```yaml
brand:
  preset: "ocean"
```

| Preset | Style | Best For |
|--------|-------|----------|
| `navy` | Professional blue (default) | Corporate, institutional |
| `charcoal` | Dark neutral grey | Consulting, finance |
| `ocean` | Blue-teal gradient | Tech, startups |
| `forest` | Green-earth tones | Environment, sustainability |
| `crimson` | Red-dark accents | Law, government |
| `slate` | Cool grey | Engineering, minimal |
| `royal` | Purple-gold | Academic, research |
| `sunset` | Warm orange | Creative, media |
| `mono` | Pure black and white | Print-first, reference |
| `midnight` | Dark mode palette | Screen reading |

## Custom Colors

Override individual colors for full brand control:

```yaml
brand:
  preset: "custom"
  primary: "#1B2A4A"
  secondary: "#2E86AB"
  accent: "#E8C547"
  body_text: "#2C2C2C"
  caption: "#666666"
  background: "#FFFFFF"
  rule: "#CCCCCC"
```

## Project Identity

Configure your organization's branding on cover pages and headers:

```yaml
project:
  name: "My Documentation"
  org: "My Organization"
  tagline: "Building Better Documentation"
  url: "https://example.com"
  copyright: "© {year} My Organization"
```

## Document IDs

Enable automatic document ID tracking for version control:

```yaml
doc_ids:
  enabled: true
  prefix: "DOC"
  format: "{prefix}-{group}-{seq:04d}/{year}"
```

## Configuration Precedence

Settings are resolved in this order (highest to lowest):

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | CLI flags | `--template report --preset charcoal` |
| 2 | `briefkit.yml` in project root | `template.preset: "report"` |
| 3 | Built-in defaults | briefing template, navy preset |

> For the full configuration reference with every available option, see [docs/configuration.md](../../../../docs/configuration.md).
