import os
import struct
import bpy
from bpy import ops
from bpy.props import (BoolProperty,
                       FloatProperty,
                       StringProperty,
                       EnumProperty,
                       )

from .tools import *


class NGnode(object):
    def __init__(self, i, node_name, x, y, z):
        self.i = i
        self.node_name = node_name
        self.x = x
        self.y = y
        self.z = z


class ExportJbeam(bpy.types.Operator):
    bl_idname = 'export_mesh.jbeam'
    bl_description = 'Export for use in BeamNG.drive (.jbeam)'
    # bl_space_type = "PROPERTIES"
    # bl_region_type = "WINDOW"
    bl_label = 'Export JBeam' + ' v.' + PrintVer()

    # From ExportHelper. Filter filenames.
    filename_ext = ".jbeam"
    filter_glob: StringProperty(default="*.jbeam", options={'HIDDEN'})

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting the JBeam file",
        maxlen=1024, default="")

    listbn: bpy.props.BoolProperty(
        name="Export has a list of beam and nodes",
        description="",
        default=False)

    exp_ef: bpy.props.BoolProperty(
        name="Export edge from face",
        description="",
        default=True)

    exp_tricol: bpy.props.BoolProperty(
        name="Export Faces to colision triangle",
        description="",
        default=True)

    exp_diag: bpy.props.BoolProperty(
        name="Edge on quad face",
        description="",
        default=True)

    export_scene: bpy.props.BoolProperty(
        name="scene_export",
        description="exporter_prop_scene_tip",
        default=False,
        options={'HIDDEN'})

    def invoke(self, context, event):
        # context.window_manager.fileselect_add(self)
        # return {'RUNNING_MODAL'}
        ops.wm.call_menu(name="IO_mesh_jbeam_ExporterChoice")
        return {'PASS_THROUGH'}

    def execute(self, context, ):
        import sys
        jbeam_file = None

        scene = context.collection

        # Save currently active object
        active_object = context.active_object

        export_objects = []
        if self.export_scene:
            for obj in bpy.context.selectable_objects:
                if obj.type == 'MESH':
                    if '.jbeam' in obj.name:
                        export_objects.append(obj)

        else:
            for selected_object in context.selected_objects:
                if selected_object.type == 'MESH':
                    # selected_object.select = False
                    export_objects.append(selected_object)
        if len(export_objects) == 0:
            '''self.report({'WARNING'}, 'WARNING : Must be select objects to export')
            print('CANCELLED: Must be select objects to export')'''
            return {'CANCELLED'}

        temp_mesh = None
        ob_new = None
        try:
            for objsel in export_objects:
                # Make the active object be the selected one
                bpy.context.view_layer.objects.active = objsel
                print(objsel.data.jbeam)
                # Want to be in Object mode
                bpy.ops.object.mode_set(mode='OBJECT')

                # -------------------------------------
                # Create a copy of the selected object
                # -------------------------------------

                temp_name = objsel.name + '.JBEAM_TEMP'

                # Create new mesh
                temp_mesh = bpy.data.meshes.new(temp_name)

                # Create new object associated with the mesh
                ob_new = bpy.data.objects.new(temp_name, temp_mesh)

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
                ob_new.select_set(True)
                bpy.context.view_layer.objects.active = ob_new

                # Apply transforms
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                # TODO: Can we copy modifiers from original object and then do this?
                # mesh = ob_new.to_mesh(scene, True, 'PREVIEW')

                # Sort vertices
                mesh = ob_new.data
                nodes = []
                for vertex in mesh.vertices:
                    node = NGnode(vertex.index,
                                  objsel.data.jbeam.nodename,
                                  round(vertex.co[0] + objsel.delta_location[0], 3),
                                  round(vertex.co[1] + objsel.delta_location[1], 3),
                                  round(vertex.co[2] + objsel.delta_location[2], 3))
                    nodes.append(node)

                sorted_z = sorted(nodes, key=lambda NGnode: NGnode.z)
                # sorted_z is nodes sorted by Z axis
                sorted_x = sorted(sorted_z, key=lambda NGnode: NGnode.x, reverse=True)
                # sorted_x is sorted_z sorted by -X axis
                sorted_nodes = sorted(sorted_x, key=lambda NGnode: NGnode.y)
                # sorted_nodes is sorted_x sorted by Yaxis
                # sorted_nodes is nodes sorted by Z axis then -X axis then Y axis?

                # Export
                new_line = '\n'
                # filename = objsel.name + '.jbeam'
                if '.jbeam' in objsel.name:
                    filename = objsel.name
                else:
                    filename = objsel.name + '.jbeam'
                print("File = " + str(self.filepath) + filename)

                if self.filepath == "":
                    if context.scene.jbeam.export_path == "":
                        self.report({'WARNING'},
                                    'WARNING : No export folder set. Go to Scene > JBeam Exporter. Export cancelled!')
                        if ob_new:
                            scene.objects.unlink(ob_new)
                            bpy.data.objects.remove(ob_new)
                        return {'CANCELLED'}
                    if context.scene.jbeam.export_path.startswith("//") and not context.blend_data.filepath:
                        if ob_new:
                            scene.objects.unlink(ob_new)
                            bpy.data.objects.remove(ob_new)
                        self.report({'ERROR'}, "Save the .blend file first")
                        return {'CANCELLED'}
                    self.filepath = bpy.path.abspath(context.scene.jbeam.export_path)

                if not context.scene.jbeam.export_path.startswith("//"):
                    if not (os.path.isdir(self.filepath)):
                        if ob_new:
                            scene.objects.unlink(ob_new)
                            bpy.data.objects.remove(ob_new)
                        self.report({'WARNING'}, 'WARNING : Must be exported in a directory. Export cancelled!')
                        print('CANCELLLED: Must be exported in a directory. drectory = "' + self.filepath + '"')
                        return {'CANCELLED'}
                jbeam_file = open(self.filepath + filename, 'wt')
                # file = open(self.filepath + '/' + filename, 'wt')

                if not context.scene.jbeam.listbn:
                    # if(bpy.context.preferences.filepaths.author == "" and False):
                    author = 'Blender JBeam' + ' v' + PrintVer()
                    # else:
                    # author = bpy.context.preferences.filepaths.author + "," + 'Blender Jbeam' + ' v' + PrintVer()
                    if '.jbeam' in objsel.name:
                        name = objsel.name[0:len(objsel.name) - 6]
                    else:
                        name = objsel.name
                    jbeam_file.write(
                        '{\n\t"%s":{\n\t\t"information":{\n\t\t\t"name":"%s",\n\t\t\t"authors":"%s"},\n\t\t"slotType":"%s",\n' % (
                            name, objsel.data.jbeam.name, author, objsel.data.jbeam.slot))
                mesh.update(calc_edges=True, calc_loop_triangles=True)

                i = 0
                jbeam_file.write('//--Nodes--')
                jbeam_file.write(new_line)
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t\t"nodes":[\n\t\t\t["id", "posX", "posY", "posZ"],\n')
                for vertex in sorted_nodes:
                    if context.scene.jbeam.listbn:
                        jbeam_file.write('[\"')
                    else:
                        jbeam_file.write('\t\t\t[\"')
                    if vertex.x > 0:
                        vertex.node_name = vertex.node_name + 'l' + ('%s' % i)
                    elif vertex.x < 0:
                        vertex.node_name = vertex.node_name + 'r' + ('%s' % i)
                    else:
                        vertex.node_name = vertex.node_name + ('%s' % i)
                    jbeam_file.write(vertex.node_name)
                    jbeam_file.write('\",')
                    jbeam_file.write('%s' % (round(vertex.x + objsel.delta_location[0], 3)))
                    jbeam_file.write(',')
                    jbeam_file.write('%s' % (round(vertex.y + objsel.delta_location[1], 3)))
                    jbeam_file.write(',')
                    jbeam_file.write('%s' % (round(vertex.z + objsel.delta_location[2], 3)))
                    jbeam_file.write('],')
                    jbeam_file.write(new_line)
                    i += 1
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t\t\t],\n')

                jbeam_file.write('//--Beams--')
                jbeam_file.write(new_line)
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t\t"beams":[\n\t\t\t["id1:", "id2:"],\n')
                for e in mesh.edges:
                    if context.scene.jbeam.listbn:
                        jbeam_file.write('[\"')
                    else:
                        jbeam_file.write('\t\t\t[\"')
                    node_index1 = ([n.i for n in sorted_nodes].index(e.vertices[0]))
                    jbeam_file.write('%s\"' % sorted_nodes[node_index1].node_name)
                    jbeam_file.write(',')
                    node_index2 = ([n.i for n in sorted_nodes].index(e.vertices[1]))
                    jbeam_file.write('\"%s\"' % sorted_nodes[node_index2].node_name)
                    jbeam_file.write('],')
                    jbeam_file.write(new_line)

                if context.scene.jbeam.exp_ef:
                    for f in mesh.polygons:
                        vs = f.vertices
                        if len(vs) == 3:
                            node_index1 = ([n.i for n in sorted_nodes].index(vs[0]))
                            node_index2 = ([n.i for n in sorted_nodes].index(vs[1]))
                            node_index3 = ([n.i for n in sorted_nodes].index(vs[2]))
                            if context.scene.jbeam.listbn:
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index1].node_name, sorted_nodes[node_index2].node_name))
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index2].node_name, sorted_nodes[node_index3].node_name))
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index3].node_name, sorted_nodes[node_index1].node_name))
                            else:
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index1].node_name, sorted_nodes[node_index2].node_name))
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index2].node_name, sorted_nodes[node_index3].node_name))
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index3].node_name, sorted_nodes[node_index1].node_name))
                        elif len(vs) == 4:
                            node_index1 = ([n.i for n in sorted_nodes].index(vs[0]))
                            node_index2 = ([n.i for n in sorted_nodes].index(vs[1]))
                            node_index3 = ([n.i for n in sorted_nodes].index(vs[2]))
                            node_index4 = ([n.i for n in sorted_nodes].index(vs[3]))
                            if context.scene.jbeam.listbn:
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index1].node_name, sorted_nodes[node_index2].node_name))
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index2].node_name, sorted_nodes[node_index3].node_name))
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index3].node_name, sorted_nodes[node_index4].node_name))
                                jbeam_file.write('["%s","%s"],\n' % (
                                    sorted_nodes[node_index4].node_name, sorted_nodes[node_index1].node_name))
                            else:
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index1].node_name, sorted_nodes[node_index2].node_name))
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index2].node_name, sorted_nodes[node_index3].node_name))
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index3].node_name, sorted_nodes[node_index4].node_name))
                                jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                    sorted_nodes[node_index4].node_name, sorted_nodes[node_index1].node_name))
                            if context.scene.jbeam.exp_diag:
                                if self.listbn:
                                    jbeam_file.write('["%s","%s"],\n' % (
                                        sorted_nodes[node_index1].node_name, sorted_nodes[node_index3].node_name))
                                    jbeam_file.write('["%s","%s"],\n' % (
                                        sorted_nodes[node_index2].node_name, sorted_nodes[node_index4].node_name))
                                else:
                                    jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                        sorted_nodes[node_index1].node_name, sorted_nodes[node_index3].node_name))
                                    jbeam_file.write('\t\t\t["%s","%s"],\n' % (
                                        sorted_nodes[node_index2].node_name, sorted_nodes[node_index4].node_name))
                        else:
                            report({'ERROR'}, 'ERROR: Face %i isn\'t tri or quad.' % vs.index)
                            if jbeam_file: jbeam_file.close()
                            if ob_new:
                                scene.objects.unlink(ob_new)
                                bpy.data.objects.remove(ob_new)
                            return {'CANCELLED'}
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t\t\t],\n')

                if context.scene.jbeam.exp_tricol:
                    jbeam_file.write('//--Collision Triangles--')
                    jbeam_file.write(new_line)
                    ob_new.modifiers.new("tricol", "TRIANGULATE")
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="tricol")
                    if not context.scene.jbeam.listbn:
                        jbeam_file.write('\t\t"triangles":[\n\t\t\t["id1:", "id2:", "id3:"],\n')
                    mesh = ob_new.data
                    mesh.update(calc_edges=True, calc_loop_triangles=True)
                    for f in mesh.polygons:
                        vs = f.vertices
                        if len(vs) == 3:
                            if not context.scene.jbeam.listbn:
                                jbeam_file.write('\t\t\t')
                            node_index1 = ([n.i for n in sorted_nodes].index(vs[0]))
                            node_index2 = ([n.i for n in sorted_nodes].index(vs[1]))
                            node_index3 = ([n.i for n in sorted_nodes].index(vs[2]))
                            jbeam_file.write('["%s","%s","%s"],\n' % (
                                sorted_nodes[node_index1].node_name, sorted_nodes[node_index2].node_name,
                                sorted_nodes[node_index3].node_name))
                        else:
                            self.report({'ERROR'}, 'ERROR: TriCol %i isn\'t tri' % vs.index)
                            if jbeam_file: jbeam_file.close()
                            if ob_new:
                                scene.objects.unlink(ob_new)
                                bpy.data.objects.remove(ob_new)
                            return {'CANCELLED'}
                    if not context.scene.jbeam.listbn:
                        jbeam_file.write('\t\t\t],\n')
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t}\n}')
                jbeam_file.flush()
                jbeam_file.close()

                # Deselect our new object
                ob_new.select_set(False)

                # Remove the new temp object
                scene.objects.unlink(ob_new)
                bpy.data.objects.remove(ob_new)

                if mesh.users == 0:
                    mesh.user_clear()

                bpy.data.meshes.remove(mesh)

                if temp_mesh.users == 0:
                    temp_mesh.user_clear()

                bpy.data.meshes.remove(temp_mesh)

            # Restore selection status
            '''for o in selectedObjects:
                o.select = True'''

            # Restore active object
            bpy.context.view_layer.objects.active = active_object

            return {'FINISHED'}

        except Exception as e:
            import traceback
            traceback.print_exception(type(e), e, sys.exc_info()[2])
            self.report({'ERROR'}, 'ERROR: ' + str(e))
            if jbeam_file: jbeam_file.close()
            if ob_new:
                scene.objects.unlink(ob_new)
                bpy.data.objects.remove(ob_new)
            return {'CANCELLED'}
