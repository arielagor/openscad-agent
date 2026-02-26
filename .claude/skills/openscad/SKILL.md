---
name: openscad
description: Create versioned OpenSCAD (.scad) files for 3D printing, render previews, and compare iterations. Use this when designing or iterating on 3D models.
allowed-tools:
  - Bash(*/render-scad.sh*)
  - Bash(*/version-scad.sh*)
  - Bash(*/export-stl.sh*)
  - Bash(*openscad*)
  - Bash(*python*)
  - Read
  - Write
  - Glob
  - Task
---

# OpenSCAD Design Skill

Create versioned OpenSCAD files, render previews, and compare iterations for 3D printing designs.

## Workflow

### 1. Determine the Next Version Number

Before creating a new .scad file, find existing versions:

```bash
.claude/skills/openscad/scripts/version-scad.sh <name>
```

This returns the next version number and filename. For example, if `piano_001.scad` exists, it returns `piano_002`.

### 2. Create the Versioned .scad File

Write the OpenSCAD code to the versioned filename (e.g., `piano_002.scad`).

### 3. Render the Preview

```bash
.claude/skills/preview-scad/scripts/render-scad.sh <name>_<version>.scad --output <name>_<version>.png
```

This creates a PNG with the matching version number (e.g., `piano_002.png`).

### 4. Compare with Previous Version

Read both the current and previous PNG images to visually compare:

- Current: `piano_002.png`
- Previous: `piano_001.png` (if exists)

Evaluate what changed and whether the new version better matches requirements.

### 5. Iterate

If the design needs improvement:
1. Analyze what's wrong — be specific (e.g., "ribbon too thin", "drip too flat")
2. Create the next version (e.g., `piano_003.scad`)
3. Render and compare again

## Matching a Reference Image

When the user provides a reference image to replicate:

1. **Decompose** the reference into distinct elements (cage, ribbon, blob, etc.)
2. **Start with structure** — get the main shape/proportions right first
3. **Layer in details** — add decorative elements one at a time
4. **Compare methodically** — after each render, list specific differences from the reference
5. **Parallelize** — for complex designs, use Task agents to iterate on different elements simultaneously, then combine the best of each

### Parallel Iteration Strategy

For complex models, launch multiple agents working on different aspects:
- Agent A: Ribbon/curves
- Agent B: Organic/blob forms
- Agent C: Structural proportions
- Agent D: Overall composition

Then use a judge agent to pick the best elements and combine them.

## File Naming Convention

```
<model-name>_<version>.scad  ->  <model-name>_<version>.png
```

- Use underscores in model names
- Use 3-digit zero-padded version numbers (001, 002, etc.)
- For parallel agents: `<model-name>_<agent>_<version>.scad` (e.g., `pendant_A_001.scad`)

## Render Options

```bash
.claude/skills/preview-scad/scripts/render-scad.sh <input.scad> [options]
```

- `--output <path>` — Output PNG path (default: `<input>.png`)
- `--size <WxH>` — Image dimensions (default: `800x600`, use `1024x768` for detail)
- `--camera <x,y,z,tx,ty,tz,d>` — Camera position
- `--colorscheme <name>` — Color scheme (default: `Cornfield`)
- `--render` — Full render mode (slower, accurate)
- `--preview` — Preview mode (faster, default)

### Useful Camera Angles

- Default (auto): omit `--camera` for automatic viewall
- Front: `--camera 0,-80,20,11,3.5,20,80`
- 3/4 view: `--camera 30,20,25,11,3.5,20,80`
- Side: `--camera 90,0,20,11,3.5,20,80`

## OpenSCAD Techniques

### Organic/Flowing Shapes
- **Tubular paths**: Chain `hull()` between consecutive `sphere()` placements along a parametric curve
- **Ribbons**: Use `hull()` between `scale([thin, wide, 1]) sphere(r)` pairs for flat ribbon cross-sections
- **Puddles/blobs**: Layer multiple `scale([x,y,z]) sphere(r)` with different flattening factors
- **Smooth transitions**: Use `hull()` to blend between two shapes
- **Wavy forms**: Add `sin()/cos()` perturbation to parametric paths

### Structural/Grid Shapes
- **Bar/rod**: `hull() { translate(p1) sphere(r); translate(p2) sphere(r); }`
- **Rounded cube**: `minkowski() { cube(size - 2*r, center=true); sphere(r); }`
- **Torus/ring**: `rotate_extrude() translate([R,0,0]) circle(r);`

### Key Functions
- `smoothstep(a,b,t)` — Smooth interpolation for transitions
- `$fn` — Controls curve smoothness (48 for preview, 96+ for final export)

### Common Pitfalls
- `hull()` of many spheres is expensive — keep step count reasonable (200-400)
- `minkowski()` is slow — avoid in loops, use for single accents only
- Always wrap overlapping geometry in `union()` to avoid self-intersection in STL
- Flat shapes (scale Z near 0) can cause degenerate faces — keep minimum 0.2

## Full Pipeline

```
/openscad → /preview-scad → /export-stl (with validation)
    ↑______________|
    (iterate until correct)
```

## SVG-Based Workflow (Recommended for Complex Shapes)

For complex organic curves, blobs, ribbons, and detailed 2D outlines, generate SVG paths with Python instead of building shapes purely in OpenSCAD. This approach is **100-1000x faster** (sub-second vs 2+ minutes) and produces more precise geometry.

### When to Use SVG vs Pure OpenSCAD

| Use SVG + linear_extrude | Use pure OpenSCAD |
|--------------------------|-------------------|
| Organic curves, ribbons, S-shapes | Simple boxes, cylinders, spheres |
| Complex outlines, blobs, puddles | Boolean operations (difference, union) |
| Detailed grids with many bars | Parametric mechanical parts |
| Bezier curves, smooth paths | Rotate_extrude shapes (torus, etc.) |
| Text or logo silhouettes | Screw threads, gears |

### The Pipeline

```
Python generates SVG  -->  OpenSCAD imports SVG  -->  linear_extrude to 3D  -->  render/export
  (sub-second)              import("file.svg")       height = thickness         .png / .stl
```

### Python SVG Generation Pattern

Use filled shapes only -- OpenSCAD 2021 only imports filled SVG elements (not strokes). Convert all strokes to filled rectangles or paths.

```python
import math

def svg_header(width, height):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}mm" height="{height}mm"
     viewBox="0 0 {width} {height}">
'''

def svg_footer():
    return '</svg>\n'

# Bars as filled rectangles (NOT strokes)
def hbar(x1, y, x2, w=1.3):
    r = w / 2
    return f'  <rect x="{min(x1,x2):.3f}" y="{y-r:.3f}" width="{abs(x2-x1):.3f}" height="{w:.3f}" rx="{r:.3f}" fill="black"/>\n'

def vbar(x, y1, y2, w=1.3):
    r = w / 2
    return f'  <rect x="{x-r:.3f}" y="{min(y1,y2):.3f}" width="{w:.3f}" height="{abs(y2-y1):.3f}" rx="{r:.3f}" fill="black"/>\n'

# Organic shapes as bezier paths
def blob(cx, cy, r):
    d = (f"M {cx},{cy-r} "
         f"C {cx+r*1.2},{cy-r} {cx+r*1.2},{cy+r} {cx},{cy+r} "
         f"C {cx-r*1.2},{cy+r} {cx-r*1.2},{cy-r} {cx},{cy-r} Z")
    return f'  <path d="{d}" fill="black"/>\n'

# Ring (donut) using even-odd fill rule
def ring(cx, cy, outer_r, tube_r):
    inner_r = outer_r - tube_r
    outer_r2 = outer_r + tube_r
    d = (f"M {cx-outer_r2:.3f},{cy:.3f} "
         f"A {outer_r2:.3f},{outer_r2:.3f} 0 1,0 {cx+outer_r2:.3f},{cy:.3f} "
         f"A {outer_r2:.3f},{outer_r2:.3f} 0 1,0 {cx-outer_r2:.3f},{cy:.3f} Z "
         f"M {cx-inner_r:.3f},{cy:.3f} "
         f"A {inner_r:.3f},{inner_r:.3f} 0 1,1 {cx+inner_r:.3f},{cy:.3f} "
         f"A {inner_r:.3f},{inner_r:.3f} 0 1,1 {cx-inner_r:.3f},{cy:.3f} Z")
    return f'  <path d="{d}" fill="black" fill-rule="evenodd"/>\n'
```

A full template script is available at `.claude/skills/openscad/scripts/generate-svg-template.py`.

### OpenSCAD Import Pattern

```openscad
// Import SVG and extrude to 3D
// rotate([90,0,0]) flips the SVG from XY-plane to XZ-plane (standing up)
rotate([90, 0, 0])
    linear_extrude(height = 1.5)
        import("layer_grid.svg");

// Different layers can have different thicknesses for 3D depth effect
rotate([90, 0, 0])
    linear_extrude(height = 2.5)
        import("layer_ribbon.svg");

rotate([90, 0, 0])
    linear_extrude(height = 3.0)
        import("layer_blob.svg");
```

### Multi-Layer SVG Strategy

For 3D depth, split the design into separate SVG files per layer:

1. **Background layer** (thin, e.g. 1.5mm): Grid bars, structural elements
2. **Mid layer** (medium, e.g. 2.5mm): Ribbons, flowing shapes
3. **Foreground layer** (thick, e.g. 3.0mm): Accent blobs, cubes, focal elements

Each layer is a separate SVG, imported and extruded at different heights, then combined with `union()`.

### Key Gotchas

- **Filled shapes only**: OpenSCAD 2021 ignores `stroke` -- use `fill="black"` on all elements
- **Coordinate system**: SVG Y-axis points down; use `rotate([90,0,0])` in OpenSCAD to stand the shape up
- **Units**: Set SVG `width`/`height` in mm and matching `viewBox` for correct scale
- **Even-odd fill rule**: Use `fill-rule="evenodd"` for donut/ring shapes (hole inside a shape)
- **Performance**: A complex SVG with 300+ path points imports in under 1 second vs 2+ minutes for equivalent hull/sphere chains

## Tips

- Start simple and add complexity in iterations
- Use meaningful model names that describe the object
- Keep each version's changes focused on specific improvements
- Document what changed between versions in your response to the user
- Only export to STL once the preview looks correct
- For reference matching: iterate at least 5-8 times, comparing each render carefully
- For complex organic shapes, prefer the SVG-based workflow over pure OpenSCAD hull/sphere chains
