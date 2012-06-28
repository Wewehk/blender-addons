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
    "author": "ideasman42",
    "version": (0, 1),
    "blender": (2, 6, 4),
    "location": "Search > Fracture Object & Add -> Fracture Helper Objects",
    "description": "Fractured Object, Bomb, Projectile, Recorder",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"\
        "Scripts/Object/Fracture",
    "tracker_url": "https://projects.blender.org/tracker/index.php?"\
        "func=detail&aid=21793",
    "category": "Object"}


#if "bpy" in locals():
#    import imp
#    imp.reload(fracture_cell_setup)

import bpy
from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
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
    
    from . import fracture_cell_setup
    
    objects = fracture_cell_setup.cell_fracture_objects(scene, obj, **kw_copy)
    objects = fracture_cell_setup.cell_fracture_boolean(scene, obj, objects)

    # todo, split islands.

    # must apply after boolean.
    if use_recenter:
        bpy.ops.object.origin_set({"selected_editable_objects": objects},
                                  type='ORIGIN_GEOMETRY', center='MEDIAN')

    if level < recursion:
        objects_recursive = []
        for i in range(len(objects) - 1, -1, -1):  # reverse loop
            
            if recursion_chance == 1.0 or recursion_chance < random.random():
                obj_cell = objects[i]
                objects_recursive += main_object(scene, obj_cell, level + 1, **kw)
                if use_remove_original:
                    scene.objects.unlink(obj_cell)
                    del objects[i]
        objects.extend(objects_recursive)
                

    # testing only!
    obj.hide = True
    return objects


def main(context, **kw):
    import time
    t = time.time()
    scene = context.scene
    obj = context.active_object
    objects = main_object(scene, obj, 0, **kw)

    bpy.ops.object.select_all(action='DESELECT')
    for obj_cell in objects:
        obj_cell.select = True
    
    print("Done! %d objects in %.4f sec" % (len(objects), time.time() - t)

class FractureCell(Operator):
    bl_idname = "object.add_fracture_cell_objects"
    bl_label = "Cell Fracture Helper Objects"

    # -------------------------------------------------------------------------
    # Source Options
    source = EnumProperty(
            name="Source",
            items=(('VERT_OWN', "Own Verts", "Use own vertices"),
                   ('EDGE_OWN', "Own Edges", "Use own edges"),
                   ('FACE_OWN', "Own Faces", "Use own faces"),
                   ('VERT_CHILD', "Child Verts", "Use own vertices"),
                   ('EDGE_CHILD', "Child Edges", "Use own edges"),
                   ('FACE_CHILD', "Child Faces", "Use own faces"),
                   ('PARTICLE', "Particles", ("All particle systems of the "
                                              "source object")),
                   ('PENCIL', "Grease Pencil", "This objects grease pencil"),
                   ),
            options={'ENUM_FLAG'},
            default={'PARTICLE', 'VERT_OWN'}  # 'VERT_OWN', 'EDGE_OWN', 'FACE_OWN'
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

    def execute(self, context):
        keywords = self.as_keywords()  # ignore=("blah",)

        main(context, **keywords)

        return {'FINISHED'}


    def invoke(self, context, event):
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

        box = layout.box()
        col = box.column()
        col.label("Mesh Data")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_smooth_faces")
        rowsub.prop(self, "use_smooth_edges")
        rowsub.prop(self, "use_data_match")
        # rowsub.prop(self, "use_island_split")  # TODO

        box = layout.box()
        col = box.column()
        col.label("Object")
        rowsub = col.row(align=True)
        rowsub.prop(self, "use_recenter")

        box = layout.box()
        col = box.column()
        col.label("Recursive Shatter")
        rowsub = col.row(align=True)
        rowsub.prop(self, "recursion")
        rowsub.prop(self, "recursion_chance")

#def menu_func(self, context):
#    self.layout.menu("INFO_MT_add_fracture_objects", icon="PLUGIN")


def register():
    bpy.utils.register_class(FractureCell)

    # Add the "add fracture objects" menu to the "Add" menu
    # bpy.types.INFO_MT_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(FractureCell)

    # Remove "add fracture objects" menu from the "Add" menu.
    # bpy.types.INFO_MT_add.remove(menu_func)


if __name__ == "__main__":
    register()
