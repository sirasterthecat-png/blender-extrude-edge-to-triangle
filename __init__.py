bl_info = {
    "name": "Extrude Edge to Triangle",
    "author": "SirAster",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "Edit Mode > Mesh",
    "description": "Creates a triangle from selected edge(s) by placing a new vertex at the midpoint. Perfect for pure-triangle / N64-style modeling workflows.",
    "category": "Mesh",
}

import bpy
import bmesh

class MESH_OT_extrude_edge_to_triangle(bpy.types.Operator):
    """Create a triangle from selected edge(s) with new vertex at the midpoint"""
    bl_idname = "mesh.extrude_edge_to_triangle"
    bl_label = "Extrude Edge to Triangle"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "No mesh object")
            return {'CANCELLED'}

        if context.mode != 'EDIT_MESH':
            bpy.ops.object.mode_set(mode='EDIT')

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.edges.ensure_lookup_table()
        bm.verts.ensure_lookup_table()

        selected_edges = [e for e in bm.edges if e.select]
        if not selected_edges:
            self.report({'ERROR'}, "No edges selected")
            return {'CANCELLED'}

        new_verts = []

        for edge in selected_edges:
            v1 = edge.verts[0]
            v2 = edge.verts[1]

            # Create new vertex exactly at the midpoint
            mid = (v1.co + v2.co) * 0.5
            new_vert = bm.verts.new(mid)
            new_verts.append(new_vert)

            # Create the triangle
            try:
                bm.faces.new((v1, v2, new_vert))
            except ValueError:
                # Face already exists
                bm.verts.remove(new_vert)
                if new_vert in new_verts:
                    new_verts.remove(new_vert)

        # Deselect everything
        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for f in bm.faces:
            f.select = False

        # Select only the new vertices
        for v in new_verts:
            v.select = True

        bm.select_history.clear()
        if new_verts:
            bm.select_history.add(new_verts[-1])

        bmesh.update_edit_mesh(me)
        self.report({'INFO'}, f"Created {len(new_verts)} triangle(s) – pull the new vertex/vertices with G")
        return {'FINISHED'}


# Keymap storage
addon_keymaps = []


def register():
    bpy.utils.register_class(MESH_OT_extrude_edge_to_triangle)

    # Add hotkeys
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')

        # Mouse thumb button (BUTTON5MOUSE)
        kmi_mouse = km.keymap_items.new(
            MESH_OT_extrude_edge_to_triangle.bl_idname,
            type='BUTTON5MOUSE',
            value='PRESS'
        )
        addon_keymaps.append((km, kmi_mouse))

        # Keyboard shortcut: Shift + E
        kmi_key = km.keymap_items.new(
            MESH_OT_extrude_edge_to_triangle.bl_idname,
            type='E',
            value='PRESS',
            shift=True
        )
        addon_keymaps.append((km, kmi_key))


def unregister():
    # Remove hotkeys
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(MESH_OT_extrude_edge_to_triangle)


if __name__ == "__main__":
    register()
