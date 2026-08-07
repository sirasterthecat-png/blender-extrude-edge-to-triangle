bl_info = {
    "name": "N64 Triangle Extrude Tools",
    "author": "SirAster",
    "version": (1, 1, 1),
    "blender": (3, 0, 0),
    "location": "Edit Mode > Mesh",
    "description": "Two pure-triangle extrude tools for N64-style modeling",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector


def get_ordered_edge_loop(bm, selected_edges):
    if len(selected_edges) < 3:
        return None

    edge_map = {}
    for e in selected_edges:
        v1, v2 = e.verts
        edge_map.setdefault(v1, []).append(e)
        edge_map.setdefault(v2, []).append(e)

    for v, edges in edge_map.items():
        if len(edges) != 2:
            return None

    start_edge = selected_edges[0]
    ordered = [start_edge]
    current_vert = start_edge.verts[1]
    prev_edge = start_edge

    for _ in range(len(selected_edges) - 1):
        candidates = edge_map[current_vert]
        next_edge = candidates[0] if candidates[0] != prev_edge else candidates[1]
        ordered.append(next_edge)
        current_vert = next_edge.other_vert(current_vert)
        prev_edge = next_edge

    return ordered


class MESH_OT_extrude_edge_to_triangle(bpy.types.Operator):
    """Create a triangle from each selected edge by placing a new vertex at the midpoint"""
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
            mid = (edge.verts[0].co + edge.verts[1].co) * 0.5
            new_vert = bm.verts.new(mid)
            new_verts.append(new_vert)
            try:
                bm.faces.new((edge.verts[0], edge.verts[1], new_vert))
            except ValueError:
                pass

        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for f in bm.faces:
            f.select = False

        for v in new_verts:
            v.select = True

        bmesh.update_edit_mesh(me)
        self.report({'INFO'}, f"Created {len(new_verts)} triangle(s)")
        return {'FINISHED'}


class MESH_OT_extrude_edge_loop_to_triangles(bpy.types.Operator):
    """Extrude a closed edge loop into a pure-triangle polygonal ring (N64 style)"""
    bl_idname = "mesh.extrude_edge_loop_to_triangles"
    bl_label = "Extrude Edge Loop to Triangles"
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
        if len(selected_edges) < 3:
            self.report({'ERROR'}, "Select a closed loop of at least 3 edges")
            return {'CANCELLED'}

        ordered_edges = get_ordered_edge_loop(bm, selected_edges)
        if ordered_edges is None:
            self.report({'ERROR'}, "Selection is not a single clean closed edge loop")
            return {'CANCELLED'}

        n = len(ordered_edges)

        normal = Vector((0, 0, 0))
        for e in ordered_edges:
            normal += (e.verts[0].co + e.verts[1].co)
        if normal.length > 0.0001:
            normal.normalize()
        else:
            normal = Vector((0, 0, 1))

        new_verts = []
        for edge in ordered_edges:
            mid = (edge.verts[0].co + edge.verts[1].co) * 0.5
            nv = bm.verts.new(mid + normal * 0.008)
            new_verts.append(nv)

        bm.verts.ensure_lookup_table()

        for i, edge in enumerate(ordered_edges):
            try:
                bm.faces.new((edge.verts[0], edge.verts[1], new_verts[i]))
            except ValueError:
                pass

        for i in range(n):
            edge_a = ordered_edges[i]
            edge_b = ordered_edges[(i + 1) % n]
            mid_a = new_verts[i]
            mid_b = new_verts[(i + 1) % n]

            shared = None
            for v in edge_a.verts:
                if v in edge_b.verts:
                    shared = v
                    break

            if shared:
                try:
                    bm.faces.new((mid_a, shared, mid_b))
                except ValueError:
                    pass

        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False
        for f in bm.faces:
            f.select = False

        for v in new_verts:
            v.select = True

        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_mode(type='VERT')

        self.report({'INFO'}, f"Created polygonal ring with {n} mid vertices")
        return {'FINISHED'}


addon_keymaps = []

def register():
    bpy.utils.register_class(MESH_OT_extrude_edge_to_triangle)
    bpy.utils.register_class(MESH_OT_extrude_edge_loop_to_triangles)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')

        # Normal front thumb button → single triangle extrude
        kmi1 = km.keymap_items.new(
            MESH_OT_extrude_edge_to_triangle.bl_idname,
            type='BUTTON5MOUSE', value='PRESS'
        )
        addon_keymaps.append((km, kmi1))

        # Shift + front thumb button → complex loop extrude
        kmi2 = km.keymap_items.new(
            MESH_OT_extrude_edge_loop_to_triangles.bl_idname,
            type='BUTTON5MOUSE', value='PRESS', shift=True
        )
        addon_keymaps.append((km, kmi2))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(MESH_OT_extrude_edge_to_triangle)
    bpy.utils.unregister_class(MESH_OT_extrude_edge_loop_to_triangles)


if __name__ == "__main__":
    register()
