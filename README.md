# blender-extrude-edge-to-triangle
A tool for classic game developers to be able to generate triangles instead of quads for extruding.
It's a tool I specifically made because I'm trying to model n64 models and the older Blender version I need to use for fast64 and tiny3d doesn't offer anything like that.

# N64 Triangle Extrude Tools

Pure-triangle tools designed for N64-style low-poly modeling in Blender.

## Tools

### 1. Extrude Edge to Triangle
Creates a triangle from each selected edge by placing a new vertex at the midpoint.

### 2. Split Triangle by Longest Edge
Splits selected triangles in half along their longest edge, producing two clean triangles.

### 3. Extrude Edge Loop to Triangles
Extrudes a closed edge loop into a pure-triangle polygonal ring.  
Creates mid-point vertices, side triangles, and perimeter triangles that connect back to the original edge vertices.

## Hotkeys

| Input | Action |
|-------|--------|
| **Front thumb button** | **Context-sensitive**<br>• Edges selected → Extrude Edge to Triangle<br>• Faces selected → Split Triangle by Longest Edge |
| **Shift + Front thumb button** | Extrude Edge Loop to Triangles |

> You can rebind these tools to any key or mouse button in  
> **Edit → Preferences → Keymap**.

## Installation

1. Download the latest release zip **or** clone this repository.
2. In Blender go to `Edit → Preferences → Add-ons → Install...`
3. Select the zip (or the folder containing `__init__.py` + `blender_manifest.toml`).
4. Enable **N64 Triangle Extrude Tools**.

## Usage

1. Enter **Edit Mode**.
2. Select edges, triangular faces, or a clean closed edge loop.
3. Use the hotkeys above.

## Notes

- Designed for pure-triangle workflows (no quads).
- The face-splitting tool works on multiple triangles at once.
- Compatible with Blender 3.0+ and the Blender 4.2+ Extensions system.

## Author

SirAster
