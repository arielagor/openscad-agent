# OpenSCAD Agent — Foundational Architecture Decisions

**Date**: 2026-02-02
**Session type**: Retroactive documentation
**Scope**: Initial project setup and architecture

---

## Context

This entry was created retroactively to document the foundational decisions
made when this project was first built. Reconstructed from codebase analysis
and git history. This is a Claude Code agent environment that enables
AI-assisted 3D modeling and printing through natural language interaction.

## Decisions Made

### 1. Claude Code Skills as the Framework

- **Choice**: Claude Code custom skills (/openscad, /preview-scad, /export-stl)
- **Over**: Standalone CLI tool, web-based interface, VS Code extension, Python framework
- **Because**: Claude Code provides the AI reasoning layer — the agent can interpret natural language design descriptions, generate parametric code, visually evaluate renders, and iterate. Skills make the workflows invocable and composable.
- **Consequence**: Tied to Claude Code's skill system. Users must have Claude Code installed. But gains the full power of an LLM that can see rendered images and reason about 3D geometry.

### 2. OpenSCAD as Primary 3D Engine

- **Choice**: OpenSCAD for parametric 3D modeling
- **Over**: FreeCAD, Blender-only, custom 3D engine, Three.js
- **Because**: OpenSCAD is code-based (not GUI-based), making it ideal for AI generation. The agent writes .scad files as text — no mouse interaction needed. Parametric by nature, so designs are adjustable. CLI rendering enables automated preview/export pipelines.
- **Consequence**: Limited to constructive solid geometry (CSG). Organic shapes are difficult. This limitation drove the addition of Blender and SVG workflows.

### 3. Triple Workflow Architecture (OpenSCAD + SVG + Blender)

- **Choice**: Three distinct design workflows for different shape categories
- **Over**: Single-tool approach, OpenSCAD-only
- **Because**: Each tool excels at different shape types. OpenSCAD handles mechanical/geometric parts. SVG-to-3D (via Python) handles flat 2D-to-3D extrusions 100-1000x faster. Blender Python handles complex organic/sculptural shapes that CSG can't represent.
- **Consequence**: Three toolchains to maintain. The agent must select the right workflow per design. But covers the full spectrum of 3D printable shapes.

### 4. Versioned File Naming Convention

- **Choice**: `model_version.scad` → `model_version.png` → `model_version.stl`
- **Over**: Git-only versioning, overwriting files, timestamp-based naming
- **Because**: Design iteration is visual — you need to compare renders side by side. Versioned filenames keep all iterations visible in the filesystem. The agent can reference previous versions when refining.
- **Consequence**: Directory grows with iterations. But the design history is immediately browsable without git log.

### 5. Bash-Based Skill Scripts (No Package Manager)

- **Choice**: Pure Bash scripts for skills, no npm/pip dependencies
- **Over**: Node.js CLI, Python package, compiled binary
- **Because**: OpenSCAD and Blender are invoked as shell commands. Bash is the natural glue layer. No dependency installation needed beyond the 3D tools themselves.
- **Consequence**: Cross-platform Bash compatibility required (Windows Git Bash, macOS, Linux). No package ecosystem benefits.

### 6. Cross-Platform Support

- **Choice**: Explicit Windows/macOS/Linux support with platform detection
- **Over**: Single-platform (Linux-only or macOS-only)
- **Because**: 3D printing enthusiasts use all platforms. Blender and OpenSCAD paths differ per OS. Platform detection ensures the agent works everywhere.
- **Consequence**: Path detection logic for each platform. Testing needed on all three.

### 7. Geometry Validation on STL Export

- **Choice**: Non-manifold detection, self-intersection checks, degenerate face warnings
- **Over**: Export without validation, rely on slicer warnings
- **Because**: Invalid geometry wastes print time and filament. Catching issues before export saves the user from failed prints.
- **Consequence**: Validation adds export time but prevents downstream failures.

## What Was Built

- Three Claude Code skills: /openscad (create + iterate), /preview-scad (render), /export-stl (validate + export)
- OpenSCAD workflow: parametric code generation with visual feedback loop
- SVG workflow: Python-based 2D-to-3D conversion for flat shapes
- Blender workflow: Python headless scripting for organic/sculptural shapes
- Geometry validation pipeline (non-manifold, self-intersection, degenerate face)
- Cross-platform support (Windows, macOS, Linux)
- Cage pendant design iterations (active project demonstrating the workflow)

## Open Questions

- No automated testing framework — skill correctness relies on manual verification
- Blender workflow documentation exists but may need more examples

## Next Session Context

> This repo now has decision documentation. Future sessions should create
> a new entry in docs/decisions/ for every session that involves substantive
> code changes. Log decisions AS they happen, not at session end.
