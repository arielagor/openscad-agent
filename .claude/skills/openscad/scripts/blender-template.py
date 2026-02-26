"""
Blender Python Template for 3D Model Generation
=================================================
Reusable functions for creating 3D geometry with Blender's headless Python API.
Covers the most common patterns: bars, tubes, metaballs, torus, rounded cubes.

Run headless:
    blender --background --python blender-template.py

This script produces an STL file. For preview rendering, import the STL into
OpenSCAD and use the standard render-scad.sh pipeline.
"""

import bpy
import math
from mathutils import Vector


# ── Scene Management ─────────────────────────────────────────

def clear_scene():
    """Remove all default objects and orphan data from the scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Clean up orphan data blocks
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.curves:
        if block.users == 0:
            bpy.data.curves.remove(block)
    for block in bpy.data.metaballs:
        if block.users == 0:
            bpy.data.metaballs.remove(block)


# ── Primitive Builders ───────────────────────────────────────

def create_bar(p1, p2, radius=0.65, name="bar"):
    """Create a cylindrical bar between two 3D points using a curve with bevel.

    This is the Blender equivalent of OpenSCAD's:
        hull() { translate(p1) sphere(r); translate(p2) sphere(r); }
    but renders instantly and produces cleaner geometry.

    Args:
        p1: Start point as (x, y, z) tuple.
        p2: End point as (x, y, z) tuple.
        radius: Cross-section radius of the bar.
        name: Object name in the Blender scene.

    Returns:
        The created Blender curve object.
    """
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 8
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 4
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new('POLY')
    spline.points.add(1)  # Already has 1 point by default, add 1 more
    spline.points[0].co = (*p1, 1)  # 4th value is the spline weight
    spline.points[1].co = (*p2, 1)

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    return obj


def create_tube_along_path(points, radius=1.0, n_ring=12, name="tube"):
    """Sweep a circular cross-section along a list of 3D points to create a tube.

    This is the Blender equivalent of chaining hull(sphere(), sphere()) along
    a path in OpenSCAD, but produces true tubular geometry with proper
    cross-sections oriented perpendicular to the path tangent.

    Uses a Frenet frame to orient each cross-section ring.

    Args:
        points: List of (x, y, z) tuples defining the path centerline.
        radius: Radius of the circular cross-section.
        n_ring: Number of vertices per cross-section ring (more = smoother).
        name: Object name in the Blender scene.

    Returns:
        The created Blender mesh object.
    """
    verts = []
    faces = []

    for i, center in enumerate(points):
        center = Vector(center)

        # Compute tangent from adjacent points
        if i < len(points) - 1:
            tangent = Vector(points[i + 1]) - center
        else:
            tangent = center - Vector(points[i - 1])
        tangent.normalize()

        # Build Frenet frame (normal + binormal)
        up = Vector((0, 0, 1)) if abs(tangent.z) < 0.99 else Vector((1, 0, 0))
        normal = tangent.cross(up).normalized()
        binormal = tangent.cross(normal).normalized()

        # Create ring of vertices as circular cross-section
        for k in range(n_ring):
            angle = 2 * math.pi * k / n_ring
            offset = normal * (radius * math.cos(angle)) + binormal * (radius * math.sin(angle))
            verts.append(center + offset)

    # Create quad faces connecting adjacent rings
    for i in range(len(points) - 1):
        for k in range(n_ring):
            k_next = (k + 1) % n_ring
            v0 = i * n_ring + k
            v1 = i * n_ring + k_next
            v2 = (i + 1) * n_ring + k_next
            v3 = (i + 1) * n_ring + k
            faces.append((v0, v1, v2, v3))

    # Cap the start end
    cap_start_idx = len(verts)
    verts.append(Vector(points[0]))
    for k in range(n_ring):
        k_next = (k + 1) % n_ring
        faces.append((cap_start_idx, k_next, k))

    # Cap the end
    cap_end_idx = len(verts)
    verts.append(Vector(points[-1]))
    last_ring = (len(points) - 1) * n_ring
    for k in range(n_ring):
        k_next = (k + 1) % n_ring
        faces.append((cap_end_idx, last_ring + k, last_ring + k_next))

    # Create the Blender mesh
    mesh = bpy.data.meshes.new(f"{name}_mesh")
    mesh.from_pydata([(v.x, v.y, v.z) for v in verts], [], faces)
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)

    # Enable smooth shading for better appearance
    for poly in obj.data.polygons:
        poly.use_smooth = True

    return obj


def create_metaball_blob(elements, resolution=0.3, threshold=0.6, name="blob"):
    """Create an organic blobby shape from metaball elements.

    Metaballs automatically merge into smooth organic forms when they overlap,
    making them perfect for drips, puddles, melting effects, and organic blobs.
    There is no equivalent in OpenSCAD.

    Args:
        elements: List of dicts, each with:
            - 'pos': (x, y, z) center position
            - 'radius': float, influence radius
            - 'type': 'BALL' or 'ELLIPSOID' (default: 'BALL')
            - 'size': (sx, sy, sz) for ELLIPSOID type (optional)
        resolution: Mesh resolution (lower = finer). 0.3 for preview, 0.15 for export.
        threshold: Merge threshold (higher = tighter blobs, lower = more merging).
        name: Object name in the Blender scene.

    Returns:
        The created Blender metaball object.
    """
    mball = bpy.data.metaballs.new(name)
    mball.resolution = resolution
    mball.render_resolution = resolution / 2
    mball.threshold = threshold

    for spec in elements:
        elem = mball.elements.new()
        elem.co = spec['pos']
        elem.radius = spec['radius']
        elem.type = spec.get('type', 'BALL')
        if elem.type == 'ELLIPSOID' and 'size' in spec:
            elem.size_x, elem.size_y, elem.size_z = spec['size']

    obj = bpy.data.objects.new(name, mball)
    bpy.context.collection.objects.link(obj)
    return obj


def create_torus(location, major_radius=2.5, minor_radius=0.7, name="torus"):
    """Create a torus (ring/loop) at the given location.

    Args:
        location: (x, y, z) center position.
        major_radius: Distance from center of torus to center of tube.
        minor_radius: Radius of the tube itself.
        name: Object name in the Blender scene.

    Returns:
        The created Blender mesh object.
    """
    bpy.ops.mesh.primitive_torus_add(
        align='WORLD',
        location=location,
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=32,
        minor_segments=12,
    )
    torus = bpy.context.active_object
    torus.name = name
    return torus


def create_rounded_cube(location, size=(4, 4, 4), subdivisions=2, name="rounded_cube"):
    """Create a rounded cube using subdivision surface modifier.

    This is the Blender equivalent of OpenSCAD's:
        minkowski() { cube(size, center=true); sphere(r); }
    but is dramatically faster (instant vs potentially minutes).

    Args:
        location: (x, y, z) center position.
        size: (width, depth, height) dimensions.
        subdivisions: Subdivision levels (1-3). Higher = rounder.
        name: Object name in the Blender scene.

    Returns:
        The created Blender mesh object.
    """
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=location,
        scale=size,
    )
    cube = bpy.context.active_object
    cube.name = name

    subsurf = cube.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = subdivisions
    subsurf.render_levels = subdivisions

    return cube


# ── Assembly & Export ────────────────────────────────────────

def convert_and_join():
    """Convert all curves and metaballs to meshes, then join into one object.

    Must be called before STL export since STL only supports mesh data.
    After this call, the scene contains a single mesh object.

    Returns:
        The single joined Blender mesh object.
    """
    bpy.ops.object.select_all(action='SELECT')
    bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]

    # Convert curves and metaballs to mesh geometry
    bpy.ops.object.convert(target='MESH')

    # Join all mesh objects into one
    bpy.ops.object.join()

    return bpy.context.active_object


def export_stl(filepath):
    """Export the scene as a binary STL file.

    Args:
        filepath: Absolute path for the output .stl file.
    """
    bpy.ops.wm.stl_export(
        filepath=filepath,
        export_selected_objects=False,
        ascii_format=False,
    )
    print(f"Exported STL: {filepath}")


# ── Example Usage ────────────────────────────────────────────

if __name__ == "__main__":
    import os

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Start with a clean scene
    clear_scene()

    # --- Example: Cylindrical bars forming a simple frame ---
    print("Creating bars...")
    # Four vertical posts
    for x, y in [(-5, -5), (5, -5), (5, 5), (-5, 5)]:
        create_bar((x, y, 0), (x, y, 20), radius=0.5, name=f"post_{x}_{y}")

    # Horizontal bars connecting the posts at top and bottom
    corners = [(-5, -5), (5, -5), (5, 5), (-5, 5)]
    for i in range(4):
        x1, y1 = corners[i]
        x2, y2 = corners[(i + 1) % 4]
        create_bar((x1, y1, 0), (x2, y2, 0), radius=0.5, name=f"bottom_{i}")
        create_bar((x1, y1, 20), (x2, y2, 20), radius=0.5, name=f"top_{i}")

    # --- Example: Helical tube ---
    print("Creating helix tube...")
    helix_points = []
    for i in range(200):
        t = i / 199
        angle = t * 4 * math.pi  # 2 full turns
        x = 3 * math.cos(angle)
        y = 3 * math.sin(angle)
        z = t * 20
        helix_points.append((x, y, z))
    create_tube_along_path(helix_points, radius=0.4, n_ring=8, name="helix")

    # --- Example: Metaball blob at the base ---
    print("Creating metaball blob...")
    create_metaball_blob([
        {'pos': (0, 0, -2), 'radius': 4.0, 'type': 'ELLIPSOID', 'size': (2.0, 2.0, 0.5)},
        {'pos': (2, 1, -1.5), 'radius': 2.5, 'type': 'BALL'},
        {'pos': (-2, -1, -1.5), 'radius': 2.5, 'type': 'BALL'},
    ], resolution=0.3, name="base_blob")

    # --- Example: Torus on top ---
    print("Creating torus...")
    create_torus((0, 0, 22), major_radius=2.0, minor_radius=0.5, name="top_ring")

    # --- Example: Rounded cube accent ---
    print("Creating rounded cube...")
    create_rounded_cube((0, 0, 10), size=(3, 3, 3), subdivisions=2, name="accent")

    # --- Convert and export ---
    print("Converting to mesh and joining...")
    obj = convert_and_join()
    obj.name = "example_model"

    stl_path = os.path.join(base_dir, "blender_template_example.stl")
    export_stl(stl_path)

    print("Done! To preview, import the STL into OpenSCAD:")
    print(f'  import("{stl_path}");')
