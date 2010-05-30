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

import bpy
from mathutils import *
from math import *
from bpy.props import *

bl_addon_info = {
    'name': 'Add Mesh: Extras',
    'author': 'Pontiac, Fourmadmen, meta-androcto',
    'version': '0.3',
    'blender': (2, 5, 3),
    'location': 'View3D > Add > Mesh > Extras',
    'description': 'Adds Star, Wedge, Sqorus & Spindle objects.',
    'url': 'http://wiki.blender.org/index.php/Extensions:2.5/Py/' \
        'Scripts/Add_Mesh/',
    'category': 'Add Mesh'}


# Stores the values of a list of properties and the
# operator id in a property group ('recall_op') inside the object.
# Could (in theory) be used for non-objects.
# Note: Replaces any existing property group with the same name!
# ob ... Object to store the properties in.
# op ... The operator that should be used.
# op_args ... A dictionary with valid Blender
#             properties (operator arguments/parameters).
def store_recall_properties(ob, op, op_args):
    if ob and op and op_args:
        recall_properties = {}

        # Add the operator identifier and op parameters to the properties.
        recall_properties['op'] = op.bl_idname
        recall_properties['args'] = op_args

        # Store new recall properties.
        ob['recall'] = recall_properties


# calculates the matrix for the new object
# depending on user pref
def align_matrix(context):
    loc = TranslationMatrix(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
        and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.rotation_part().invert().resize4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot
    return align_matrix

# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
# edit ... Replace existing mesh data.
# Note: Using "edit" will destroy/delete existing mesh data.
def create_mesh_object(context, verts, edges, faces, name, edit, align_matrix):
    scene = context.scene
    obj_act = scene.objects.active

    # Can't edit anything, unless we have an active obj.
    if edit and not obj_act:
        return None

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    # Deselect all objects.
    bpy.ops.object.select_all(action='DESELECT')

    if edit:
        # Replace geometry of existing object

        # Use the active obj and select it.
        ob_new = obj_act
        ob_new.selected = True

        if obj_act.mode == 'OBJECT':
            # Get existing mesh datablock.
            old_mesh = ob_new.data

            # Set object data to nothing
            ob_new.data = None

            # Clear users of existing mesh datablock.
            old_mesh.user_clear()

            # Remove old mesh datablock if no users are left.
            if (old_mesh.users == 0):
                bpy.data.meshes.remove(old_mesh)

            # Assign new mesh datablock.
            ob_new.data = mesh

    else:
        # Create new object
        ob_new = bpy.data.objects.new(name, mesh)

        # Link new object to the given scene and select it.
        scene.objects.link(ob_new)
        ob_new.selected = True

        # Place the object at the 3D cursor location.
        # apply viewRotaion
        ob_new.matrix = align_matrix

    if obj_act and obj_act.mode == 'EDIT':
        if not edit:
            # We are in EditMode, switch to ObjectMode.
            bpy.ops.object.mode_set(mode='OBJECT')

            # Select the active object as well.
            obj_act.selected = True

            # Apply location of new object.
            scene.update()

            # Join new object into the active.
            bpy.ops.object.join()

            # Switching back to EditMode.
            bpy.ops.object.mode_set(mode='EDIT')

            ob_new = obj_act

    else:
        # We are in ObjectMode.
        # Make the new object the active one.
        scene.objects.active = ob_new

    return ob_new


# A very simple "bridge" tool.
# Connects two equally long vertex rows with faces.
# Returns a list of the new faces (list of  lists)
#
# vertIdx1 ... First vertex list (list of vertex indices).
# vertIdx2 ... Second vertex list (list of vertex indices).
# closed ... Creates a loop (first & last are closed).
# flipped ... Invert the normal of the face(s).
#
# Note: You can set vertIdx1 to a single vertex index to create
#       a fan/star of faces.
# Note: If both vertex idx list are the same length they have
#       to have at least 2 vertices.
def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                    vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                    vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces


# @todo Clean up vertex&face creation process a bit.
def add_sqorus(hole_size, subdivide):
    verts = []
    faces = []

    size = 2.0

    thickness = (size - hole_size) / 2.0
    distances = [
        -size / 2.0,
        -size / 2.0 + thickness,
        size / 2.0 - thickness,
        size / 2.0]

    if subdivide:
        for i in range(4):
            y = distances[i]

            for j in range(4):
                x = distances[j]

                verts.append(Vector((x, y, size / 2.0)))
                verts.append(Vector((x, y, -size / 2.0)))

        # Top outer loop (vertex indices)
        vIdx_out_up = [0, 2, 4, 6, 14, 22, 30, 28, 26, 24, 16, 8]
        # Lower outer loop (vertex indices)
        vIdx_out_low = [i + 1 for i in vIdx_out_up]

        faces_outside = createFaces(vIdx_out_up, vIdx_out_low, closed=True)
        faces.extend(faces_outside)

        # Top inner loop (vertex indices)
        vIdx_inner_up = [10, 12, 20, 18]

        # Lower inner loop (vertex indices)
        vIdx_inner_low = [i + 1 for i in vIdx_inner_up]

        faces_inside = createFaces(vIdx_inner_up, vIdx_inner_low,
            closed=True, flipped=True)
        faces.extend(faces_inside)

        row1_top = [0, 8, 16, 24]
        row2_top = [i + 2 for i in row1_top]
        row3_top = [i + 2 for i in row2_top]
        row4_top = [i + 2 for i in row3_top]

        faces_top1 = createFaces(row1_top, row2_top)
        faces.extend(faces_top1)
        faces_top2_side1 = createFaces(row2_top[:2], row3_top[:2])
        faces.extend(faces_top2_side1)
        faces_top2_side2 = createFaces(row2_top[2:], row3_top[2:])
        faces.extend(faces_top2_side2)
        faces_top3 = createFaces(row3_top, row4_top)
        faces.extend(faces_top3)

        row1_bot = [1, 9, 17, 25]
        row2_bot = [i + 2 for i in row1_bot]
        row3_bot = [i + 2 for i in row2_bot]
        row4_bot = [i + 2 for i in row3_bot]

        faces_bot1 = createFaces(row1_bot, row2_bot, flipped=True)
        faces.extend(faces_bot1)
        faces_bot2_side1 = createFaces(row2_bot[:2], row3_bot[:2],
            flipped=True)
        faces.extend(faces_bot2_side1)
        faces_bot2_side2 = createFaces(row2_bot[2:], row3_bot[2:],
            flipped=True)
        faces.extend(faces_bot2_side2)
        faces_bot3 = createFaces(row3_bot, row4_bot, flipped=True)
        faces.extend(faces_bot3)

    else:
        # Do not subdivde outer faces

        vIdx_out_up = []
        vIdx_out_low = []
        vIdx_in_up = []
        vIdx_in_low = []

        for i in range(4):
            y = distances[i]

            for j in range(4):
                x = distances[j]

                append = False
                inner = False
                # Outer
                if (i in [0, 3] and j in [0, 3]):
                    append = True

                # Inner
                if (i in [1, 2] and j in [1, 2]):
                    append = True
                    inner = True

                if append:
                    vert_up = len(verts)
                    verts.append(Vector((x, y, size / 2.0)))
                    vert_low = len(verts)
                    verts.append(Vector((x, y, -size / 2.0)))

                    if inner:
                        vIdx_in_up.append(vert_up)
                        vIdx_in_low.append(vert_low)

                    else:
                        vIdx_out_up.append(vert_up)
                        vIdx_out_low.append(vert_low)

        # Flip last two vertices
        vIdx_out_up = vIdx_out_up[:2] + list(reversed(vIdx_out_up[2:]))
        vIdx_out_low = vIdx_out_low[:2] + list(reversed(vIdx_out_low[2:]))
        vIdx_in_up = vIdx_in_up[:2] + list(reversed(vIdx_in_up[2:]))
        vIdx_in_low = vIdx_in_low[:2] + list(reversed(vIdx_in_low[2:]))

        # Create faces
        faces_top = createFaces(vIdx_in_up, vIdx_out_up, closed=True)
        faces.extend(faces_top)
        faces_bottom = createFaces(vIdx_out_low, vIdx_in_low, closed=True)
        faces.extend(faces_bottom)
        faces_inside = createFaces(vIdx_in_low, vIdx_in_up, closed=True)
        faces.extend(faces_inside)
        faces_outside = createFaces(vIdx_out_up, vIdx_out_low, closed=True)
        faces.extend(faces_outside)

    return verts, faces


def add_wedge(size_x, size_y, size_z):
    verts = []
    faces = []

    size_x /= 2.0
    size_y /= 2.0
    size_z /= 2.0

    vIdx_top = []
    vIdx_bot = []

    vIdx_top.append(len(verts))
    verts.append(Vector((-size_x, -size_y, size_z)))
    vIdx_bot.append(len(verts))
    verts.append(Vector((-size_x, -size_y, -size_z)))

    vIdx_top.append(len(verts))
    verts.append(Vector((size_x, -size_y, size_z)))
    vIdx_bot.append(len(verts))
    verts.append(Vector((size_x, -size_y, -size_z)))

    vIdx_top.append(len(verts))
    verts.append(Vector((-size_x, size_y, size_z)))
    vIdx_bot.append(len(verts))
    verts.append(Vector((-size_x, size_y, -size_z)))

    faces.append(vIdx_top)
    faces.append(vIdx_bot)
    faces_outside = createFaces(vIdx_top, vIdx_bot, closed=True)
    faces.extend(faces_outside)

    return verts, faces

def add_spindle(segments, radius, height, cap_height):
    verts = []
    faces = []

    tot_verts = segments * 2 + 2

    half_height = height / 2.0

    # Upper tip
    idx_upper_tip = len(verts)
    verts.append(Vector((0, 0, half_height + cap_height)))

    # Lower tip
    idx_lower_tip = len(verts)
    verts.append(Vector((0.0, 0.0, -half_height - cap_height)))

    upper_edgeloop = []
    lower_edgeloop = []
    for index in range(segments):
        mtx = RotationMatrix(2.0 * pi * float(index) / segments, 3, 'Z')

        # Calculate index & location of upper verte4x tip.
        idx_up = len(verts)
        upper_edgeloop.append(idx_up)
        verts.append(Vector((radius, 0.0, half_height)) * mtx)

        if height > 0:
            idx_low = len(verts)
            lower_edgeloop.append(idx_low)
            verts.append(Vector((radius, 0.0, -half_height)) * mtx)

    # Create faces for the upper tip.
    tip_up_faces = createFaces([idx_upper_tip], upper_edgeloop,
        closed=True, flipped=True)
    faces.extend(tip_up_faces)

    if height > 0:
        # Create faces for the middle cylinder.
        cyl_faces = createFaces(lower_edgeloop, upper_edgeloop, closed=True)
        faces.extend(cyl_faces)

        # Create faces for the lower tip.
        tip_low_faces = createFaces([idx_lower_tip], lower_edgeloop,
            closed=True)
        faces.extend(tip_low_faces)

    else:
        # Skipping middle part/cylinder (height=0).

        # Create faces for the lower tip.
        tip_low_faces = createFaces([idx_lower_tip], upper_edgeloop,
            closed=True)
        faces.extend(tip_low_faces)

    return verts, faces

def add_star(points, outer_radius, inner_radius, height):
    PI_2 = pi * 2
    z_axis = (0, 0, 1)

    verts = []
    faces = []

    segments = points * 2

    half_height = height / 2.0

    vert_idx_top = len(verts)
    verts.append(Vector((0.0, 0.0, half_height)))

    vert_idx_bottom = len(verts)
    verts.append(Vector((0.0, 0.0, -half_height)))

    edgeloop_top = []
    edgeloop_bottom = []

    for index in range(segments):
        quat = Quaternion(z_axis, (index / segments) * PI_2)

        if index % 2:
            # Uneven
            radius = outer_radius
        else:
            # Even
            radius = inner_radius

        edgeloop_top.append(len(verts))
        vec = Vector((radius, 0, half_height)) * quat
        verts.append(vec)

        edgeloop_bottom.append(len(verts))
        vec = Vector((radius, 0, -half_height)) * quat
        verts.append(vec)



    faces_top = createFaces([vert_idx_top], edgeloop_top, closed=True)
    faces_outside = createFaces(edgeloop_top, edgeloop_bottom, closed=True)
    faces_bottom = createFaces([vert_idx_bottom], edgeloop_bottom,
        flipped=True, closed=True)

    faces.extend(faces_top)
    faces.extend(faces_outside)
    faces.extend(faces_bottom)

    return verts, faces

def trapezohedron(s,r,h):
    """
    s = segments
    r = base radius
    h = tip height
    """
    
    # calculate constants
    a = 2*pi/(2*s)          # angle between points along the equator
    l = r*cos(a)            # helper for  e
    e = h*(r-l)/(l+r)       # the z offset for each vector along the equator so faces are planar

    # rotation for the points
    quat = Quaternion((0,0,1),a)
    
    # first 3 vectors, every next one is calculated from the last, and the z-value is negated
    verts = [Vector(i) for i in [(0,0,h),(0,0,-h),(r,0,e)]]
    for i in range(2*s-1):
        verts.append(verts[-1]*quat)    # rotate further "a" radians around the z-axis
        verts[-1].z *= -1               # negate last z-value to account for the zigzag 
    
    faces = []
    for i in range(2,2+2*s,2):
        n = [i+1,i+2,i+3]               # vertices in current section
        for j in range(3):              # check whether the numbers dont go over len(verts)
            if n[j]>=2*s+2: n[j]-=2*s   # if so, subtract len(verts)-2
        
        # add faces of current section
        faces.append([0,i]+n[:2])
        faces.append([1,n[2],n[1],n[0]])
    
    return verts,faces

class AddSqorus(bpy.types.Operator):
    '''Add a sqorus mesh.'''
    bl_idname = "mesh.primitive_sqorus_add"
    bl_label = "Add Sqorus"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    hole_size = FloatProperty(name="Hole Size",
        description="Size of the Hole",
        min=0.01,
        max=1.99,
        default=2.0 / 3.0)
    subdivide = BoolProperty(name="Subdivide Outside",
        description="Enable to subdivide the faces on the outside." \
            " This results in equally spaced vertices.",
        default=True)
    align_matrix = Matrix()

    def execute(self, context):
        props = self.properties

        # Create mesh geometry
        verts, faces = add_sqorus(
            props.hole_size,
            props.subdivide)

        # Create mesh object (and meshdata)
        obj = create_mesh_object(context, verts, [], faces, "Sqorus",
            props.edit, self.align_matrix)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "hole_size": props.hole_size,
            "subdivide": props.subdivide}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}

class AddWedge(bpy.types.Operator):
    '''Add a wedge mesh.'''
    bl_idname = "mesh.primitive_wedge_add"
    bl_label = "Add Wedge"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    size_x = FloatProperty(name="Size X",
        description="Size along the X axis",
        min=0.01,
        max=9999.0,
        default=2.0)
    size_y = FloatProperty(name="Size Y",
        description="Size along the Y axis",
        min=0.01,
        max=9999.0,
        default=2.0)
    size_z = FloatProperty(name="Size Z",
        description="Size along the Z axis",
        min=0.01,
        max=9999.0,
        default=2.00)
    align_matrix = Matrix()

    def execute(self, context):
        props = self.properties

        verts, faces = add_wedge(
            props.size_x,
            props.size_y,
            props.size_z)

        obj = create_mesh_object(context, verts, [], faces, "Wedge",
            props.edit, self.align_matrix)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "size_x": props.size_x,
            "size_y": props.size_y,
            "size_z": props.size_z}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}

class AddSpindle(bpy.types.Operator):
    '''Add a spindle mesh.'''
    bl_idname = "mesh.primitive_spindle_add"
    bl_label = "Add Spindle"
    bl_description = "Create a spindle mesh."
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    segments = IntProperty(name="Segments",
        description="Number of segments of the spindle",
        min=3,
        max=512,
        default=32)
    radius = FloatProperty(name="Radius",
        description="Radius of the spindle",
        min=0.01,
        max=9999.0,
        default=1.0)
    height = FloatProperty(name="Height",
        description="Height of the spindle",
        min=0.0,
        max=100.0,
        default=1.0)
    cap_height = FloatProperty(name="Cap Height",
        description="Cap height of the spindle",
        min=-9999.0,
        max=9999.0,
        default=0.5)
    align_matrix = Matrix()

    def execute(self, context):
        props = self.properties

        verts, faces = add_spindle(
            props.segments,
            props.radius,
            props.height,
            props.cap_height)

        obj = create_mesh_object(context, verts, [], faces, "Spindle",
            props.edit, self.align_matrix)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "segments": props.segments,
            "radius": props.radius,
            "height": props.height,
            "cap_height": props.cap_height}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}

class AddStar(bpy.types.Operator):
    '''Add a star mesh.'''
    bl_idname = "mesh.primitive_star_add"
    bl_label = "Add Star"
    bl_options = {'REGISTER', 'UNDO'}

    # edit - Whether to add or update.
    edit = BoolProperty(name="",
        description="",
        default=False,
        options={'HIDDEN'})
    points = IntProperty(name="Points",
        description="Number of points for the star",
        min=2,
        max=256,
        default=5)
    outer_radius = FloatProperty(name="Outer Radius",
        description="Outer radius of the star",
        min=0.01,
        max=9999.0,
        default=1.0)
    innter_radius = FloatProperty(name="Inner Radius",
        description="Inner radius of the star",
        min=0.01,
        max=9999.0,
        default=0.5)
    height = FloatProperty(name="Height",
        description="Height of the star",
        min=0.01,
        max=9999.0,
        default=0.5)
    align_matrix = Matrix()

    def execute(self, context):
        props = self.properties

        verts, faces = add_star(
            props.points,
            props.outer_radius,
            props.innter_radius,
            props.height)

        obj = create_mesh_object(context, verts, [], faces, "Star",
            props.edit, self.align_matrix)

        # Store 'recall' properties in the object.
        recall_args_list = {
            "edit": True,
            "points": props.points,
            "outer_radius": props.outer_radius,
            "innter_radius": props.innter_radius,
            "height": props.height}
        store_recall_properties(obj, self, recall_args_list)

        return {'FINISHED'}

    def invoke(self, context, event):
        self.align_matrix = align_matrix(context)
        self.execute(context)
        return {'FINISHED'}

class AddTrapezohedron(bpy.types.Operator):
    """Add a trapezohedron"""
    bl_idname = "mesh.primitive_trapezohedron_add"
    bl_label = "Add trapezohedron"
    bl_description = "Create one of the regular solids"
    bl_options = {'REGISTER', 'UNDO'}

    segments = IntProperty(name = "Segments",
                description = "Number of repeated segments",
                default = 4, min = 2, max = 256)
    radius = FloatProperty(name = "Base radius",
                description = "Radius of the middle",
                default = 1.0, min = 0.01, max = 100.0)
    height = FloatProperty(name = "Tip height",
                description = "Height of the tip",
                default = 1, min = 0.01, max = 100.0)
    edit = BoolProperty(name="",
                        description="",
                        default=False,
                        options={'HIDDEN'})
    align_matrix = Matrix()
    def execute(self,context):
        props = self.properties
        # generate mesh
        verts,faces = trapezohedron(props.segments,
                                    props.radius,
                                    props.height)
        
        obj = create_mesh_object(context, verts, [], faces, "Trapazohedron",
            props.edit, self.align_matrix)
        
        # store recall properties in object
        recall_args_list = {
                "edit": True,
                "segments" : props.segments,
                "radius" : props.radius,
                "height": props.height}
        store_recall_properties(obj,self,recall_args_list)

        return {'FINISHED'}

class INFO_MT_mesh_extras_add(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "INFO_MT_mesh_extras_add"
    bl_label = "Extras"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_sqorus_add",
            text="Sqorus")
        layout.operator("mesh.primitive_wedge_add",
            text="Wedge")
        layout.operator("mesh.primitive_spindle_add",
            text="Spindle")
        layout.operator("mesh.primitive_star_add",
            text="Star")
        layout.operator("mesh.primitive_trapezohedron_add",
            text="Trapezohedron")


# Register all operators and panels
import space_info

# Define "Gemstones" menu
menu_func = (lambda self,
    context: self.layout.menu("INFO_MT_mesh_extras_add", icon="PLUGIN"))


def register():
    # Register the operators/menus.
    bpy.types.register(AddSqorus)
    bpy.types.register(AddWedge)
    bpy.types.register(AddSpindle)
    bpy.types.register(AddStar)
    bpy.types.register(AddTrapezohedron)
    bpy.types.register(INFO_MT_mesh_extras_add)

    # Add "Gemstones" menu to the "Add Mesh" menu
    space_info.INFO_MT_mesh_add.append(menu_func)


def unregister():
    # Unregister the operators/menus.
    bpy.types.unregister(AddSqorus)
    bpy.types.unregister(AddWedge)
    bpy.types.unregister(AddSpindle)
    bpy.types.unregister(AddStar)
    bpy.types.unregister(AddTrapezohedron)
    bpy.types.unregister(INFO_MT_mesh_extras_add)

    # Remove "Gemstones" menu from the "Add Mesh" menu.
    space_info.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()
