# blender-extrude-edge-to-triangle
A tool for classic game developers to be able to generate triangles instead of quads for extruding.
It's a tool I specifically made because I'm trying to model n64 models and the older Blender version I need to use for fast64 and tiny3d doesn't offer anything like that.

# Extrude Edge to Triangle

It takes one or more selected edges and creates a new triangle for each by placing a vertex at the **midpoint** of the edge. You can then immediately pull the new vertex(s) with `G` in any direction you want.

## Features

- Works on **multiple edges** at once
- Places the new vertex exactly in the middle of each edge
- Automatically selects the new vertices so you can move them right away
- Comes with two hotkeys ready to use

## Installation

### Method 1: As a script (quick)
1. Open Blender
2. Go to the **Scripting** workspace
3. Open the `extrude_edge_to_triangle.py` file (or paste the code)
4. Click **Run Script**

### Method 2: As an addon (recommended)
1. In Blender go to `Edit → Preferences → Add-ons`
2. Click **Install...**
3. Select the `extrude_edge_to_triangle.py` file
4. Enable the addon (check the box)

## How to use

1. Go into **Edit Mode**
2. Switch to **Edge Select** mode (`2`)
3. Select one or more edges
4. Trigger the tool with either:
   - **Shift + E**
   - The top thumb button on a Logitech mouse (`BUTTON5MOUSE`)
5. The new vertices will be selected — press `G` and move them wherever you want

## Hotkeys

| Input              | Action                        |
|--------------------|-------------------------------|
| `Shift + E`        | Extrude Edge to Triangle      |
| Mouse Button 5     | Extrude Edge to Triangle      |

You can change the hotkeys in Blender’s Keymap preferences if you want.

## Why this tool?

When working in a strict triangle-only workflow (especially for N64-style models), constantly extruding quads and then collapsing them is tedious. This tool lets you quickly grow new triangles from existing edges while staying in pure triangles.

## Credits
SirAsterTheCat

Created for a pure-triangle N64 modeling workflow.
