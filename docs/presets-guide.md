# Presets Guide

Presets control the visual appearance of generated PDFs -- colors, fonts, and overall feel. Changing the preset changes the entire look with one line.

---

## Available Presets

BriefKit ships with 15 built-in color presets:

| Preset | Style | Primary Color | Font Family |
|--------|-------|--------------|-------------|
| `navy` | Professional, institutional **(default)** | `#1B2A4A` | Helvetica |
| `charcoal` | Dark neutral -- consulting, finance | `#2D2D2D` | Helvetica |
| `ocean` | Blue-teal -- tech, startups | `#0A2463` | Helvetica |
| `forest` | Green-earth -- environment, sustainability | `#1B4332` | Helvetica |
| `crimson` | Red-dark -- law, government | `#590D22` | Helvetica |
| `slate` | Cool grey -- minimal, engineering | `#37474F` | Helvetica |
| `royal` | Purple-gold -- academic, research | `#2D1B69` | Times-Roman |
| `sunset` | Warm orange -- creative, media | `#3D1C02` | Helvetica |
| `mono` | Pure black and white -- print-first | `#000000` | Courier |
| `midnight` | Dark mode -- screen reading | `#E0E0E0` (on `#121212` background) | Helvetica |
| `emerald` | Green accent -- fresh, modern | `#10ac84` | Helvetica |
| `corporate` | Standard corporate -- clean, professional | `#2c3e50` | Helvetica |
| `arctic` | Ice blue -- cool, technical | `#0a3d62` | Helvetica |
| `terracotta` | Pink-plum -- distinctive, warm | `#6F1E51` | Helvetica |
| `ink` | Muted with orange accent -- editorial | `#222f3e` | Times-Roman |

---

## How to Select a Preset

### Via CLI Flag

```bash
briefkit generate docs/my-topic/ --preset ocean
briefkit generate docs/my-topic/ -p crimson
```

### Via Config File

```yaml
# briefkit.yml
brand:
  preset: ocean
```

### Default

If no preset is specified, BriefKit uses `navy`.

---

## List All Presets with Colors

```bash
briefkit presets
```

Output:

```
  navy
    primary      #1B2A4A
    secondary    #2E86AB
    accent       #E8C547
    body_text    #2C2C2C
    ...

  charcoal
    primary      #2D2D2D
    secondary    #5C8A97
    ...
```

For JSON output:

```bash
briefkit presets --json
```

---

## Color Keys Explained

Every preset defines 16 keys:

| Key | What It Controls |
|-----|-----------------|
| `primary` | Headers, cover page, accent bars, dominant brand color |
| `secondary` | Sub-headers, links, chart bars, supporting brand color |
| `accent` | Highlights, call-outs, badges |
| `body_text` | Main body copy |
| `caption` | Captions, footnotes, supporting text |
| `background` | Page / panel background |
| `rule` | Horizontal rules, table borders, dividers |
| `success` | Positive / success indicators (charts, badges) |
| `warning` | Warning indicators |
| `danger` | Error / danger indicators |
| `code_bg` | Code block background fill |
| `table_alt` | Alternating table row background |
| `font_body` | Body text font family |
| `font_heading` | Heading font family |
| `font_mono` | Code / monospace font family |
| `font_caption` | Caption / oblique font family |

---

## Overriding Individual Colors

Use `preset: custom` and specify each color explicitly:

```yaml
brand:
  preset: custom
  primary: "#003366"
  secondary: "#0066CC"
  accent: "#FF9900"
  body_text: "#333333"
  caption: "#666666"
  background: "#FFFFFF"
  rule: "#CCCCCC"
```

Or override specific colors on top of an existing preset:

```yaml
brand:
  preset: ocean
  accent: "#FF0000"          # override just the accent color
```

The resolution order is:
1. Preset values (fill all 16 keys)
2. Your explicit overrides (win over preset values)

---

## Overriding Fonts

```yaml
brand:
  preset: navy
  font_body: "Times-Roman"
  font_heading: "Times-Bold"
  font_mono: "Courier"
  font_caption: "Times-Italic"
```

Available fonts are limited to those bundled with ReportLab:
- `Helvetica`, `Helvetica-Bold`, `Helvetica-Oblique`, `Helvetica-BoldOblique`
- `Times-Roman`, `Times-Bold`, `Times-Italic`, `Times-BoldItalic`
- `Courier`, `Courier-Bold`, `Courier-Oblique`, `Courier-BoldOblique`

---

## Choosing the Right Preset

| Use Case | Recommended Preset |
|----------|-------------------|
| Client-facing executive briefings | `navy`, `charcoal`, `corporate` |
| Tech startup documentation | `ocean`, `emerald` |
| Academic/research papers | `royal`, `ink` |
| Legal/government reports | `crimson` |
| Engineering/technical manuals | `slate`, `arctic` |
| Environmental/sustainability | `forest` |
| Creative/media briefs | `sunset`, `terracotta` |
| Print-first (no color) | `mono` |
| Screen reading (dark mode) | `midnight` |
| General purpose | `navy` (default) |

---

## Creating a Fully Custom Preset

For complete control, set `preset: custom` and define every color:

```yaml
brand:
  preset: custom
  primary: "#1A1A2E"
  secondary: "#16213E"
  accent: "#E94560"
  body_text: "#2C2C2C"
  caption: "#666666"
  background: "#FFFFFF"
  rule: "#CCCCCC"
  success: "#00b894"
  warning: "#fdcb6e"
  danger: "#d63031"
  code_bg: "#f5f6fa"
  table_alt: "#f8f9fa"
  font_body: "Helvetica"
  font_heading: "Helvetica-Bold"
  font_mono: "Courier"
  font_caption: "Helvetica-Oblique"
```

All color values must be 6-digit hex codes (e.g., `#1B2A4A`). The config validator will reject invalid colors.

---

## Adding a Logo

```yaml
brand:
  preset: ocean
  logo: "path/to/logo.png"
```

The logo appears on the cover page. Supports PNG and JPEG formats.

---

## Comparing Presets Visually

Generate the same document with different presets:

```bash
for preset in navy charcoal ocean forest crimson slate royal; do
  briefkit generate docs/my-topic/ --preset $preset --output "${preset}-preview.pdf"
done
```
