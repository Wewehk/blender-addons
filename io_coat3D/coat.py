# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

import bpy
from bpy.props import *
from io_coat3D import tex
import os


bpy.coat3D = dict()
bpy.coat3D['active_coat'] = ''
bpy.coat3D['status'] = 0

def set_folders():
    platform = os.sys.platform
    coat3D = bpy.context.scene.coat3D
    if(platform == 'win32'):
        folder_objects = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Objects'
        folder_textures = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Textures' + os.sep
        if(not(os.path.isdir(folder_objects))):
            os.makedirs(folder_objects)
        if(not(os.path.isdir(folder_textures))):
            os.makedirs(folder_textures)
        exchange = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3D-CoatV3' + os.sep +'Exchange'
       
    else:
        folder_objects = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Objects'
        folder_textures = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Textures' + os.sep
        if(not(os.path.isdir(folder_objects))):
            os.makedirs(folder_objects)
        if(not(os.path.isdir(folder_textures))):
            os.makedirs(folder_textures)
        exchange = os.path.expanduser("~") + os.sep + '3D-CoatV3' + os.sep +'Exchange'
    if(os.path.isdir(exchange)):
        coat3D.exchange_found = True
    else:
        if(platform == 'win32'):
            exchange_path = os.path.expanduser("~") + os.sep + 'Documents' + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        else:
            exchange_path = os.path.expanduser("~") + os.sep + '3DC2Blender' + os.sep + 'Exchange_folder.txt'
        if(os.path.isfile(exchange_path)):
            ex_path =''

            ex_pathh = open(exchange_path)
            for line in ex_pathh:
                ex_path = line
                break
            ex_pathh.close()

            if(os.path.isdir(ex_path) and ex_path.rfind('Exchange') >= 0):
                exchange = ex_path
                coat3D.exchange_found = True
            else:
                coat3D.exchange_found = False
        else:
            coat3D.exchange_found = False
            
                
    return exchange,folder_objects,folder_textures

class ObjectButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

class SCENE_PT_Main(ObjectButtonsPanel,bpy.types.Panel):
    bl_label = "3D-Coat Applink"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        me = context.scene.objects
        mat_list = []
        import_no = 0
        coat = bpy.coat3D
        coat3D = bpy.context.scene.coat3D
        Blender_export = ""
        if(bpy.context.scene.objects.active):
            coa = bpy.context.scene.objects.active.coat3D
        
        if(os.path.isdir(coat3D.exchangedir)):
            foldder = coat3D.exchangedir
            if(foldder.rfind('Exchange') >= 0):
                coat['status'] = 1
            else:
                coat['status'] = 0
        else:
            coat['status'] = 0

        if(coat['status'] == 1):
            Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
            Blender_export = Blender_folder
            path3b_now = coat3D.exchangedir
            path3b_now += ('last_saved_3b_file.txt')
            Blender_export += ('%sexport.txt'%(os.sep))

            if(not(os.path.isdir(Blender_folder))):
                os.makedirs(Blender_folder)
                Blender_folder = os.path.join(Blender_folder,"run.txt")
                file = open(Blender_folder, "w")
                file.close()
        
        #Here you add your GUI 
        row = layout.row()
        row.prop(coat3D,"type",text = "")
        row = layout.row()
        if(context.selected_objects):
            for selected in context.selected_objects:
                if(selected.type == 'MESH'):
                    row.active = True
                    break
                else:
                    row.active = False
        else:
            row.active = False

      

        
        colL = row.column()
        colR = row.column()
    
        colR.operator("export_applink.pilgway_3d_coat", text="Transfer")
           
        colL.operator("import_applink.pilgway_3d_coat", text="Update")

        if(os.path.isfile(Blender_export)):
            row = layout.row()
            row.operator("import3b_applink.pilgway_3d_coat", text="Bring from 3D-Coat")

        if(coat3D.exchange_found == False):
            row = layout.row()
            row.label(text="Applink didn't find your 3d-Coat/Excahnge folder.")
            row = layout.row()
            row.label("Please select it and press Transfer button again")
            row = layout.row()
            row.prop(coat3D,"exchangefolder",text="")

                    
            
            
              



class SCENE_OT_export(bpy.types.Operator):
    bl_idname = "export_applink.pilgway_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        checkname = ''
        coat3D = bpy.context.scene.coat3D
        scene = context.scene
        activeobj = bpy.context.active_object.name
        obj = scene.objects[activeobj]
        coa = bpy.context.scene.objects.active.coat3D

        coat3D.exchangedir,folder_objects,folder_textures = set_folders()

        if(coat3D.exchange_found == False):
            return {'FINISHED'}

        importfile = coat3D.exchangedir
        texturefile = coat3D.exchangedir
        importfile += ('%simport.txt'%(os.sep))
        texturefile += ('%stextures.txt'%(os.sep))

        looking = True
        object_index = 0
        if(coa.applink_name and os.path.isfile(coa.applink_name)):
            checkname = coa.applink_name
           
        else:
            while(looking == True):
                checkname = folder_objects + os.sep + activeobj
                checkname = ("%s%.2d.obj"%(checkname,object_index))
                if(os.path.isfile(checkname)):
                    object_index += 1
                else:
                    looking = False
                    coa.applink_name = checkname

        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

        coa.loc = obj.location
        coa.rot = obj.rotation_euler
        coa.sca = obj.scale
        coa.dime = obj.dimensions

        

        obj.location = (0,0,0)
        obj.rotation_euler = (0,0,0)
        obj.scale = (1,1,1)

        bpy.ops.export_scene.obj(filepath=coa.applink_name,use_selection=True,
        use_apply_modifiers=False,use_blen_objects=True, group_by_material= True,
        use_materials = False,keep_vertex_order = True,axis_forward='X',axis_up='Y')
        

        obj.location = coa.loc
        obj.rotation_euler = coa.rot
        obj.scale = coa.sca
        
        file = open(importfile, "w")
        file.write("%s"%(checkname))
        file.write("\n%s"%(checkname))
        file.write("\n[%s]"%(coat3D.type))
        file.write("\n[TexOutput:%s]"%(folder_textures))
        file.close()

        coa.objecttime = str(os.path.getmtime(coa.applink_name))
               
        return {'FINISHED'}

class SCENE_OT_import(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_coat"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}
    
    def invoke(self, context, event):
        scene = context.scene
        coat3D = bpy.context.scene.coat3D
        coat = bpy.coat3D
        test = bpy.context.selected_objects
        act_first = bpy.context.scene.objects.active

        for act_name in test:
            coa = act_name.coat3D
            path_object = coa.applink_name
            print(path_object)
            if act_name.type == 'MESH' and os.path.isfile(path_object):
                multires_on = False
                activeobj = act_name.name
                mat_list = []
                scene.objects[activeobj].select = True
                objekti = scene.objects[activeobj]
                coat3D.loca = objekti.location
                coat3D.rota = objekti.rotation_euler
                coat3D.dime = objekti.scale
                

                
                #See if there is multres modifier. 
                for modifiers in objekti.modifiers:
                    if modifiers.type == 'MULTIRES' and (modifiers.total_levels > 0):
                        if(not(coat3D.importlevel)):
                            bpy.ops.object.multires_external_pack()
                            multires = coat3D.exchangedir
                            multires += ('%stemp.btx'%(os.sep))
                            bpy.ops.object.multires_external_save(filepath=multires)
                            #bpy.ops.object.multires_external_pack()
                        multires_on = True
                        multires_name = modifiers.name
                        break
                        
                exportfile = coat3D.exchangedir
                path3b_n = coat3D.exchangedir
                path3b_n += ('last_saved_3b_file.txt')
                exportfile += ('%sexport.txt'%(os.sep))
                if(os.path.isfile(exportfile)):
                    export_file = open(exportfile)
                    for line in export_file:
                        if line.rfind('.3b'):
                            objekti.coat3D.coatpath = line
                            coat['active_coat'] = line
                    export_file.close()
                    os.remove(exportfile)

                if(len(objekti.material_slots) == 0):
                    delete_material = False
                else:
                    delete_material = True
                    
               
                if(not(objekti.active_material) and objekti.material_slots):
                    act_mat_index = objekti.active_material_index
                    materials_old = bpy.data.materials.keys()
                    bpy.ops.material.new()
                    materials_new = bpy.data.materials.keys()
                    new_ma = list(set(materials_new).difference(set(materials_old)))
                    new_mat = new_ma[0]
                    ki = bpy.data.materials[new_mat]
                    objekti.material_slots[act_mat_index].material = ki
                 

                 
                if(os.path.isfile(path_object) and (coa.objecttime != str(os.path.getmtime(path_object)))):

                    if(objekti.material_slots):
                        act_mat_index = objekti.active_material_index
                        for obj_mat in objekti.material_slots:
                            mat_list.append(obj_mat.material)
                            
                    coa.dime = objekti.dimensions
                    coa.objecttime = str(os.path.getmtime(path_object))
                    mtl = coa.applink_name
                    mtl = mtl.replace('.obj','.mtl')
                    if(os.path.isfile(mtl)):
                        os.remove(mtl)

                    
                    bpy.ops.import_scene.obj(filepath=path_object,axis_forward='X',axis_up='Y')
                    obj_proxy = scene.objects[0]
                    bpy.ops.object.select_all(action='TOGGLE')
                    obj_proxy.select = True
            
                        
                    bpy.ops.object.transform_apply(rotation=True)
                    proxy_mat = obj_proxy.material_slots[0].material
                    if(delete_material):
                        obj_proxy.data.materials.pop(0,1)
                        proxy_mat.user_clear()
                        bpy.data.materials.remove(proxy_mat)
                    bpy.ops.object.select_all(action='TOGGLE')

                    if(coat3D.importlevel):
                        obj_proxy.select = True
                        obj_proxy.modifiers.new(name='temp',type='MULTIRES')
                        objekti.select = True
                        bpy.ops.object.multires_reshape(modifier=multires_name)
                        bpy.ops.object.select_all(action='TOGGLE')
                        multires_on = False
                    else:
                    
                        scene.objects.active = obj_proxy
                    
                        obj_data = objekti.data.id_data
                        objekti.data = obj_proxy.data.id_data
                        if(bpy.data.meshes[obj_data.name].users == 0):
                            bpy.data.meshes.remove(obj_data)
                            objekti.data.id_data.name = obj_data.name

                    obj_proxy.select = True
                    bpy.ops.object.delete()
                    objekti.select = True
                    objekti.scale = coat3D.dime
                    bpy.context.scene.objects.active = objekti

                if(os.path.isfile(path3b_n)):
                    path3b_fil = open(path3b_n)
                    for lin in path3b_fil:
                        objekti.coat3D.path3b = lin
                    path3b_fil.close()
                    os.remove(path3b_n)
                        
                if(coat3D.importmesh and not(os.path.isfile(path_object))):
                    coat3D.importmesh = False

                if(mat_list and coat3D.importmesh):
                    for mat_one in mat_list:
                        objekti.data.materials.append(mat_one)
                    objekti.active_material_index = act_mat_index
                    
                if(mat_list):
                    for obj_mate in objekti.material_slots:
                        if(hasattr(obj_mate.material,'texture_slots')):
                            for tex_slot in obj_mate.material.texture_slots:
                                if(hasattr(tex_slot,'texture')):
                                    if(tex_slot.texture.type == 'IMAGE'):
                                        if tex_slot.texture.image is not None:
                                            tex_slot.texture.image.reload()
                                                                
                        
                if(coat3D.importtextures):
                    export = ''
                    tex.gettex(mat_list,objekti,scene,export)

                if(multires_on):
                    temp_file = coat3D.exchangedir
                    temp_file += ('%stemp2.btx'%(os.sep))
                    if(objekti.modifiers[multires_name].levels == 0):
                        objekti.modifiers[multires_name].levels = 1
                        bpy.ops.object.multires_external_save(filepath=temp_file)
                        objekti.modifiers[multires_name].filepath = multires
                        objekti.modifiers[multires_name].levels = 0

                    else:
                        bpy.ops.object.multires_external_save(filepath=temp_file)
                        objekti.modifiers[multires_name].filepath = multires
                    #bpy.ops.object.multires_external_pack()
                bpy.ops.object.shade_smooth()
                
              
        for act_name in test:
            act_name.select = True
        bpy.context.scene.objects.active = act_first

        return {'FINISHED'}

class SCENE_OT_import3b(bpy.types.Operator):
    bl_idname = "import3b_applink.pilgway_3d_coat"
    bl_label = "Brings mesh from 3D-Coat"
    bl_description = "Bring 3D-Coat Mesh"
    bl_options = {'UNDO'}

    def invoke(self, context, event):

        coat3D = bpy.context.scene.coat3D
        scene = context.scene
        
        Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
        Blender_export = Blender_folder
        path3b_now = coat3D.exchangedir
        path3b_now += ('last_saved_3b_file.txt')
        Blender_export += ('%sexport.txt'%(os.sep))

        import_no = 0
        mat_list = []
        obj_path =''

        obj_pathh = open(Blender_export)
        for line in obj_pathh:
            obj_path = line
            break
        obj_pathh.close()
        export = obj_path
        mod_time = os.path.getmtime(obj_path)
        mtl_list = obj_path.replace('.obj','.mtl')
        if(os.path.isfile(mtl_list)):
            os.remove(mtl_list)
            
        if(os.path.isfile(path3b_now)):
            path3b_file = open(path3b_now)
            for lin in path3b_file:
                path_export = lin
                path_on = 1
            path3b_file.close()
            os.remove(path3b_now)
        else:
            path_on = 0

        for palikka in bpy.context.scene.objects:
            if(palikka.type == 'MESH'):
                if(palikka.coat3D.objectdir == export): #objectdir muutettava
                    import_no = 1
                    target = palikka
                    break

        if(import_no):
            new_obj = palikka
            import_no = 0
        else:
            bpy.ops.import_scene.obj(filepath=obj_path,axis_forward='X',axis_up='Y')
            bpy.ops.object.transform_apply(rotation=True)
            new_obj = scene.objects[0]
            new_obj.coat3D.applink_name = obj_path
            scene.objects[0].coat3D.objectdir = export #objectdir muutettava
            if(path_on):
                scene.objects[0].coat3D.path3b = path_export
            
        os.remove(Blender_export)
        
        bpy.context.scene.objects.active = new_obj

        bpy.ops.object.shade_smooth()
       
        Blender_tex = ("%s%stextures.txt"%(coat3D.exchangedir,os.sep))
        mat_list.append(new_obj.material_slots[0].material)
        tex.gettex(mat_list, new_obj, scene,export)

        return {'FINISHED'}

class SCENE_OT_load3b(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_coat_3b"
    bl_label = "Loads 3b linked into object"
    bl_description = "Loads 3b linked into object"

    
    def invoke(self, context, event):
        checkname = ''
        coa = bpy.context.scene.objects.active.coat3D
        if(coa.path3b):
            coat3D = bpy.context.scene.coat3D
            scene = context.scene
            importfile = coat3D.exchangedir
            importfile += ('%simport.txt'%(os.sep))
            
            coat_path = bpy.context.active_object.coat3D.path3b
            
            file = open(importfile, "w")
            file.write("%s"%(coat_path))
            file.write("\n%s"%(coat_path))
            file.write("\n[3B]")
            file.close()

        return {'FINISHED'}

class SCENE_OT_deltex(bpy.types.Operator):
    bl_idname = "import_applink.pilgway_3d_deltex"  # XXX, name?
    bl_label = "Picks Object's name into path"
    bl_description = "Loads 3b linked into object"

    def invoke(self, context, event):
        if(bpy.context.selected_objects):
            if(context.selected_objects[0].type == 'MESH'):
                coat3D = bpy.context.scene.coat3D
                coa = bpy.context.scene.objects.active.coat3D
                scene = context.scene
                nimi = tex.objname(coa.objectdir)  #objectdir muutettava
                if(coa.texturefolder):
                    osoite = os.path.dirname(coa.texturefolder) + os.sep
                else:
                    osoite = os.path.dirname(coa.objectdir) + os.sep #objectdir muutettava
                just_nimi = tex.justname(nimi)
                just_nimi += '_'

                files = os.listdir(osoite)
                for i in files:
                    if(i.rfind(just_nimi) >= 0):
                        del_osoite = osoite + i
                        os.remove(del_osoite)
    
        return {'FINISHED'}

from bpy import *
from mathutils import Vector, Matrix

# 3D-Coat Dynamic Menu
class VIEW3D_MT_Coat_Dynamic_Menu(bpy.types.Menu):
    bl_label = "3D-Coat Applink Menu"

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'
        coat3D = bpy.context.scene.coat3D
        Blender_folder = ("%s%sBlender"%(coat3D.exchangedir,os.sep))
        Blender_export = Blender_folder
        Blender_export += ('%sexport.txt'%(os.sep))

        ob = context
        if ob.mode == 'OBJECT':
            if(bpy.context.selected_objects):
                for ind_obj in bpy.context.selected_objects:
                    if(ind_obj.type == 'MESH'):
                        layout.active = True
                        break
                    layout.active = False

                if(layout.active == True):

                    layout.operator("import_applink.pilgway_3d_coat", text="Import")
                    layout.separator()

                    layout.operator("export_applink.pilgway_3d_coat", text="Export")
                    layout.separator()

                    layout.menu("VIEW3D_MT_ImportMenu")
                    layout.separator()

                    layout.menu("VIEW3D_MT_ExportMenu")
                    layout.separator()

                    layout.menu("VIEW3D_MT_ExtraMenu")
                    layout.separator()

                    if(len(bpy.context.selected_objects) == 1):
                        if(os.path.isfile(bpy.context.selected_objects[0].coat3D.path3b)):
                            layout.operator("import_applink.pilgway_3d_coat_3b", text="Load 3b")
                            layout.separator()

                    if(os.path.isfile(Blender_export)):

                        layout.operator("import3b_applink.pilgway_3d_coat", text="Bring from 3D-Coat")
                        layout.separator()
                else:
                    if(os.path.isfile(Blender_export)):
                        layout.active = True

                        layout.operator("import3b_applink.pilgway_3d_coat", text="Bring from 3D-Coat")
                        layout.separator()
            else:
                 if(os.path.isfile(Blender_export)):
                    

                    layout.operator("import3b_applink.pilgway_3d_coat", text="Bring from 3D-Coat")
                    layout.separator()
                
class VIEW3D_MT_ImportMenu(bpy.types.Menu):
    bl_label = "Import Settings"

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.prop(coat3D,"importmesh")
        layout.prop(coat3D,"importmod")
        layout.prop(coat3D,"smooth_on")
        layout.prop(coat3D,"importtextures")
        
class VIEW3D_MT_ExportMenu(bpy.types.Menu):
    bl_label = "Export Settings"

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.prop(coat3D,"exportover")
        if(coat3D.exportover):
           layout.prop(coat3D,"exportmod")

class VIEW3D_MT_ExtraMenu(bpy.types.Menu):
    bl_label = "Extra"

    def draw(self, context):
        layout = self.layout
        coat3D = bpy.context.scene.coat3D
        settings = context.tool_settings
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("import_applink.pilgway_3d_deltex",text="Delete all Textures")
        layout.separator()

def register():
    bpy.utils.register_module(__name__)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('wm.call_menu2', 'Q', 'PRESS')
    kmi.properties.name = "VIEW3D_MT_Coat_Dynamic_Menu"

def unregister():
    bpy.utils.unregister_module(__name__)

    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == '':
            if kmi.properties.name == "VIEW3D_MT_Coat_Dynamic_Menu":
                km.keymap_items.remove(kmi)
                break


if __name__ == "__main__":
    register()
