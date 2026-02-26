"""
Cage Pendant — Blender v6 — Based on v3 (closest match) with specific fixes:
- Grid changed to 4x7
- Drip THICKER (bevel_depth 0.5 -> 1.2)
- Blob MUCH TALLER (vertical mound, not flat puddle)
- Spiral starts at TOP CENTER (phase_offset = pi)
- Spiral ends at BOTTOM RIGHT IN FRONT of grid (~1.875 turns)
"""

import bpy
import math
import random
from mathutils import Vector

# ── Parameters ──────────────────────────────────────────────
WIDTH = 25
HEIGHT = 40
COLS = 4
ROWS = 7
BAR_RADIUS = 0.55
CORNER_RADIUS = 3.0  # rounded corner radius for frame

RIBBON_TURNS = 1.875  # ends at bottom-right-front with phase_offset=pi
LOOP_MAJOR_R = 2.2
LOOP_MINOR_R = 0.6

CUBE_SIZE = 4.0

dx = WIDTH / (COLS - 1)
dz = HEIGHT / (ROWS - 1)


def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.curves:
        if block.users == 0:
            bpy.data.curves.remove(block)
    for block in bpy.data.metaballs:
        if block.users == 0:
            bpy.data.metaballs.remove(block)


def create_bar(p1, p2, radius=BAR_RADIUS, name="bar"):
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 8
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    curve_data.use_fill_caps = True
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (*p1, 1)
    spline.points[1].co = (*p2, 1)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_curve_bar(points_list, radius=BAR_RADIUS, name="curve_bar"):
    """Create a bar along multiple points (for rounded corners)."""
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    curve_data.use_fill_caps = True
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points_list) - 1)
    for i, p in enumerate(points_list):
        spline.points[i].co = (*p, 1)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_grid():
    """Grid with ROUNDED CORNER frame — 4x7 grid."""
    parts = []
    r = CORNER_RADIUS

    # ── Outer frame with rounded corners ──
    n_corner = 8
    frame_pts = []
    # Bottom-left corner (0, 0)
    for i in range(n_corner + 1):
        a = math.pi + (math.pi / 2) * i / n_corner
        frame_pts.append((r + r * math.cos(a), 0, r + r * math.sin(a)))
    # Bottom-right corner (WIDTH, 0)
    for i in range(n_corner + 1):
        a = (3 * math.pi / 2) + (math.pi / 2) * i / n_corner
        frame_pts.append((WIDTH - r + r * math.cos(a), 0, r + r * math.sin(a)))
    # Top-right corner (WIDTH, HEIGHT)
    for i in range(n_corner + 1):
        a = 0 + (math.pi / 2) * i / n_corner
        frame_pts.append((WIDTH - r + r * math.cos(a), 0, HEIGHT - r + r * math.sin(a)))
    # Top-left corner (0, HEIGHT)
    for i in range(n_corner + 1):
        a = (math.pi / 2) + (math.pi / 2) * i / n_corner
        frame_pts.append((r + r * math.cos(a), 0, HEIGHT - r + r * math.sin(a)))
    frame_pts.append(frame_pts[0])

    parts.append(create_curve_bar(frame_pts, radius=BAR_RADIUS * 1.1, name="frame"))

    # ── Internal vertical bars (skip first and last column — they're part of frame) ──
    for i in range(1, COLS - 1):
        x = i * dx
        parts.append(create_bar((x, 0, 0), (x, 0, HEIGHT), name=f"vbar_{i}"))

    # ── Internal horizontal bars (skip first and last row — they're part of frame) ──
    for j in range(1, ROWS - 1):
        z = j * dz
        parts.append(create_bar((0, 0, z), (WIDTH, 0, z), name=f"hbar_{j}"))

    # Intersection spheres at all grid points
    for i in range(COLS):
        for j in range(ROWS):
            x = i * dx
            z = j * dz
            if (i == 0 or i == COLS - 1) and (j == 0 or j == ROWS - 1):
                continue
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=BAR_RADIUS * 1.1, segments=10, ring_count=6,
                location=(x, 0, z))
            bpy.context.active_object.name = f"joint_{i}_{j}"
            parts.append(bpy.context.active_object)

    return parts


def create_hanging_loop():
    """VERTICAL ring at top for hanging."""
    center_x = WIDTH / 2
    loop_z = HEIGHT + LOOP_MAJOR_R + 2.0

    bpy.ops.mesh.primitive_torus_add(
        align='WORLD',
        location=(center_x, 0, loop_z),
        rotation=(math.radians(90), 0, 0),
        major_radius=LOOP_MAJOR_R,
        minor_radius=LOOP_MINOR_R,
        major_segments=32,
        minor_segments=12,
    )
    torus = bpy.context.active_object
    torus.name = "hanging_loop"

    post = create_bar(
        (center_x, 0, HEIGHT),
        (center_x, 0, loop_z - LOOP_MAJOR_R),
        radius=0.6,
        name="loop_post"
    )
    return [torus, post]


def create_ribbon():
    """Bold helical ribbon:
    - Starts at TOP CENTER (phase_offset = pi → sin(pi)=0 center, cos(pi)=-1 toward viewer)
    - ~1.875 turns so it ends at BOTTOM RIGHT IN FRONT of grid
      (final angle mod 2pi ≈ 3pi/4 → sin=+0.7 right, cos=-0.7 front)
    """
    cx = WIDTH / 2
    cy = 0
    amp_x = WIDTH / 2 + 2.5
    amp_y = 5.5

    def smoothstep(edge0, edge1, x):
        t = max(0, min(1, (x - edge0) / (edge1 - edge0)))
        return t * t * (3 - 2 * t)

    steps = 500
    points = []

    # Start at top center, toward viewer
    phase_offset = math.pi

    for i in range(steps + 1):
        t = i / steps
        z_base = HEIGHT * 0.95 * (1 - t) + HEIGHT * 0.025
        angle = t * RIBBON_TURNS * 2 * math.pi + phase_offset

        # Bottom organic section
        wave_blend = smoothstep(0.75, 0.92, t)
        wave_t = max(0, (t - 0.75) / 0.25)

        wave_x = wave_blend * (
            math.sin(wave_t * 2.0 * math.pi) * 2.0
            + math.sin(wave_t * 0.7 * math.pi) * 1.2
        )
        wave_z = wave_blend * math.sin(wave_t * 1.5 * math.pi) * 1.5

        amp_fade = 1.0 - wave_blend * 0.4
        droop = smoothstep(0.88, 1.0, t) * 4.0
        taper = 1.0 - smoothstep(0.88, 1.0, t) * 0.25

        x = cx + amp_x * amp_fade * math.sin(angle) + wave_x
        y = cy + amp_y * amp_fade * math.cos(angle)
        z_final = z_base + wave_z - droop

        points.append((Vector((x, y, z_final)), taper))

    # Build mesh tube — round cross-section
    n_ring = 20
    rw = 1.40  # ~2.8mm wide
    rt = 1.40  # ROUND tube (was 0.50 flat band in v3)

    verts = []
    faces = []
    prev_normal = None

    for i, (center, taper) in enumerate(points):
        if i < len(points) - 1:
            tangent = points[i + 1][0] - center
        else:
            tangent = center - points[i - 1][0]
        if tangent.length < 1e-8:
            tangent = Vector((0, 0, -1))
        tangent.normalize()

        if prev_normal is None:
            up = Vector((0, 0, 1)) if abs(tangent.z) < 0.99 else Vector((1, 0, 0))
            normal = tangent.cross(up).normalized()
        else:
            normal = prev_normal - tangent * prev_normal.dot(tangent)
            if normal.length < 1e-6:
                up = Vector((0, 0, 1)) if abs(tangent.z) < 0.99 else Vector((1, 0, 0))
                normal = tangent.cross(up).normalized()
            else:
                normal.normalize()

        binormal = tangent.cross(normal).normalized()
        prev_normal = normal.copy()

        for k in range(n_ring):
            a = 2 * math.pi * k / n_ring
            offset = normal * (rt * taper * math.cos(a)) + binormal * (rw * taper * math.sin(a))
            verts.append(center + offset)

    total_rings = len(points)
    for i in range(total_rings - 1):
        for k in range(n_ring):
            k_next = (k + 1) % n_ring
            v0 = i * n_ring + k
            v1 = i * n_ring + k_next
            v2 = (i + 1) * n_ring + k_next
            v3 = (i + 1) * n_ring + k
            faces.append((v0, v1, v2, v3))

    # Caps
    ci = len(verts)
    verts.append(points[0][0])
    for k in range(n_ring):
        faces.append((ci, (k + 1) % n_ring, k))
    ci = len(verts)
    verts.append(points[-1][0])
    lr = (total_rings - 1) * n_ring
    for k in range(n_ring):
        faces.append((ci, lr + k, lr + (k + 1) % n_ring))

    mesh = bpy.data.meshes.new("ribbon_mesh")
    mesh.from_pydata([(v.x, v.y, v.z) for v in verts], [], faces)
    mesh.update()

    ribbon_obj = bpy.data.objects.new("ribbon", mesh)
    bpy.context.collection.objects.link(ribbon_obj)
    for poly in ribbon_obj.data.polygons:
        poly.use_smooth = True

    subsurf = ribbon_obj.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 1
    subsurf.render_levels = 2

    return [ribbon_obj]


def create_accent_cube():
    """Square block on the grid, upper-right area.
    Has a sinusoidal drip stream going DOWN from its center to the blob."""
    px = WIDTH * 0.70
    pz = HEIGHT - dz * 1.5

    # Cube on the grid plane
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(px, 0, pz),
        scale=(CUBE_SIZE, CUBE_SIZE * 0.5, CUBE_SIZE)
    )
    cube = bpy.context.active_object
    cube.name = "accent_cube"

    bevel = cube.modifiers.new(name="Bevel", type='BEVEL')
    bevel.width = 0.4
    bevel.segments = 3
    subsurf = cube.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 1

    return [cube]


def create_sinusoidal_drip():
    """THICK sinusoidal drip stream flowing from cube center down to blob.
    Bevel increased from 0.5 to 1.2 for much thicker drip.
    Starts DIRECTLY at the cube bottom (no gap)."""
    cube_x = WIDTH * 0.70
    # Start right at cube bottom
    cube_bottom_z = HEIGHT - dz * 1.5 - CUBE_SIZE / 2

    # End at the tall blob top
    blob_top_z = -2.0

    n_pts = 120
    drip_pts = []
    for i in range(n_pts + 1):
        t = i / n_pts
        z = cube_bottom_z - t * (cube_bottom_z - blob_top_z)
        # Sinusoidal wave in X — gradual onset, gets more wavy toward bottom
        onset = min(1.0, t * 3.0)  # ramp up over first third
        amplitude = onset * (1.5 + t * 2.5)
        freq = 3.0
        x = cube_x + amplitude * math.sin(t * freq * 2 * math.pi)
        drip_pts.append((x, 0, z))

    # Create as a curve with bevel — THICK
    curve_data = bpy.data.curves.new(name="sinusoidal_drip", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12
    curve_data.bevel_depth = 1.2  # MUCH thicker (was 0.5 in v3)
    curve_data.bevel_resolution = 4
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new('POLY')
    spline.points.add(len(drip_pts) - 1)
    for i, p in enumerate(drip_pts):
        spline.points[i].co = (*p, 1)
        # Taper: slightly thinner at top, thicker at bottom
        spline.points[i].radius = 0.6 + 0.4 * (i / n_pts)

    obj = bpy.data.objects.new("sinusoidal_drip", curve_data)
    bpy.context.collection.objects.link(obj)
    return [obj]


def create_drip_blob():
    """TALL organic blob — much taller than v3's flat puddle.
    Vertical mound shape like liquid pooling and rising, not a flat disc."""
    mball = bpy.data.metaballs.new("drip_mball")
    mball.resolution = 0.3
    mball.render_resolution = 0.15
    mball.threshold = 0.5

    # Center under the drip area
    cx = WIDTH * 0.55
    base_z = -3.0

    # ── TALL central column — the main vertical mass ──
    # Stack multiple balls vertically for tall blob shape
    for i in range(8):
        elem = mball.elements.new()
        z_offset = i * 1.8  # spread up from base
        elem.co = (cx, 0, base_z + z_offset)
        # Larger at base, slightly smaller at top
        r = 3.5 - i * 0.25
        elem.radius = max(r, 1.5)
        elem.type = 'ELLIPSOID'
        elem.size_x = 1.2
        elem.size_y = 0.8
        elem.size_z = 1.0

    # ── Wide base / roots — organic spread at the bottom ──
    for angle_i in range(5):
        a = (angle_i / 5) * 2 * math.pi + 0.3
        spread = 2.5 + random.Random(42 + angle_i).uniform(0, 1.5)
        elem = mball.elements.new()
        elem.co = (cx + spread * math.cos(a), spread * math.sin(a) * 0.6, base_z - 0.5)
        elem.radius = 2.0 + random.Random(100 + angle_i).uniform(0, 1.0)
        elem.type = 'ELLIPSOID'
        elem.size_x = 1.5
        elem.size_y = 1.0
        elem.size_z = 0.5

    # ── Connecting mass between drip endpoint and blob top ──
    for i in range(3):
        elem = mball.elements.new()
        elem.co = (cx + 0.5, 0, base_z + 12 + i * 2.0)
        elem.radius = 2.0 - i * 0.3
        elem.type = 'BALL'

    # ── Small organic bumps for texture ──
    rng = random.Random(42)
    for _ in range(6):
        elem = mball.elements.new()
        elem.co = (cx + rng.uniform(-3, 3), rng.uniform(-1.5, 1.5), base_z + rng.uniform(0, 10))
        elem.radius = rng.uniform(0.8, 1.5)
        elem.type = 'BALL'

    mball_obj = bpy.data.objects.new("drip_blob", mball)
    bpy.context.collection.objects.link(mball_obj)
    return [mball_obj]


def convert_all_to_mesh():
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.convert(target='MESH')


def join_all():
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def export_stl(filepath):
    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=False,
        ascii_format=False,
    )


if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))

    clear_scene()

    print("Creating grid (4x7, rounded corners)...")
    create_grid()

    print("Creating hanging loop (vertical)...")
    create_hanging_loop()

    print("Creating ribbon (starts top center, ends bottom-right-front)...")
    create_ribbon()

    print("Creating accent cube...")
    create_accent_cube()

    print("Creating sinusoidal drip (THICK)...")
    create_sinusoidal_drip()

    print("Creating drip blob (TALL mound)...")
    create_drip_blob()

    print("Converting to mesh...")
    convert_all_to_mesh()

    print("Joining...")
    pendant = join_all()
    pendant.name = "cage_pendant"

    stl_path = os.path.join(base_dir, "cage_pendant_blender_v6.stl")
    print(f"Exporting STL: {stl_path}")
    export_stl(stl_path)

    print("Done!")
