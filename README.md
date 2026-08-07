# blender-extrude-edge-to-triangle
A tool for classic game developers to be able to generate triangles instead of quads for extruding.
It's a tool I specifically made because I'm trying to model n64 models and the older Blender version I need to use for fast64 and tiny3d doesn't offer anything like that.

# N64 Triangle Extrude Tools

Two pure-triangle extrude tools designed for N64-style low-poly modeling in Blender.

## Tools

### 1. Extrude Edge to Triangle
Creates a triangle from each selected edge by placing a new vertex at the midpoint.

**Default hotkey:** Front thumb button (BUTTON5MOUSE)

### 2. Extrude Edge Loop to Triangles
Extrudes a closed edge loop into a pure-triangle polygonal ring.  
Creates mid-point vertices, side triangles, and perimeter triangles that connect back to the original edge vertices.

**Default hotkey:** Shift + Front thumb button

> You can rebind either tool to any key or mouse button you prefer in  
> **Edit → Preferences → Keymap** (search for “Extrude Edge”).

## Installation

1. Download the latest release zip **or** clone this repository.
2. In Blender go to `Edit → Preferences → Add-ons → Install...`
3. Select the zip (or the folder containing `__init__.py` + `blender_manifest.toml`).
4. Enable **N64 Triangle Extrude Tools**.

## Usage

1. Enter **Edit Mode**.
2. Select edges (or a clean closed edge loop).
3. Use the hotkeys above (or your own custom bindings).

## Notes

- Designed for pure-triangle workflows (no quads).
- Works best with clean closed loops for the second tool.
- Compatible with Blender 3.0+ and the Blender 4.2+ Extensions system.

## Author

SirAster
