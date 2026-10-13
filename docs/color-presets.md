# Color Presets

Switch the entire look with one line in your configuration: `brand.preset` in `briefkit.yml`, or `--preset NAME` on the command line. `briefkit presets` prints every preset with all sixteen values; `briefkit presets --quiet` prints the names.

## The presets

| Preset | Character | Primary | Secondary | Accent | Background | Body font |
|---|---|---|---|---|---|---|
| `arctic` | Ice blue: cool, technical | `#0a3d62` | `#3c6382` | `#82ccdd` | `#FFFFFF` | Helvetica |
| `charcoal` | Dark neutral: consulting, finance | `#2D2D2D` | `#5C8A97` | `#D4A853` | `#FFFFFF` | Helvetica |
| `corporate` | Blue-gray with red accent: corporate | `#2c3e50` | `#3498db` | `#e74c3c` | `#FFFFFF` | Helvetica |
| `crimson` | Red-dark: law, government, compliance | `#590D22` | `#A4133C` | `#FFCCD5` | `#FFFFFF` | Helvetica |
| `cyber` | Near-black with electric blue and teal: security, infrastructure | `#0C1116` | `#57A5FF` | `#38D1BF` | `#FFFFFF` | Helvetica |
| `deep-research` | Near-black with teal accent: research reports | `#0F1318` | `#00D4AA` | `#00D4AA` | `#FFFFFF` | Helvetica |
| `emerald` | Green accent: fresh, modern | `#10ac84` | `#1dd1a1` | `#feca57` | `#FFFFFF` | Helvetica |
| `forest` | Green-earth: environment, sustainability | `#1B4332` | `#40916C` | `#D4A373` | `#FFFFFF` | Helvetica |
| `gothic` | Near-black on warm off-white, Times: literary | `#1A1A1A` | `#4A4A4A` | `#8B7355` | `#FAFAF5` | Times-Roman |
| `ink` | Charcoal with orange accent, Times: editorial | `#222f3e` | `#576574` | `#ff9f43` | `#FFFFFF` | Times-Roman |
| `midnight` | Dark mode: screen reading | `#E0E0E0` | `#64B5F6` | `#FFE082` | `#121212` | Helvetica |
| `mono` | Black and white, Courier: print-first | `#000000` | `#333333` | `#F0F0F0` | `#FFFFFF` | Courier |
| `navy` | Professional, institutional (default) | `#1B2A4A` | `#2E86AB` | `#E8C547` | `#FFFFFF` | Helvetica |
| `neon` | Dark page with cyan and violet: screens only | `#0A0E16` | `#00E4FF` | `#B387FF` | `#0A0E16` | Helvetica |
| `neon-print` | The neon palette rebalanced for white paper | `#1A1F2B` | `#0077B5` | `#C3B5FD` | `#FFFFFF` | Helvetica |
| `ocean` | Blue-teal: tech, startups | `#0A2463` | `#1E96FC` | `#FFC600` | `#FFFFFF` | Helvetica |
| `royal` | Purple-gold, Times: academic, research | `#2D1B69` | `#7B2FBE` | `#FFD700` | `#FFFFFF` | Times-Roman |
| `slate` | Cool gray: minimal, engineering | `#37474F` | `#607D8B` | `#80CBC4` | `#FFFFFF` | Helvetica |
| `sunset` | Warm orange on cream: creative, media | `#3D1C02` | `#E85D04` | `#FAA307` | `#FFFCF7` | Helvetica |
| `terracotta` | Plum and pink: distinctive, warm | `#6F1E51` | `#B53471` | `#FDA7DF` | `#FFFFFF` | Helvetica |

`midnight` and `neon` carry a dark page color for screen reading; a template that does not paint the page background shows their light text on white, so use `neon-print` or any light preset for paper.

## Usage

```yaml
# briefkit.yml
brand:
  preset: "ocean"
```

```bash
briefkit generate docs/my-topic/ --preset crimson
```

## Custom colors

Every preset sets twelve colors and four fonts. Any key you set in `brand:` overrides the preset's value; `preset: "custom"` starts from the defaults instead of a preset. Colors are 6-digit hex strings and must be quoted in YAML.

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

Fonts are the PDF base fourteen: Helvetica, Times and Courier in their regular, bold, oblique and bold-oblique cuts. How each key is used, and how to combine a preset with a logo: [presets-guide.md](presets-guide.md).
