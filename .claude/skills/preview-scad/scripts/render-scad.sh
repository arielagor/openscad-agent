#!/bin/bash

# OpenSCAD Preview Renderer
# Renders .scad files to PNG images for visual verification
# Cross-platform: macOS, Linux, Windows (Git Bash/MSYS2)

set -e

# Default values
SIZE="800x600"
COLORSCHEME="Cornfield"
RENDER_MODE="preview"
OUTPUT=""
CAMERA=""

# ── Find OpenSCAD (cross-platform) ──────────────────────────
find_openscad() {
    # 1. Check PATH first
    if command -v openscad &> /dev/null; then
        echo "openscad"
        return 0
    fi

    # 2. macOS default
    if [[ -x "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD" ]]; then
        echo "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"
        return 0
    fi

    # 3. Windows Program Files
    for pf in "/c/Program Files/OpenSCAD" "/c/Program Files (x86)/OpenSCAD" \
              "$PROGRAMFILES/OpenSCAD" "${PROGRAMFILES:-}/OpenSCAD"; do
        if [[ -x "$pf/openscad.exe" ]] || [[ -x "$pf/openscad" ]]; then
            echo "$pf/openscad"
            return 0
        fi
        # Also check if just the dir exists (exe may not have .exe in git bash)
        if [[ -d "$pf" ]]; then
            export PATH="$PATH:$pf"
            if command -v openscad &> /dev/null; then
                echo "openscad"
                return 0
            fi
        fi
    done

    # 4. Linux common paths
    for p in /usr/bin/openscad /usr/local/bin/openscad /snap/bin/openscad; do
        if [[ -x "$p" ]]; then
            echo "$p"
            return 0
        fi
    done

    return 1
}

OPENSCAD=$(find_openscad) || {
    echo "Error: OpenSCAD not found."
    echo "Install from https://openscad.org/ or via:"
    echo "  macOS:   brew install openscad"
    echo "  Linux:   sudo apt install openscad"
    echo "  Windows: winget install OpenSCAD.OpenSCAD"
    exit 1
}

echo "Using OpenSCAD: $OPENSCAD"

# Parse arguments
INPUT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --size)
            SIZE="$2"
            shift 2
            ;;
        --camera)
            CAMERA="$2"
            shift 2
            ;;
        --colorscheme)
            COLORSCHEME="$2"
            shift 2
            ;;
        --render)
            RENDER_MODE="render"
            shift
            ;;
        --preview)
            RENDER_MODE="preview"
            shift
            ;;
        --help|-h)
            echo "Usage: render-scad.sh <input.scad> [options]"
            echo ""
            echo "Options:"
            echo "  --output <path>       Output PNG path (default: <input>.png)"
            echo "  --size <WxH>          Image size (default: 800x600)"
            echo "  --camera <params>     Camera position: x,y,z,tx,ty,tz,d"
            echo "  --colorscheme <name>  Color scheme (default: Cornfield)"
            echo "  --render              Full render mode (slower, accurate)"
            echo "  --preview             Preview mode (faster, default)"
            echo ""
            echo "Common camera angles for jewelry/pendants:"
            echo "  Front:   --camera 0,0,0,11,3.5,20,80"
            echo "  3/4:     --camera 30,20,25,11,3.5,20,80"
            echo "  Side:    --camera 90,0,20,11,3.5,20,80"
            echo ""
            echo "Example:"
            echo "  render-scad.sh model.scad --size 1024x768"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            if [[ -z "$INPUT" ]]; then
                INPUT="$1"
            else
                echo "Error: Multiple input files specified"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate input
if [[ -z "$INPUT" ]]; then
    echo "Error: No input file specified"
    echo "Usage: render-scad.sh <input.scad> [options]"
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file not found: $INPUT"
    exit 1
fi

# Determine output path
if [[ -z "$OUTPUT" ]]; then
    BASENAME="${INPUT%.scad}"
    OUTPUT="${BASENAME}.png"
fi

# Store output path before it gets clobbered
OUT_PATH="$OUTPUT"

# Build OpenSCAD command
CMD=("$OPENSCAD")
CMD+=("--viewall" "--autocenter")
CMD+=("--imgsize" "${SIZE/x/,}")
CMD+=("--colorscheme" "$COLORSCHEME")

if [[ -n "$CAMERA" ]]; then
    CMD+=("--camera" "$CAMERA")
fi

if [[ "$RENDER_MODE" == "preview" ]]; then
    CMD+=("--preview")
fi

CMD+=("-o" "$OUT_PATH")
CMD+=("$INPUT")

# Run OpenSCAD
echo "Rendering: $INPUT -> $OUT_PATH"
echo "Mode: $RENDER_MODE, Size: $SIZE"

RENDER_OUTPUT=$("${CMD[@]}" 2>&1) || true

if [[ -f "$OUT_PATH" ]]; then
    FILE_SIZE=$(ls -lh "$OUT_PATH" 2>/dev/null | awk '{print $5}')
    echo "Success: Preview saved to $OUT_PATH ($FILE_SIZE)"
else
    echo "Render may have failed. OpenSCAD output:"
    echo "$RENDER_OUTPUT"
    exit 1
fi
