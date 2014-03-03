

bl_info = {
    "name": "Export Jbeam (.jbeam)",
    "author": "Mike Baker (rmikebaker) & Thomas Portassau (50thomatoes50)",
    "location": "File > Import-Export",
    "version": (0, 0, 1),
    "wiki_url": 'http://www.beamng.com/threads/5775-Blender-Script-to-Export-Nodes-and-Beams',
    "tracker_url": "https://github.com/rmikebaker/BlenderBeamNGExport/issues",
    "warning": "Under construction!",
    "description": "Export Nodes and Beams for BeamNG (.jbeam)",
    #"category": "Object"
    "category": "Import-Export"
    }

__version__ = '0.0.1'


import os
import struct

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

class NGnode(object):
    def __init__(self, i, nodeName, x, y, z):
        self.i = i
        self.nodeName = nodeName
        self.x = x
        self.y = y
        self.z = z


class ExportJbeam(bpy.types.Operator):
    """Export Nodes and Beams to .jbeam file for BeamNG"""
    bl_idname = 'object.export_jbeam'
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
    
    use_filepath = bpy.props.BoolProperty(
        name = "Use filepath defined when exported, else use the blender file location",
        description="",
        default = True)
    
    listbn = bpy.props.BoolProperty(
        name = "Export has a list of beam and nodes",
        description="",
        default = True)
    
    exp_ef = bpy.props.BoolProperty(
        name = "Export edge from face",
        description="",
        default = True)
    
    exp_tricol = bpy.props.BoolProperty(
        name = "Export Faces to colision triangle",
        description="",
        default = True)

    # execute() is called by blender when running the operator.
    def execute(self, context):

        file = None
        
        # Need path for saving data to file
        if not(self.use_filepath):
            self.filepath = bpy.path.abspath('//')
            if self.filepath == '':
                self.report({'ERROR'}, "You must save your objects to a .blend file first")        
                return {'FINISHED'}
                                               
        scene = context.scene

        # Save currently active object
        active = context.active_object

        selectedObjects = []
        for o in context.selected_objects:
            if (o.type == 'MESH'):
                o.select = False
                selectedObjects.append(o)
        
        try:
            for objsel in selectedObjects:
                # Make the active object be the selected one
                scene.objects.active = objsel
    
                # Want to be in Object mode
                bpy.ops.object.mode_set(mode='OBJECT')
    
                # Prefix for node names
                try:
                    nodePrefix = objsel['JbeamNodePrefix']
                except:
                    nodePrefix = 'n'
                    
                #-------------------------------------
                # Create a copy of the selected object
                #-------------------------------------
                
                tempName = objsel.name + '.JBEAM_TEMP'
                 
                # Create new mesh
                tempMesh = bpy.data.meshes.new(tempName)
             
                # Create new object associated with the mesh
                ob_new = bpy.data.objects.new(tempName, tempMesh)
             
                # Copy data block from the old object into the new object
                ob_new.data = objsel.data.copy()
                ob_new.scale = objsel.scale
                ob_new.location = objsel.location
                ob_new.rotation_axis_angle = objsel.rotation_axis_angle
                ob_new.rotation_euler = objsel.rotation_euler
                ob_new.rotation_mode = objsel.rotation_mode
                ob_new.rotation_quaternion = objsel.rotation_quaternion
                
                # Link new object to the given scene, select it, and
                # make it active
                scene.objects.link(ob_new)
                ob_new.select = True
                scene.objects.active = ob_new
             
                # Apply transforms
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
                # TODO: Can we copy modifiers from original object and then do this?
                #mesh = ob_new.to_mesh(scene, True, 'PREVIEW')
                
                # Sort vertices
                mesh = ob_new.data
                nodes = []
                for v in mesh.vertices:
                    node = NGnode(v.index,
                                  nodePrefix,
                                  round(v.co[0] + objsel.delta_location[0], 3),
                                  round(v.co[1] + objsel.delta_location[1], 3),
                                  round(v.co[2] + objsel.delta_location[2], 3))
                    nodes.append(node)
    
                sortedz = sorted(nodes, key=lambda NGnode: NGnode.z)
                #sortedz is nodes sorted by Z axis
                sortedx = sorted(sortedz, key=lambda NGnode: NGnode.x, reverse=True)
                #sortedx is sortedz sorted by -X axis 
                sortedNodes = sorted(sortedx, key=lambda NGnode: NGnode.y)
                #sortedNodes is sortedx sorted by Yaxis
                #sortedNodes is nodes sorted by Z axis then -X axis then Y axis?
                    
                # Export
                anewline = '\n'
                filename = objsel.name + '.jbeam'
                file = open(self.filepath + '/' + filename, 'wt')
                if not(self.listbn):
                    file.write('{\n\t"%s":{\n\t\t"information":{\n\t\t\t"name":"%s",\n\t\t\t"authors":"%s"},\n\t\t"slotType":"main",\n' % (objsel.name,objsel.name,self.bl_label))
                mesh.update(True, True)  #http://www.blender.org/documentation/blender_python_api_2_69_7/bpy.types.Mesh.html?highlight=update#bpy.types.Mesh.update

                i = 0
                file.write('//--Nodes--')
                file.write(anewline)
                if not(self.listbn):
                    file.write('\t\t"nodes":[\n\t\t\t["id", "posX", "posY", "posZ"],\n')
                for v in sortedNodes:
                    if self.listbn:
                        file.write('[\"')
                    else:
                        file.write('\t\t\t[\"')
                    if v.x > 0:
                        v.nodeName = v.nodeName + 'l' + ('%s' % (i))
                    elif v.x < 0:
                        v.nodeName = v.nodeName + 'r' + ('%s' % (i))
                    else:
                        v.nodeName = v.nodeName + ('%s' % (i))
                    file.write(v.nodeName)
                    file.write('\",')
                    file.write('%s' % (round(v.x + objsel.delta_location[0], 3))) 
                    file.write(',') 
                    file.write('%s' % (round(v.y + objsel.delta_location[1], 3)))
                    file.write(',')
                    file.write('%s' % (round(v.z + objsel.delta_location[2], 3)))
                    file.write('],')
                    file.write(anewline)
                    i += 1
                if not(self.listbn):
                    file.write('\t\t\t],\n')
                
                
                file.write('//--Beams--')
                file.write(anewline)
                if not(self.listbn):
                    file.write('\t\t"beams":[\n\t\t\t["id1:", "id2:"],\n')
                for e in mesh.edges:
                    nodeIndex1 = ([n.i for n in sortedNodes].index(e.vertices[0]))
                    file.write('[\"%s\"' % (sortedNodes[nodeIndex1].nodeName)) 
                    file.write(',') 
                    nodeIndex2 = ([n.i for n in sortedNodes].index(e.vertices[1]))
                    file.write('\"%s\"' % (sortedNodes[nodeIndex2].nodeName))
                    file.write('],')
                    file.write(anewline)
                    
                if self.exp_ef:
                    for f in mesh.tessfaces:
                        vs = f.vertices
                        if len(vs) == 3:
                            nodeIndex1 = ([n.i for n in sortedNodes].index(vs[0]))
                            nodeIndex2 = ([n.i for n in sortedNodes].index(vs[1]))
                            nodeIndex3 = ([n.i for n in sortedNodes].index(vs[2]))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex1].nodeName, sortedNodes[nodeIndex2].nodeName))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex2].nodeName, sortedNodes[nodeIndex3].nodeName))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex3].nodeName, sortedNodes[nodeIndex1].nodeName))
                        elif len(vs) == 4:
                            nodeIndex1 = ([n.i for n in sortedNodes].index(vs[0]))
                            nodeIndex2 = ([n.i for n in sortedNodes].index(vs[1]))
                            nodeIndex3 = ([n.i for n in sortedNodes].index(vs[2]))
                            nodeIndex4 = ([n.i for n in sortedNodes].index(vs[3]))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex1].nodeName, sortedNodes[nodeIndex2].nodeName))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex2].nodeName, sortedNodes[nodeIndex3].nodeName))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex3].nodeName, sortedNodes[nodeIndex4].nodeName))
                            file.write('["%s","%s"],\n' % (sortedNodes[nodeIndex4].nodeName, sortedNodes[nodeIndex1].nodeName))
                        else:
                            self.report({'ERROR'}, 'ERROR: Face %i isn\'t tri or quad.' % vs.index)
                if not(self.listbn):
                    file.write('\t\t\t],\n')
                
                if self.exp_tricol:
                    file.write('//--tri col--')
                    file.write(anewline)
                    ob_new.modifiers.new("tricol","TRIANGULATE")
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="tricol")
                    if not(self.listbn):
                        file.write('\t\t"triangles":[\n\t\t\t["id1:", "id2:", "id3:"],\n')
                    mesh = ob_new.data
                    mesh.update(False, True)
                    for f in mesh.tessfaces:
                        vs = f.vertices
                        if len(vs) == 3:
                            nodeIndex1 = ([n.i for n in sortedNodes].index(vs[0]))
                            nodeIndex2 = ([n.i for n in sortedNodes].index(vs[1]))
                            nodeIndex3 = ([n.i for n in sortedNodes].index(vs[2]))
                            file.write('["%s","%s","%s"],\n' % (sortedNodes[nodeIndex1].nodeName, sortedNodes[nodeIndex2].nodeName, sortedNodes[nodeIndex3].nodeName))
                        else:
                             self.report({'ERROR'}, 'ERROR: TriCol %i isn\'t tri' % vs.index)
                    if not(self.listbn):
                        file.write('\t\t\t],\n')
                if not(self.listbn):
                    file.write('\t}\n}')
                file.flush()
                file.close()
    
                # Deselect our new object
                ob_new.select = False
                
                # Remove the new temp object
                scene.objects.unlink(ob_new)
                bpy.data.objects.remove(ob_new)
                
                if (mesh.users == 0):
                    mesh.user_clear()
                    
                bpy.data.meshes.remove(mesh)
                
                if (tempMesh.users == 0):
                    tempMesh.user_clear()
                    
                bpy.data.meshes.remove(tempMesh)
            
            # Restore selection status
            for o in selectedObjects:
                o.select = True
                    
            # Restore active object
            scene.objects.active = active
            
        except Exception as e:
            self.report({'ERROR'}, 'ERROR: ' + str(e))
            if file: file.close()
        
        # this lets blender know the operator finished successfully.
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func_export(self, context):
    self.layout.operator(ExportJbeam.bl_idname, text='Export Jbeam v.' + __version__ + ' (.jbeam)')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
