---
name: openscad
description: Create versioned OpenSCAD (.scad) files for 3D printing, render previews, and compare iterations. Use this when designing or iterating on 3D models.
allowed-tools:
  - Bash(*/render-scad.sh*)
  - Bash(*/version-scad.sh*)
  - Bash(*/export-stl.sh*)
  - Bash(*openscad*)
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

## Tips

- Start simple and add complexity in iterations
- Use meaningful model names that describe the object
- Keep each version's changes focused on specific improvements
- Document what changed between versions in your response to the user
- Only export to STL once the preview looks correct
- For reference matching: iterate at least 5-8 times, comparing each render carefully
