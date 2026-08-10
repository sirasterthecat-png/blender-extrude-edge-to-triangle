bl_info = {
    "name": "N64 Triangle Extrude Tools",
    "author": "SirAster",
    "version": (1, 3, 1),
    "blender": (3, 0, 0),
    "location": "Edit Mode > Mesh",
    "description": "Pure-triangle extrude and smart face tools for N64-style modeling",
    "category": "Mesh",
}

import bpy
import bmesh
from mathutils import Vector


def get_ordered_edge_loop(bm, selected_edges):
    """Return one clean closed loop as ordered vertices and ordered edges.

    Rejects branched selections, open chains, disconnected loops, and repeated
    traversal.  For N selected edges a valid loop returns N vertices and N
    edges, with edge i connecting vertex i to vertex (i + 1) % N.
    """
    if len(selected_edges) < 3:
        return None, None

    selected_set = set(selected_edges)
    edge_map = {}
    for edge in selected_edges:
        v1, v2 = edge.verts
        edge_map.setdefault(v1, []).append(edge)
        edge_map.setdefault(v2, []).append(edge)

    # Every vertex in a simple closed cycle has degree exactly 2 within the
    # selected edge set.
    if any(len(edges) != 2 for edges in edge_map.values()):
        return None, None

    start_edge = selected_edges[0]
    start_vert = start_edge.verts[0]
    current_vert = start_edge.verts[1]

    ordered_verts = [start_vert, current_vert]
    ordered_edges = [start_edge]
    used_edges = {start_edge}
    prev_edge = start_edge

    while len(used_edges) < len(selected_edges):
        candidates = [
            edge for edge in edge_map[current_vert]
            if edge != prev_edge and edge not in used_edges
        ]

        if len(candidates) != 1:
            return None, None

        next_edge = candidates[0]
        next_vert = next_edge.other_vert(current_vert)

        ordered_edges.append(next_edge)
        used_edges.add(next_edge)

        if next_vert == start_vert:
            # Closing early means there is at least one disconnected cycle in
            # the selection, which this operator should not try to extrude.
            if len(used_edges) != len(selected_edges):
                return None, None
            current_vert = next_vert
            break

        ordered_verts.append(next_vert)
        prev_edge = next_edge
        current_vert = next_vert

    if current_vert != start_vert:
        return None, None

    if len(ordered_verts) != len(selected_edges):
        return None, None

    if used_edges != selected_set:
        return None, None

    return ordered_verts, ordered_edges


def calculate_loop_normal(ordered_verts):
    """Calculate a translation-invariant normal from a closed vertex loop."""
    if len(ordered_verts) < 3:
        return None

    center = Vector((0.0, 0.0, 0.0))
    for vert in ordered_verts:
        center += vert.co
    center /= len(ordered_verts)

    normal = Vector((0.0, 0.0, 0.0))
    for i, vert in enumerate(ordered_verts):
        a = vert.co - center
        b = ordered_verts[(i + 1) % len(ordered_verts)].co - center
        normal += a.cross(b)

    if normal.length <= 1.0e-10:
        return None

    normal.normalize()
    return normal


def rebuild_ordered_edges(ordered_verts, selected_edges):
    """Rebuild edge order after the vertex winding has been reversed."""
    selected_set = set(selected_edges)
    result = []

    for i, vert in enumerate(ordered_verts):
        next_vert = ordered_verts[(i + 1) % len(ordered_verts)]
        edge = next((
            e for e in vert.link_edges
            if e in selected_set and e.other_vert(vert) == next_vert
        ), None)
        if edge is None:
            return None
        result.append(edge)

    return result


def orient_loop_outward(ordered_verts, ordered_edges, selected_edges, normal):
    """Prefer the side of the loop away from already-connected geometry.

    This gives a boundary ring at the end of a limb/tube a predictable
    extrusion direction.  An isolated edge ring has no interior reference, so
    its existing winding is retained.
    """
    loop_center = Vector((0.0, 0.0, 0.0))
    for vert in ordered_verts:
        loop_center += vert.co
    loop_center /= len(ordered_verts)

    # Adjacent face centers are the best hint for which side contains the
    # existing mesh.  Deduplicate faces because neighboring selected edges can
    # refer to the same face.
    adjacent_faces = set()
    for edge in ordered_edges:
        adjacent_faces.update(edge.link_faces)

    reference_points = [face.calc_center_median() for face in adjacent_faces]

    # For a naked ring, fall back to non-loop neighboring vertices.
    if not reference_points:
        loop_vert_set = set(ordered_verts)
        selected_set = set(selected_edges)
        neighbor_verts = set()
        for vert in ordered_verts:
            for edge in vert.link_edges:
                if edge in selected_set:
                    continue
                other = edge.other_vert(vert)
                if other not in loop_vert_set:
                    neighbor_verts.add(other)
        reference_points = [vert.co.copy() for vert in neighbor_verts]

    if not reference_points:
        return ordered_verts, ordered_edges, normal

    interior_center = Vector((0.0, 0.0, 0.0))
    for point in reference_points:
        interior_center += point
    interior_center /= len(reference_points)

    away = loop_center - interior_center
    if away.length <= 1.0e-10 or normal.dot(away) >= 0.0:
        return ordered_verts, ordered_edges, normal

    # Reverse the cycle while keeping the first vertex stable.  Reversing the
    # winding flips the geometric normal and keeps the generated triangle
    # winding consistent with the chosen extrusion direction.
    ordered_verts = [ordered_verts[0]] + list(reversed(ordered_verts[1:]))
    ordered_edges = rebuild_ordered_edges(ordered_verts, selected_edges)
    if ordered_edges is None:
        return None, None, None

    normal = -normal
    return ordered_verts, ordered_edges, normal


def split_triangle_by_longest_edge(bm, face):
    if not face.is_valid or len(face.verts) != 3:
        return None

    edges = list(face.edges)
    edges.sort(key=lambda e: e.calc_length(), reverse=True)
    edge = edges[0]

    v1 = edge.verts[0]
    v2 = edge.verts[1]

    opposite = None
    for v in face.verts:
        if v not in (v1, v2):
            opposite = v
            break

    if opposite is None:
        return None

    result = bmesh.utils.edge_split(edge, v1, 0.5)
    mid_vert = None
    for item in result:
        if isinstance(item, bmesh.types.BMVert):
            mid_vert = item
            break

    if mid_vert is None:
        return None

    try:
        bmesh.ops.connect_vert_pair(bm, verts=[mid_vert, opposite])
    except:
        try:
            bm.edges.new((mid_vert, opposite))
        except:
            pass

    return mid_vert


def extrude_edge_to_triangle(bm, selected_edges):
    new_verts = []
    for edge in selected_edges:
        mid = (edge.verts[0].co + edge.verts[1].co) * 0.5
        new_vert = bm.verts.new(mid)
        new_verts.append(new_vert)
        try:
            bm.faces.new((edge.verts[0], edge.verts[1], new_vert))
        except ValueError:
            pass
    return new_verts


class MESH_OT_extrude_edge_to_triangle(bpy.types.Operator):
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

        new_verts = extrude_edge_to_triangle(bm, selected_edges)

        for v in bm.verts: v.select = False
        for e in bm.edges: e.select = False
        for f in bm.faces: f.select = False
        for v in new_verts: v.select = True

        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_mode(type='VERT')
        self.report({'INFO'}, f"Created {len(new_verts)} triangle(s)")
        return {'FINISHED'}


class MESH_OT_smart_face_tool(bpy.types.Operator):
    """Triangle → split by longest edge | Quad → triangulate"""
    bl_idname = "mesh.smart_face_tool"
    bl_label = "Smart Face Tool"
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
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        selected_faces = [f for f in bm.faces if f.select]
        if not selected_faces:
            self.report({'WARNING'}, "No faces selected")
            return {'CANCELLED'}

        new_verts = []
        triangulated = 0
        split_count = 0

        for face in list(selected_faces):
            if not face.is_valid:
                continue

            vert_count = len(face.verts)

            if vert_count == 3:
                mid = split_triangle_by_longest_edge(bm, face)
                if mid:
                    new_verts.append(mid)
                    split_count += 1

            elif vert_count == 4:
                try:
                    bmesh.ops.triangulate(bm, faces=[face])
                    triangulated += 1
                except:
                    pass

            bm.faces.ensure_lookup_table()
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()

        for v in bm.verts: v.select = False
        for e in bm.edges: e.select = False
        for f in bm.faces: f.select = False

        for v in new_verts:
            if v.is_valid:
                v.select = True

        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_mode(type='VERT')

        msg = []
        if split_count:
            msg.append(f"Split {split_count} triangle(s)")
        if triangulated:
            msg.append(f"Triangulated {triangulated} quad(s)")
        self.report({'INFO'}, " | ".join(msg) if msg else "Nothing done")
        return {'FINISHED'}


class MESH_OT_extrude_edge_loop_to_triangles(bpy.types.Operator):
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
            self.report({'ERROR'}, "Select one closed loop of at least 3 edges")
            return {'CANCELLED'}

        # Adding another face to an edge that already has two faces would make
        # non-manifold geometry.  Boundary edges (1 face) and naked rings
        # (0 faces) are safe for this construction tool.
        if any(len(edge.link_faces) > 1 for edge in selected_edges):
            self.report({'ERROR'}, "Loop contains non-boundary edges (2+ linked faces)")
            return {'CANCELLED'}

        ordered_verts, ordered_edges = get_ordered_edge_loop(bm, selected_edges)
        if ordered_edges is None:
            self.report({'ERROR'}, "Selection must be one clean closed edge loop")
            return {'CANCELLED'}

        normal = calculate_loop_normal(ordered_verts)
        if normal is None:
            self.report({'ERROR'}, "Loop is degenerate; could not determine its plane")
            return {'CANCELLED'}

        ordered_verts, ordered_edges, normal = orient_loop_outward(
            ordered_verts, ordered_edges, selected_edges, normal
        )
        if ordered_edges is None:
            self.report({'ERROR'}, "Could not resolve loop winding")
            return {'CANCELLED'}

        n = len(ordered_edges)

        # Scale the tiny seed offset to the selected topology instead of using
        # a hard-coded object-space distance.  The offset only gives the new
        # triangles non-zero area before the user moves the selected ring.
        average_edge_length = sum(edge.calc_length() for edge in ordered_edges) / n
        seed_offset = max(average_edge_length * 0.01, 1.0e-6)

        new_verts = []
        for i, edge in enumerate(ordered_edges):
            v1 = ordered_verts[i]
            v2 = ordered_verts[(i + 1) % n]
            mid = (v1.co + v2.co) * 0.5
            nv = bm.verts.new(mid + normal * seed_offset)
            new_verts.append(nv)

        bm.verts.ensure_lookup_table()

        # First triangle on each original edge.
        for i in range(n):
            v1 = ordered_verts[i]
            v2 = ordered_verts[(i + 1) % n]
            try:
                bm.faces.new((v1, v2, new_verts[i]))
            except ValueError:
                pass

        # Second triangle bridges neighboring midpoint vertices.  Together the
        # two passes create an all-triangle strip/ring with consistent winding.
        for i in range(n):
            shared = ordered_verts[(i + 1) % n]
            mid_a = new_verts[i]
            mid_b = new_verts[(i + 1) % n]
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

        bm.normal_update()
        bmesh.update_edit_mesh(me)
        bpy.ops.mesh.select_mode(type='VERT')
        self.report({'INFO'}, f"Created triangle ring with {n} midpoint vertices")
        return {'FINISHED'}


addon_keymaps = []

def register():
    bpy.utils.register_class(MESH_OT_extrude_edge_to_triangle)
    bpy.utils.register_class(MESH_OT_smart_face_tool)
    bpy.utils.register_class(MESH_OT_extrude_edge_loop_to_triangles)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Mesh', space_type='EMPTY')

        # Front thumb button → Extrude Edge to Triangle
        kmi1 = km.keymap_items.new(
            "mesh.extrude_edge_to_triangle",
            type='BUTTON5MOUSE', value='PRESS'
        )
        addon_keymaps.append((km, kmi1))

        # Back thumb button → Smart Face Tool
        kmi2 = km.keymap_items.new(
            "mesh.smart_face_tool",
            type='BUTTON4MOUSE', value='PRESS'
        )
        addon_keymaps.append((km, kmi2))

        # Shift + Front thumb button → Loop extrude
        kmi3 = km.keymap_items.new(
            "mesh.extrude_edge_loop_to_triangles",
            type='BUTTON5MOUSE', value='PRESS', shift=True
        )
        addon_keymaps.append((km, kmi3))


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.utils.unregister_class(MESH_OT_extrude_edge_to_triangle)
    bpy.utils.unregister_class(MESH_OT_smart_face_tool)
    bpy.utils.unregister_class(MESH_OT_extrude_edge_loop_to_triangles)


if __name__ == "__main__":
    register()
