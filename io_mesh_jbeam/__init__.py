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

# Script copyright (C) Thomas PORTASSAU (50thomatoes50)
# Contributors: Campbell Barton, Jiri Hnidek, Paolo Ciccone, Thomas Larsson, http://blender.stackexchange.com/users/185/adhi


# <pep8-80 compliant>

bl_info = {
    "name": "Export Jbeam (.jbeam)",
    "author": "Mike Baker (rmikebaker) & Thomas Portassau (50thomatoes50)",
    "location": "File > Import-Export",
    "version": (0, 1, 1),
    "wiki_url": 'http://wiki.beamng.com/Blender_Exporter_plugin',
    "tracker_url": "https://github.com/50thomatoes50/BlenderBeamNGExport/issues",
    "warning": "Under construction!",
    "description": "Export Nodes,Beams and Colision for BeamNG (.jbeam)",
    #"category": "Object"
    "category": "Import-Export"
    }

__version__ = '0.1.1'

#http://wiki.blender.org/index.php/Dev:2.5/Py/Scripts/Cookbook/Code_snippets/Multi-File_packages#init_.py
if "bpy" in locals():
    import imp
    if "export_jbeam" in locals():
        imp.reload(export_jbeam)
else:
    import bpy


import bpy
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )
from bpy_extras.io_utils import (ExportHelper,
                                 path_reference_mode,
                                 axis_conversion,
                                 )

class ExportJbeam(bpy.types.Operator):
    """Export Nodes and Beams to .jbeam file for BeamNG"""
    bl_idname = 'export_mesh.jbeam'
    bl_description = 'Export for use in BeamNG (.jbeam)'
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_label = 'Export Jbeam' + ' v.' + __version__
    
    # From ExportHelper. Filter filenames.
    filename_ext = ".jbeam"
    filter_glob = StringProperty(default="*.jbeam", options={'HIDDEN'})
 
    filepath = bpy.props.StringProperty(
        name="File Path", 
        description="File path used for exporting the jbeam file", 
        maxlen= 1024, default= "")
    
    listbn = bpy.props.BoolProperty(
        name = "Export has a list of beam and nodes",
        description="",
        default = False)
    
    exp_ef = bpy.props.BoolProperty(
        name = "Export edge from face",
        description="",
        default = True)
    
    exp_tricol = bpy.props.BoolProperty(
        name = "Export Faces to colision triangle",
        description="",
        default = True)
    
    exp_diag = bpy.props.BoolProperty(
        name = "Edge on quad face",
        description="",
        default = True)

    # execute() is called by blender when running the exporter.
    def execute(self, context):
        from . import export_jbeam
        export_jbeam.execute(
            self.properties.filepath, 
            context, 
            self.listbn, self.exp_ef, self.exp_tricol, self.exp_diag, )
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    
class BeamGen(bpy.types.Operator):
    bl_idname = 'object.beamgen'
    bl_description = 'beamGen'  + ' v.' + __version__
    bl_label = 'beam(edge) generator'

    # execute() is called by blender when running the operator.
    def execute(self, context):
        print("started")

        # Save currently active object
        #active = context.active_object
        active = context.edit_object
        if active is None: 
            self.report({'WARNING'}, 'WARNING : Not in edit mode! Operation cancelled!')
            print('CANCELLLED: Not in edit mode')
            return {'CANCELLED'}
            
        print("obj:"+active.name)
        nodes = []
        edge_tmp = []
        
        bpy.ops.object.mode_set(mode='OBJECT') 
        
        for v in active.data.vertices:
            if v.select:
                nodes.append(v.index)
        
        nb_point = len(nodes)
        print("nb_point:"+str(nb_point))
        if nb_point <= 1:
            self.report({'ERROR'}, 'ERROR: Select more than 1 point' )
        
        
        origin = len(active.data.edges)-1
        i = 0
        nb_edge = 0
        j = nb_point
        while(j!=0):
            j -= 1
            nb_edge += (nb_point-(nb_point-j))
        active.data.edges.add( nb_edge )
        
        for n1 in nodes:
            for n2 in nodes:
                if n1 != n2 and n2 > n1 :
                    i += 1
                    active.data.edges[origin+i].vertices[0] = n1
                    active.data.edges[origin+i].vertices[1] = n2
        
        bpy.ops.object.mode_set(mode='EDIT')
            

        
        # this lets blender know the operator finished successfully.
        return {'FINISHED'}

def menu_func_export(self, context):
    self.layout.operator(ExportJbeam.bl_idname, text='Export Jbeam v.' + __version__ + ' (.jbeam)')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    #bpy.utils.register_class(BeamGen)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    #bpy.utils.unregister_class(BeamGen)

# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
