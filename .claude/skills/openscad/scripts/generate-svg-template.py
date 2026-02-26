"""
SVG Generation Template for OpenSCAD Import

Generates filled SVG shapes that OpenSCAD can import and linear_extrude into 3D.

Key rules:
  - Use FILLED shapes only (fill="black"), not strokes -- OpenSCAD 2021 ignores strokes
  - Set width/height in mm with matching viewBox for correct scale
  - Use fill-rule="evenodd" for shapes with holes (rings, donuts)
  - Split layers into separate SVG files for different extrusion depths

Usage:
  python generate-svg-template.py
  -> Produces example.svg (importable in OpenSCAD)

OpenSCAD import:
  rotate([90,0,0]) linear_extrude(height=1.5) import("example.svg");
"""

import math
import os


# ── SVG boilerplate ─────────────────────────────────────────

def svg_header(width, height):
    """SVG header with mm units and matching viewBox."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{width}mm" height="{height}mm"
     viewBox="0 0 {width} {height}">
'''


def svg_footer():
    return '</svg>\n'


# ── Primitive shapes (all filled, no strokes) ───────────────

def filled_rect(x, y, w, h, rx=0):
    """Filled rectangle, optionally with rounded corners."""
    rx_attr = f' rx="{rx:.3f}"' if rx > 0 else ''
    return f'  <rect x="{x:.3f}" y="{y:.3f}" width="{w:.3f}" height="{h:.3f}"{rx_attr} fill="black"/>\n'


def filled_circle(cx, cy, r):
    """Filled circle."""
    return f'  <circle cx="{cx:.3f}" cy="{cy:.3f}" r="{r:.3f}" fill="black"/>\n'


def hbar(x1, y, x2, w=1.3):
    """Horizontal bar as a filled rounded rectangle."""
    r = w / 2
    return filled_rect(min(x1, x2), y - r, abs(x2 - x1), w, rx=r)


def vbar(x, y1, y2, w=1.3):
    """Vertical bar as a filled rounded rectangle."""
    r = w / 2
    return filled_rect(x - r, min(y1, y2), w, abs(y2 - y1), rx=r)


def ring(cx, cy, outer_r, tube_r):
    """Filled ring (donut) using even-odd fill rule for the hole."""
    inner_r = outer_r - tube_r
    outer_r2 = outer_r + tube_r
    d = (
        f"M {cx - outer_r2:.3f},{cy:.3f} "
        f"A {outer_r2:.3f},{outer_r2:.3f} 0 1,0 {cx + outer_r2:.3f},{cy:.3f} "
        f"A {outer_r2:.3f},{outer_r2:.3f} 0 1,0 {cx - outer_r2:.3f},{cy:.3f} Z "
        f"M {cx - inner_r:.3f},{cy:.3f} "
        f"A {inner_r:.3f},{inner_r:.3f} 0 1,1 {cx + inner_r:.3f},{cy:.3f} "
        f"A {inner_r:.3f},{inner_r:.3f} 0 1,1 {cx - inner_r:.3f},{cy:.3f} Z"
    )
    return f'  <path d="{d}" fill="black" fill-rule="evenodd"/>\n'


# ── Complex shape helpers ────────────────────────────────────

def bezier_blob(cx, cy, rx, ry):
    """Organic blob shape using cubic bezier curves."""
    d = (
        f"M {cx:.2f},{cy - ry:.2f} "
        f"C {cx + rx * 1.3:.2f},{cy - ry:.2f} "
        f"  {cx + rx * 1.3:.2f},{cy + ry:.2f} "
        f"  {cx:.2f},{cy + ry:.2f} "
        f"C {cx - rx * 1.3:.2f},{cy + ry:.2f} "
        f"  {cx - rx * 1.3:.2f},{cy - ry:.2f} "
        f"  {cx:.2f},{cy - ry:.2f} Z"
    )
    return f'  <path d="{d}" fill="black"/>\n'


def sine_ribbon(ox, oy, width, height, ribbon_w=2.0, periods=1.5, n_points=200):
    """
    Generate a filled ribbon following a sine wave.
    Uses offset curves (left/right of centerline) to create a filled outline.
    """
    left_pts = []
    right_pts = []

    for i in range(n_points + 1):
        t = i / n_points
        y = oy + t * height
        amp = width / 2
        x = ox + width / 2 + amp * math.sin(t * periods * 2 * math.pi)

        # Compute tangent for perpendicular offset
        dt = 0.002
        t2 = min(1.0, t + dt)
        y2 = oy + t2 * height
        x2 = ox + width / 2 + amp * math.sin(t2 * periods * 2 * math.pi)

        tdx = x2 - x
        tdy = y2 - y
        tlen = math.sqrt(tdx * tdx + tdy * tdy) + 1e-6

        # Normal perpendicular to tangent
        nx = -tdy / tlen
        ny = tdx / tlen

        rw = ribbon_w / 2
        left_pts.append((x + nx * rw, y + ny * rw))
        right_pts.append((x - nx * rw, y - ny * rw))

    # Closed path: left side forward, right side backward
    d = f"M {left_pts[0][0]:.2f},{left_pts[0][1]:.2f} "
    for p in left_pts[1:]:
        d += f"L {p[0]:.2f},{p[1]:.2f} "
    for p in reversed(right_pts):
        d += f"L {p[0]:.2f},{p[1]:.2f} "
    d += "Z"

    return f'  <path d="{d}" fill="black"/>\n'


# ── Example: generate a sample SVG ──────────────────────────

def make_example_svg():
    """Generate an example SVG demonstrating all primitive types."""
    W, H = 50, 60
    svg = svg_header(W, H)

    # Grid of bars
    for i in range(5):
        x = 10 + i * 8
        svg += vbar(x, 5, 45, w=1.2)
    for j in range(6):
        y = 5 + j * 8
        svg += hbar(10, y, 42)

    # A ring at the top
    svg += ring(25, 3, 2.5, 0.6)

    # A blob at the bottom
    svg += bezier_blob(25, 52, 8, 5)

    # A small accent circle
    svg += filled_circle(38, 15, 2.5)

    svg += svg_footer()
    return svg


if __name__ == "__main__":
    outdir = os.path.dirname(os.path.abspath(__file__))
    outpath = os.path.join(outdir, "example.svg")

    with open(outpath, "w") as f:
        f.write(make_example_svg())
    print(f"Written: {outpath}")
    print("\nTo use in OpenSCAD:")
    print('  rotate([90,0,0]) linear_extrude(height=1.5) import("example.svg");')
