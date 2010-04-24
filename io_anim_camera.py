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

# <pep8 compliant>

bl_addon_info = {
    'name': 'I/O: Camera Animation',
    'author': 'Campbell Barton',
    'version': '0.1',
    'blender': (2, 5, 3),
    'location': 'File > Export > Camera Animation',
    'description': 'Export Cameras & Markers',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
           'Scripts/File_I-O/Camera_Animation',
    'category': 'Import/Export'}


import bpy


def writeCameras(context, path, frame_start, frame_end, only_selected=False):

    data_attrs = ['lens', 'shift_x', 'shift_y', 'dof_distance', 'clip_start', 'clip_end', 'draw_size']
    obj_attrs = ['restrict_render']

    fw = open(path, 'w').write

    scene = bpy.context.scene

    cameras = []

    for obj in scene.objects:
        if only_selected and not obj.selected:
            continue
        if obj.type != 'CAMERA':
            continue

        cameras.append((obj, obj.data))

    frame_range = range(frame_start, frame_end + 1)

    fw("cameras = {}\n")
    fw("scene = bpy.context.scene\n")
    fw("frame = scene.frame_current - 1\n")
    fw("\n")

    for obj, obj_data in cameras:
        fw("data = bpy.data.cameras.new('%s')\n" % obj.name)
        for attr in data_attrs:
            fw("data.%s = %s\n" % (attr, repr(getattr(obj_data, attr))))

        fw("obj = bpy.data.objects.new('%s', data)\n" % obj.name)

        for attr in obj_attrs:
            fw("obj.%s = %s\n" % (attr, repr(getattr(obj, attr))))

        fw("scene.objects.link(obj)\n")
        fw("cameras['%s'] = obj\n" % obj.name)
        fw("\n")


    for f in frame_range:
        scene.set_frame(f)
        fw("# new frame\n")
        fw("scene.set_frame(%d + frame)\n" % f)

        for obj, obj_data in cameras:
            fw("obj = cameras['%s']\n" % obj.name)

            matrix = obj.matrix.copy()
            fw("obj.location = %s\n" % repr(tuple(matrix.translation_part())))
            fw("obj.scale = %s\n" % repr(tuple(matrix.scale_part())))
            fw("obj.rotation_euler = %s\n" % repr(tuple(matrix.to_euler())))

            fw("obj.keyframe_insert('location')\n")
            fw("obj.keyframe_insert('scale')\n")
            fw("obj.keyframe_insert('rotation_euler')\n")

            # only key the angle
            fw("data = obj.data\n")
            fw("data.lens = %s\n" % obj_data.lens)
            fw("data.keyframe_insert('lens')\n")

            fw("\n")

    # now markers
    fw("# markers\n")
    for marker in scene.timeline_markers:
        fw("marker = scene.timeline_markers.add('%s')\n" % marker.name)
        fw("marker.frame = %d + frame\n" % marker.frame)

        # will fail if the cameras not selected
        if marker.camera:
            fw("marker.camera = cameras.get('%s')\n" % marker.camera.name)
        fw("\n")


from bpy.props import *


class CameraExporter(bpy.types.Operator):
    '''Save a python script which re-creartes cameras and markers elsewhere'''
    bl_idname = "export_animation.cameras"
    bl_label = "Export Camera & Markers"

    path = StringProperty(name="File Path", description="File path used for importing the RAW file", maxlen=1024, default="")
    filename = StringProperty(name="File Name", description="Name of the file.")
    directory = StringProperty(name="Directory", description="Directory of the file.")

    frame_start = IntProperty(name="Start Frame",
            description="Start frame for export",
            default=1, min=1, max=300000)
    frame_end = IntProperty(name="End Frame",
            description="End frame for export",
            default=250, min=1, max=300000)
    only_selected = BoolProperty(name="Only Selected",
            default=True)

    def execute(self, context):
        writeCameras(context, self.properties.path, self.properties.frame_start, self.properties.frame_end, self.properties.only_selected)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.properties.frame_start = context.scene.frame_start
        self.properties.frame_end = context.scene.frame_end

        wm = context.manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}


def menu_export(self, context):
    default_path = bpy.data.filename.replace(".blend", ".py")
    self.layout.operator(CameraExporter.bl_idname, text="Cameras & Markers (.py)").path = default_path


def register():
    bpy.types.register(CameraExporter)
    bpy.types.INFO_MT_file_export.append(menu_export)

if __name__ == "__main__":
    register()
