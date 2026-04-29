#!/bin/bash
# Download the three TTF fonts the gothic-novel typesetter expects.
# Idempotent — safe to re-run.
#
# Output: ./fonts/Cardo-Regular.ttf, Cardo-Italic.ttf, Cardo-Bold.ttf,
#         UnifrakturMaguntia-Regular.ttf, CormorantGaramond-Regular.ttf
#
# All three are open-source (Cardo: SIL OFL; UnifrakturMaguntia: SIL OFL;
# Cormorant Garamond: SIL OFL). Pulled from Google's googlefonts repo on
# raw.githubusercontent.com so we get the source TTF, not the woff2 the
# Google Fonts CDN serves to modern browsers.

set -e

FONTS_DIR="${1:-$(dirname "$0")/fonts}"
mkdir -p "$FONTS_DIR"
cd "$FONTS_DIR"

RAW="https://raw.githubusercontent.com/google/fonts/main/ofl"

declare -A FILES=(
    [Cardo-Regular.ttf]="$RAW/cardo/Cardo-Regular.ttf"
    [Cardo-Italic.ttf]="$RAW/cardo/Cardo-Italic.ttf"
    [Cardo-Bold.ttf]="$RAW/cardo/Cardo-Bold.ttf"
    [UnifrakturMaguntia-Regular.ttf]="$RAW/unifrakturmaguntia/UnifrakturMaguntia-Book.ttf"
    [CormorantGaramond-Regular.ttf]="$RAW/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf"
)

for filename in "${!FILES[@]}"; do
    if [ -f "$filename" ] && [ -s "$filename" ]; then
        echo "✓ $filename (already present)"
        continue
    fi
    url="${FILES[$filename]}"
    echo "Downloading $filename..."
    curl -fsSLo "$filename" "$url"
    if [ ! -s "$filename" ]; then
        echo "  ✗ failed: $url"
        rm -f "$filename"
        exit 1
    fi
    # Verify it's actually a TTF (not an HTML 404 page)
    if ! file "$filename" | grep -q "TrueType"; then
        echo "  ✗ not a TTF file: $filename"
        file "$filename"
        rm -f "$filename"
        exit 1
    fi
    echo "  ✓ downloaded"
done

echo
echo "Fonts installed in: $FONTS_DIR"
echo "If running the typesetters from a different location, set:"
echo "  export GOTHIC_FONTS_DIR=$FONTS_DIR"
