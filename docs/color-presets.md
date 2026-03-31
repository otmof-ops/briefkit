# Color Presets

Switch the entire look with one line in your config.

## Available Presets

### navy (default)
Professional, institutional.
- Primary: `#1B2A4A` | Secondary: `#2E86AB` | Accent: `#E8C547`

### charcoal
Dark neutral — consulting, finance.
- Primary: `#2D2D2D` | Secondary: `#5C8A97` | Accent: `#D4A853`

### ocean
Blue-teal — tech, startups.
- Primary: `#0A2463` | Secondary: `#1E96FC` | Accent: `#FFC600`

### forest
Green-earth — environment, sustainability.
- Primary: `#1B4332` | Secondary: `#40916C` | Accent: `#D4A373`

### crimson
Red-dark — law, government, compliance.
- Primary: `#590D22` | Secondary: `#A4133C` | Accent: `#FFCCD5`

### slate
Cool grey — minimal, engineering.
- Primary: `#37474F` | Secondary: `#607D8B` | Accent: `#80CBC4`

### royal
Purple-gold — academic, research.
- Primary: `#2D1B69` | Secondary: `#7B2FBE` | Accent: `#FFD700`

### sunset
Warm orange — creative, media, design.
- Primary: `#3D1C02` | Secondary: `#E85D04` | Accent: `#FAA307`

### mono
Pure black and white — print-first, maximum readability.
- Primary: `#000000` | Secondary: `#333333` | Accent: `#F0F0F0`

### midnight
Dark mode — inverted for screen reading.
- Primary: `#E0E0E0` | Secondary: `#64B5F6` | Accent: `#FFE082`

## Usage

```yaml
# briefkit.yml
brand:
  preset: "ocean"
```

```bash
# CLI override
briefkit generate docs/ --preset crimson
```

## Custom Colors

Set `preset: "custom"` and define your own:

```yaml
brand:
  preset: "custom"
  primary: "#1A1A2E"
  secondary: "#0984E3"
  accent: "#F39C12"
  body_text: "#2D3436"
  caption: "#636E72"
  background: "#FFFFFF"
  rule: "#DFE6E9"
```
