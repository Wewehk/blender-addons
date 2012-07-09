# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Cell Fracture",
    "author": "ideasman42, phymec",
    "version": (0, 1),
    "blender": (2, 6, 4),
    "location": "Search > Fracture Object & Add -> Fracture Helper Objects",
    "description": "Fractured Object, Bomb, Projectile, Recorder",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Object/CellFracture",
    "category": "Object"}


#if "bpy" in locals():
#    import imp
#    imp.reload(fracture_cell_setup)

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty)

from bpy.types import Operator

def main_object(scene, obj, level, **kw):
    import random

    # pull out some args
    kw_copy = kw.copy()
    use_recenter = kw_copy.pop("use_recenter")
    use_remove_original = kw_copy.pop("use_remove_original")
    recursion = kw_copy.pop("recursion")
    recursion_chance = kw_copy.pop("recursion_chance")
    recursion_chance_select = kw_copy.pop("recursion_chance_select")
    use_layer_next = kw_copy.pop("use_layer_next")
    use_layer_index = kw_copy.pop("use_layer_index")
    group_name = kw_copy.pop("group_name")
    use_island_split = kw_copy.pop("use_island_split")
    use_debug_bool = kw_copy.pop("use_debug_bool")
    use_interior_vgroup = kw_copy.pop("use_interior_vgroup")

    from . import fracture_cell_setup

    # not essential but selection is visual distraction.
    obj.select = False

    if kw_copy["use_debug_redraw"]:
        obj_draw_type_prev = obj.draw_type
        obj.draw_type = 'WIRE'
    
    objects = fracture_cell_setup.cell_fracture_objects(scene, obj, **kw_copy)
    objects = fracture_cell_setup.cell_fracture_boolean(scene, obj, objects,
                                                        use_island_split=use_island_split,
                                                        use_interior_vgroup=use_interior_vgroup,
                                                        use_debug_bool=use_debug_bool,
                                                        use_debug_redraw=kw_copy["use_debug_redraw"])

    # todo, split islands.

    # must apply after boolean.
    if use_recenter:
        bpy.ops.object.origin_set({"selected_editable_objects": objects},
                                  type='ORIGIN_GEOMETRY', center='MEDIAN')

    if level < recursion:

        objects_recurse_input = [(i, o) for i, o in enumerate(objects)]

        if recursion_chance != 1.0:
            
            if 0:
                random.shuffle(objects_recurse_input)
            else:
                from mathutils import Vector
                if recursion_chance_select == 'RANDOM':
                    pass
                elif recursion_chance_select == {'SIZE_MIN', 'SIZE_MAX'}:
                    objects_recurse_input.sort(key=lambda ob_pair:
                        (Vector(ob_pair[1].bound_box[0]) -
                         Vector(ob_pair[1].bound_box[6])).length_squared)
                    if recursion_chance_select == 'SIZE_MAX':
                        objects_recurse_input.reverse()
                elif recursion_chance_select == {'CURSOR_MIN', 'CURSOR_MAX'}:
                    print(recursion_chance_select)
                    c = scene.cursor_location.copy()
                    objects_recurse_input.sort(key=lambda ob_pair:
                        (ob_pair[1].matrix_world.translation - c).length_squared)
                    if recursion_chance_select == 'CURSOR_MAX':
                        objects_recurse_input.reverse()

                objects_recurse_input[int(recursion_chance * len(objects_recurse_input)):] = []
                objects_recurse_input.sort()

        # reverse index values so we can remove from original list.
        objects_recurse_input.reverse()

        objects_recursive = []
        for i, obj_cell in objects_recurse_input:
            assert(objects[i] is obj_cell)
            objects_recursive += main_object(scene, obj_cell, level + 1, **kw)
            if use_remove_original:
                scene.objects.unlink(obj_cell)
                del objects[i]
        objects.extend(objects_recursive)

    #--------------
    # Scene Options

    # layer
    layers_new = None
    if use_layer_index != 0:
        layers_new = [False] * 20
        layers_new[use_layer_index - 1] = True
    elif use_layer_next:
        layers_new = [False] * 20
        layers_new[(obj.layers[:].index(True) + 1) % 20] = True

    if layers_new is not None:
        for obj_cell in objects:
            obj_cell.layers = layers_new

    # group
    if group_name:
        group = bpy.data.groups.get(group_name)
        if group is None:
            group = bpy.data.groups.new(group_name)
        for obj_cell in objects:
            group.objects.link(obj_cell)

    if kw_copy["use_debug_redraw"]:
        obj.draw_type = obj_draw_type_prev

    # testing only!
    # obj.hide = True
    return objects


def main(context, **kw):
    import time
    t = time.time()
    scene = context.scene
    objects_context = context.selected_editable_objects

    objects = []
    for obj in objects_context:
        if obj.type == 'MESH':
            objects += main_object(scene, obj, 0, **kw)

    bpy.ops.object.select_all(action='DESELECT')
    for obj_cell in objects:
        obj_cell.select = True
    
    print("Done! %d objects in %.4f sec" % (len(objects), time.time() - t))


class FractureCell(Operator):
    bl_idname = "object.add_fracture_cell_objects"
    bl_label = "Cell fracture selected mesh objects"
    bl_options = {'PRESET'}

    # -------------------------------------------------------------------------
    # Source Options
    source = EnumProperty(
            name="Source",
            items=(('VERT_OWN', "Own Verts", "Use own vertices"),
                   ('VERT_CHILD', "Child Verts", "Use own vertices"),
                   ('PARTICLE_OWN', "Own Particles", ("All particle systems of the "
                                                      "source object")),
                   ('PARTICLE_CHILD', "Child Particles", ("All particle systems of the "
                                                          "child objects")),
                   ('PENCIL', "Grease Pencil", "This objects grease pencil"),
                   ),
            options={'ENUM_FLAG'},
            default={'PARTICLE_OWN', 'VERT_OWN'},
            )

    source_limit = IntProperty(
            name="Source Limit",
            description="Limit the number of input points, 0 for unlimited",
            min=0, max=5000,
            default=1000,
            )

    source_noise = FloatProperty(
            name="Noise",
            description="Randomize point distrobution",
            min=0.0, max=1.0,
            default=0.0,
            )

    cell_scale = FloatVectorProperty(
            name="Scale",
            description="Scale Cell Shape",
            size=3,
            min=0.0, max=1.0,
            default=(1.0, 1.0, 1.0),
            )

    # -------------------------------------------------------------------------
    # Recursion

    recursion = IntProperty(
            name="Recursion",
            description="Break shards resursively",
            min=0, max=5000,
            default=0,
            )

    recursion_chance = FloatProperty(
            name="Random Factor",
            description="Likelyhood of recursion",
            min=0.0, max=1.0,
            default=1.0,
            )

    recursion_chance_select = EnumProperty(
            name="Recurse Over",
            items=(('RANDOM', "Random", ""),
                   ('SIZE_MIN', "Small", "Recursively subdivide smaller objects"),
                   ('SIZE_MAX', "Big", "Recursively subdivide smaller objects"),
                   ('CURSOR_MIN', "Cursor Close", "Recursively subdivide objects closer to the cursor"),
                   ('CURSOR_MAX', "Cursor Far", "Recursively subdivide objects closer to the cursor"),
                   ),
            default='SIZE_MIN',
            )

    # -------------------------------------------------------------------------
    # Mesh Data Options

    use_smooth_faces = BoolProperty(
            name="Smooth Faces",
            default=False,
            )

    use_smooth_edges = BoolProperty(
            name="Smooth Edges",
            description="Set sharp edges whem disabled",
            default=True,
            )

    use_data_match = BoolProperty(
            name="Match Data",
            description="Match original mesh materials and data layers",
            default=True,
            )

    use_island_split = BoolProperty(
            name="Split Islands",
            description="Split disconnected meshes",
            default=True,
            )

    margin = FloatProperty(
            name="Margin",
            description="Gaps for the fracture (gives more stable physics)",
            min=0.0, max=1.0,
            default=0.001,
            )

    material_index = IntProperty(
            name="Material",
            description="Material index for interior faces",
            default=0,
            )

    use_interior_vgroup = BoolProperty(
            name="Interior VGroup",
            description="Create a vertex group for interior verts",
            default=False,
            )

    # -------------------------------------------------------------------------
    # Object Options

    use_recenter = BoolProperty(
            name="Recenter",
            description="Recalculate the center points after splitting",
            default=True,
            )

    use_remove_original = BoolProperty(
            name="Remove Original",
            description="Removes the parents used to create the shatter",
            default=True,
            )

    # -------------------------------------------------------------------------
    # Scene Options
    #
    # .. dirreferent from object options in that this controls how the objects
    #    are setup in the scene.  

    use_layer_index = IntProperty(
            name="Layer Index",
            description="Layer to add the objects into or 0 for existing",
            default=-1,
            min=0, max=20,
            )

    use_layer_next = BoolProperty(
            name="Next Layer",
            description="At the object into the next layer (layer index overrides)",
            default=True,
            )

    group_name = StringProperty(
            name="Group",
            description="Create objects int a group "
                        "(use existing or create new)",
            )

    # -------------------------------------------------------------------------
    # Debug
    use_debug_points = BoolProperty(
            name="Debug Points",
            description="Create mesh data showing the points used for fracture",
            default=False,
            )
            
    use_debug_redraw = BoolProperty(
            name="Show Progress Realtime",
            description="Redraw as fracture is done",
            default=True,
            )

    use_debug_bool = BoolProperty(
            name="Debug Boolean",
            description="Skip applying the boolean modifier",
            default=False,
            )

    def execute(self, context):
        keywords = self.as_keywords()  # ignore=("blah",)

        main(context, **keywords)

        return {'FINISHED'}


    def invoke(self, context, event):
        print(self.recursion_chance_select)
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        col = box.column()
        col.label("Point Source")
        rowsub = col.row()
        rowsub.prop(self, "source")
        rowsub = col.row()
        rowsub.prop(self, "source_limit")
        rowsub.prop(self, "source_noise")
        rowsub = col.row()
        rowsub.prop(self, "cell_scale")

        box = layout.box()
        col = box.column()
        col.label("Recursive Shatter")
        rowsub = col.row(align=True)
        rowsub.prop(self, "recursion")
        rowsub = col.row()
        rowsub.prop(self, "recursion_chance")
        rowsub.prop(self, "recursion_chance_select", expand=True)

        box = layout.box()
        col = box.column()
        col.label("Mesh Data")
        rowsub = col.row()
        rowsub.prop(self, "use_smooth_faces")
        rowsub.prop(self, "use_smooth_edges")
        rowsub.prop(self, "use_data_match")
        rowsub.prop(self, "use_interior_vgroup")
        rowsub.prop(self, "material_index")
        rowsub = col.row()
        # could be own section, control how we subdiv
        rowsub.prop(self, "margin")
        rowsub.prop(self, "use_island_split")

        box = layout.box()
        col = box.column()
        col.label("Object")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_recenter")


        box = layout.box()
        col = box.column()
        col.label("Scene")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_layer_index")
        rowsub.prop(self, "use_layer_next")
        rowsub.prop(self, "group_name")
        
        box = layout.box()
        col = box.column()
        col.label("Debug")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_debug_redraw")
        rowsub.prop(self, "use_debug_points")
        rowsub.prop(self, "use_debug_bool")


def menu_func(self, context):
    layout = self.layout
    layout.label("Cell Fracture:")
    layout.operator("object.add_fracture_cell_objects",
                    text="Cell Fracture")


def register():
    bpy.utils.register_class(FractureCell)
    bpy.types.VIEW3D_PT_tools_objectmode.append(menu_func)


def unregister():
    bpy.utils.unregister_class(FractureCell)
    bpy.types.VIEW3D_PT_tools_objectmode.remove(menu_func)


if __name__ == "__main__":
    register()
