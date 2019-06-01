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
    def __init__(self, i, node_name, groups, x, y, z):
        self.i = i
        self.node_name = node_name
        self.groups = groups
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
        name="Export Faces to collision triangle",
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

    def execute(self, context):
        import sys
        jbeam_file = None

        scene = context.collection

        # Save currently active object
        active_object = context.active_object

        export_objects = []
        if self.export_scene:
            for selectable_object in bpy.context.selectable_objects:
                if selectable_object.type == 'MESH':
                    if '.jbeam' in selectable_object.name:
                        export_objects.append(selectable_object)

        else:
            for selected_object in context.selected_objects:
                if selected_object.type == 'MESH':
                    # selected_object.select = False
                    export_objects.append(selected_object)
        if len(export_objects) == 0:
            '''self.report({'ERROR'}, 'ERROR : At least one object must be selected to export')
            print('CANCELLED: Must be select objects to export')'''
            return {'CANCELLED'}

        temp_mesh = None
        temp_object = None
        try:
            for export_object in export_objects:
                # Make the active object be the selected one
                bpy.context.view_layer.objects.active = export_object
                print(export_object.data.jbeam)
                # Want to be in Object mode
                bpy.ops.object.mode_set(mode='OBJECT')

                # -------------------------------------
                # Create a copy of the selected object
                # -------------------------------------

                temp_name = export_object.name + '.JBEAM_TEMP'

                # Create new mesh
                temp_mesh = bpy.data.meshes.new(temp_name)

                # Create new object associated with the mesh
                temp_object = bpy.data.objects.new(temp_name, temp_mesh)

                # Copy data block from the old object into the new object
                temp_object.data = export_object.data.copy()
                temp_object.scale = export_object.scale
                temp_object.location = export_object.location
                temp_object.rotation_axis_angle = export_object.rotation_axis_angle
                temp_object.rotation_euler = export_object.rotation_euler
                temp_object.rotation_mode = export_object.rotation_mode
                temp_object.rotation_quaternion = export_object.rotation_quaternion

                # Link new object to the given scene, select it, and
                # make it active
                scene.objects.link(temp_object)
                temp_object.select_set(True)
                bpy.context.view_layer.objects.active = temp_object

                # Apply transforms
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                # TODO: Can we copy modifiers from original object and then do this?
                # mesh = ob_new.to_mesh(scene, True, 'PREVIEW')

                # Sort vertices
                mesh = temp_object.data
                nodes = []
                for vertex in mesh.vertices:
                    node = NGnode(vertex.index,
                                  export_object.data.jbeam.nodename,
                                  vertex.groups,
                                  round(vertex.co[0] + export_object.delta_location[0], 3),
                                  round(vertex.co[1] + export_object.delta_location[1], 3),
                                  round(vertex.co[2] + export_object.delta_location[2], 3))
                    nodes.append(node)

                sorted_z = sorted(nodes, key=lambda NGnode: NGnode.z)
                # sorted_z is nodes sorted by Z axis
                sorted_x = sorted(sorted_z, key=lambda NGnode: NGnode.x, reverse=True)
                # sorted_x is sorted_z sorted by -X axis
                sorted_nodes = sorted(sorted_x, key=lambda NGnode: NGnode.y)
                # sorted_nodes is sorted_x sorted by Yaxis
                # sorted_nodes is nodes sorted by Z axis then -X axis then Y axis?
                sorted_nodes = sorted(sorted_nodes, key=lambda NGnode: (
                0 in NGnode.groups.keys(), NGnode.groups[0].group if len(NGnode.groups) > 0 else 255))

                # Export
                new_line = '\n'
                # filename = objsel.name + '.jbeam'
                if '.jbeam' in export_object.name:
                    filename = export_object.name
                else:
                    filename = export_object.name + '.jbeam'
                print("File = " + str(self.filepath) + filename)

                if self.filepath == "":
                    if context.scene.jbeam.export_path == "":
                        self.report({'ERROR'},
                                    'ERROR : No export folder set. Go to Scene > JBeam Exporter. Export cancelled!')
                        if temp_object:
                            scene.objects.unlink(temp_object)
                            bpy.data.objects.remove(temp_object)
                        return {'CANCELLED'}
                    if context.scene.jbeam.export_path.startswith("//") and not context.blend_data.filepath:
                        if temp_object:
                            scene.objects.unlink(temp_object)
                            bpy.data.objects.remove(temp_object)
                        self.report({'ERROR'}, "Save the .blend file first.")
                        return {'CANCELLED'}
                    self.filepath = bpy.path.abspath(context.scene.jbeam.export_path)

                if not context.scene.jbeam.export_path.startswith("//"):
                    if not (os.path.isdir(self.filepath)):
                        if temp_object:
                            scene.objects.unlink(temp_object)
                            bpy.data.objects.remove(temp_object)
                        self.report({'ERROR'}, 'ERROR : Must be exported in a directory. Export cancelled!')
                        print('CANCELLED: Must be exported in a directory. directory = "' + self.filepath + '"')
                        return {'CANCELLED'}
                jbeam_file = open(self.filepath + filename, 'wt')
                # file = open(self.filepath + '/' + filename, 'wt')

                if not context.scene.jbeam.listbn:
                    author = 'Blender JBeam v' + PrintVer()
                    if context.scene.jbeam.author_name and len(context.scene.jbeam.author_name) > 0:
                        author = context.scene.jbeam.author_name + ", " + author
                    if '.jbeam' in export_object.name:
                        name = export_object.name[0:len(export_object.name) - 6]
                    else:
                        name = export_object.name
                    jbeam_file.write(
                        '{\n\t"%s":{\n\t\t"information":{\n\t\t\t"name":"%s",\n\t\t\t"authors":"%s"},\n\t\t"slotType":"%s",\n' % (
                            name, export_object.data.jbeam.name, author, export_object.data.jbeam.slot))
                mesh.update(calc_edges=True, calc_loop_triangles=True)

                i = 0
                jbeam_file.write('//--Nodes--')
                jbeam_file.write(new_line)
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t\t"nodes":[\n\t\t\t["id", "posX", "posY", "posZ"],\n')

                current_node_group_index = -2

                def get_vertexgroup_id(groups):
                    if len(groups) == 0:
                        return -1
                    else:
                        return groups[0].group

                def get_vertexgroup_name(groups):
                    if len(groups) == 0:
                        return ""
                    else:
                        return selected_object.vertex_groups[groups[0].group].name

                for vertex in sorted_nodes:
                    if current_node_group_index != get_vertexgroup_id(vertex.groups):
                        current_node_group_index = get_vertexgroup_id(vertex.groups)
                        if not context.scene.jbeam.listbn:
                            jbeam_file.write('\t\t\t')
                        jbeam_file.write('{"group":"%s"},\n' % (get_vertexgroup_name(vertex.groups)))

                    if not context.scene.jbeam.listbn:
                        jbeam_file.write('\t\t\t')
                    jbeam_file.write('[\"')
                    if vertex.x > 0:
                        vertex.node_name = vertex.node_name + 'l' + ('%s' % i)
                    elif vertex.x < 0:
                        vertex.node_name = vertex.node_name + 'r' + ('%s' % i)
                    else:
                        vertex.node_name = vertex.node_name + ('%s' % i)
                    jbeam_file.write(vertex.node_name)
                    jbeam_file.write('\",')
                    jbeam_file.write('%s' % (round(vertex.x + export_object.delta_location[0], 3)))
                    jbeam_file.write(',')
                    jbeam_file.write('%s' % (round(vertex.y + export_object.delta_location[1], 3)))
                    jbeam_file.write(',')
                    jbeam_file.write('%s' % (round(vertex.z + export_object.delta_location[2], 3)))
                    jbeam_file.write('],')
                    # to debug groups
                    # jbeam_file.write('//grp[%d]="%s"' % (get_vertexgroup_id(vertex.groups), get_vertexgroup_name(vertex.groups)) )
                    jbeam_file.write(new_line)
                    i += 1

                if current_node_group_index != -1:
                    if not context.scene.jbeam.listbn:
                        jbeam_file.write('\t\t\t')
                    jbeam_file.write('{"group":""},\n')

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
                    for face in mesh.polygons:
                        vertices = face.vertices
                        if len(vertices) == 3:
                            node_index1 = ([n.i for n in sorted_nodes].index(vertices[0]))
                            node_index2 = ([n.i for n in sorted_nodes].index(vertices[1]))
                            node_index3 = ([n.i for n in sorted_nodes].index(vertices[2]))
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
                        elif len(vertices) == 4:
                            node_index1 = ([n.i for n in sorted_nodes].index(vertices[0]))
                            node_index2 = ([n.i for n in sorted_nodes].index(vertices[1]))
                            node_index3 = ([n.i for n in sorted_nodes].index(vertices[2]))
                            node_index4 = ([n.i for n in sorted_nodes].index(vertices[3]))
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
                            report({'ERROR'}, 'ERROR: Face %i isn\'t tri or quad.' % vertices.index)
                            if jbeam_file: jbeam_file.close()
                            if temp_object:
                                scene.objects.unlink(temp_object)
                                bpy.data.objects.remove(temp_object)
                            return {'CANCELLED'}
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t\t\t],\n')

                if context.scene.jbeam.exp_tricol:
                    jbeam_file.write('//--Collision Triangles--')
                    jbeam_file.write(new_line)
                    temp_object.modifiers.new("tricol", "TRIANGULATE")
                    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="tricol")
                    if not context.scene.jbeam.listbn:
                        jbeam_file.write('\t\t"triangles":[\n\t\t\t["id1:", "id2:", "id3:"],\n')
                    mesh = temp_object.data
                    mesh.update(calc_edges=True, calc_loop_triangles=True)
                    for face in mesh.polygons:
                        vertices = face.vertices
                        if len(vertices) == 3:
                            if not context.scene.jbeam.listbn:
                                jbeam_file.write('\t\t\t')
                            node_index1 = ([n.i for n in sorted_nodes].index(vertices[0]))
                            node_index2 = ([n.i for n in sorted_nodes].index(vertices[1]))
                            node_index3 = ([n.i for n in sorted_nodes].index(vertices[2]))
                            jbeam_file.write('["%s","%s","%s"],\n' % (
                                sorted_nodes[node_index1].node_name, sorted_nodes[node_index2].node_name,
                                sorted_nodes[node_index3].node_name))
                        else:
                            self.report({'ERROR'}, 'ERROR: TriCol %i isn\'t tri' % vertices.index)
                            if jbeam_file: jbeam_file.close()
                            if temp_object:
                                scene.objects.unlink(temp_object)
                                bpy.data.objects.remove(temp_object)
                            return {'CANCELLED'}
                    if not context.scene.jbeam.listbn:
                        jbeam_file.write('\t\t\t],\n')
                if not context.scene.jbeam.listbn:
                    jbeam_file.write('\t}\n}')
                jbeam_file.flush()
                jbeam_file.close()

                # Deselect our new object
                temp_object.select_set(False)

                # Remove the new temp object
                scene.objects.unlink(temp_object)
                bpy.data.objects.remove(temp_object)

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
            if temp_object:
                scene.objects.unlink(temp_object)
                bpy.data.objects.remove(temp_object)
            return {'CANCELLED'}
