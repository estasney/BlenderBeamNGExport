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

# Script copyright (C) Thomas PORTASSAU (50thomatoes50) & Julien VANELIAN (Distrikt64/Juju)

# <pep8-80 compliant>

bl_info = {
    "name": "Export BeamNG.drive JBeam format (.jbeam)",
    "author": "Mike Baker (rmikebaker), Thomas Portassau (50thomatoes50) & Julien Vanelian (Distrikt64/Juju)",
    "location": "File > Import-Export",
    "version": (0, 3, 0),
    "blender": (2, 80, 0),
    "wiki_url": 'http://wiki.beamng.com/Blender_Exporter_plugin',
    "tracker_url": "https://github.com/50thomatoes50/BlenderBeamNGExport/issues",
    "warning": "Under construction!",
    "description": "Export nodes, beams and collision triangles for BeamNG.drive (.jbeam)",
    "category": "Import-Export"
}

import sys
import bpy
import imp
import os

from bpy.props import *
from bpy.utils import *
from .utils import *
from . import export_jbeam
from . import updater

for filename in [f for f in os.listdir(os.path.dirname(os.path.realpath(__file__))) if f.endswith(".py")]:
    if filename == os.path.basename(__file__):
        continue

    mod = sys.modules.get("{}.{}".format(__name__, filename[:-3]))

    if mod:
        imp.reload(mod)


class BeamGen(bpy.types.Operator):
    bl_idname = 'object.beamgen'
    bl_description = 'beamGen' + ' v.' + print_version()
    bl_label = 'beam(edge) generator'
    bl_options = {'REGISTER', 'UNDO'}

    # execute() is called by blender when running the operator.
    def execute(self, context):
        print("started")
        active_object = context.edit_object

        if active_object is None:
            self.report({'ERROR'}, 'ERROR : Currently not in edit mode! Operation cancelled!')
            print('CANCELLED: Not in edit mode')
            return {'CANCELLED'}

        print("obj:" + active_object.name)
        vertices = []

        bpy.ops.object.mode_set(mode='OBJECT')

        for vertex in active_object.data.vertices:
            if vertex.select:
                vertices.append(vertex.index)

        vertex_count = len(vertices)
        print("vertex_count:" + str(vertex_count))

        if vertex_count <= 1:
            self.report({'ERROR'}, 'ERROR: Select more than 1 vertex')
            return {'CANCELLED'}

        origin = len(active_object.data.edges) - 1
        edge_count = 0
        i = 0
        j = vertex_count

        while j != 0:
            j -= 1
            edge_count += (vertex_count - (vertex_count - j))

        active_object.data.edges.add(edge_count)

        for n1 in vertices:
            for n2 in vertices:
                if n1 != n2 and n2 > n1:
                    i += 1
                    active_object.data.edges[origin + i].vertices[0] = n1
                    active_object.data.edges[origin + i].vertices[1] = n2

        bpy.ops.object.mode_set(mode='EDIT')

        # this lets blender know the operator finished successfully.
        return {'FINISHED'}


class MENU_MT_jbeam_export(bpy.types.Menu):
    bl_label = 'Export JBeam'

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'EXEC_DEFAULT'

        selected_objects = context.selected_objects

        if len(selected_objects):
            single_object = []

            for selected_object in selected_objects:
                if selected_object.type == 'MESH':
                    single_object.append(selected_object)

            '''groups = list([ex for ex in selected_objects if ex.ob_type == 'GROUP'])
            groups.sort(key=lambda g: g.name.lower())

            group_layout = l
            for i,group in enumerate(groups):
                if type(self) == SMD_PT_Scene:
                    if i == 0: group_col = l.column(align=True)
                    if i % 2 == 0: group_layout = group_col.row(align=True)
                group_layout.operator(SmdExporter.bl_idname, text=group.name, icon='GROUP').group = group.get_id().name'''

            group_col = layout.column(align=True)
            group_layout = group_col.row(align=True)
            # group_layout.operator(SCRIPT_OT_jbeam_export.bl_idname, text="group.name", icon='GROUP')
            selected_object_count = len(single_object)

            if selected_object_count > 1:
                group_layout.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname,
                                      text="Export selected objects (" + str(selected_object_count) + ")",
                                      icon='OBJECT_DATA')

            elif selected_object_count:
                group_layout.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname, text=single_object[0].name, icon='MESH_DATA')

        elif len(bpy.context.selected_objects):
            row = layout.row()
            row.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname, text="invalid selection", icon='ERROR')
            row.enabled = False

        row = layout.row()
        num_scene_exports = getscene()

        row.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname,
                     text="Scene(selectable): all mesh like *.jbeam (" + str(num_scene_exports) + ")",
                     icon='SCENE_DATA').export_scene = True

        row.enabled = num_scene_exports > 0


def getscene():
    num = 0

    for selectable_object in bpy.context.selectable_objects:
        if selectable_object.type == 'MESH':
            if '.jbeam' in selectable_object.name:
                num += 1

    return num


def menu_func_export(self, context):
    self.layout.menu("MENU_MT_jbeam_export", text='JBeam (.jbeam)')


class JBEAM_Scene(bpy.types.Panel):
    bl_label = "JBeam Exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_default_closed = True

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname, text="Export JBeam")

        row = layout.row()
        row.alignment = 'CENTER'

        row = layout.row()
        row.alert = len(scene.jbeam.export_path) == 0
        row.prop(scene.jbeam, "export_path")

        row = layout.row()
        row.prop(scene.jbeam, "listbn")
        row.prop(scene.jbeam, "exp_ef")

        row = layout.row()
        row.prop(scene.jbeam, "exp_tricol")
        row.prop(scene.jbeam, "exp_diag")

        row = layout.row()
        row.prop(scene.jbeam, "author_name")


class Jbeam_SceneProps(bpy.types.PropertyGroup):
    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Where all the .jbeam files will be saved",
        subtype='DIR_PATH')
    listbn: bpy.props.BoolProperty(
        name="List",
        description="Export has a list of nodes and beams\nElse export as a JBeam file",
        default=False)
    exp_ef: bpy.props.BoolProperty(
        name="Edges From Faces",
        description="Export edges from faces",
        default=True)
    exp_tricol: bpy.props.BoolProperty(
        name="Collision Triangles",
        description="Export faces to collision triangles",
        default=True)
    exp_diag: bpy.props.BoolProperty(
        name="Diagonal Quad Faces",
        description="Edge on quad face (automatic diagonals)",
        default=True)
    incompatible: bpy.props.BoolProperty(
        name="Incompatible type",
        description="This type of object is not compatible with the exporter. Use mesh type please.",
        default=True)
    author_name: bpy.props.StringProperty(
        name="Author",
        description="Your name here")


class Jbeam_ObjProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Name",
        description="Part name",
        default="")
    slot: bpy.props.StringProperty(
        name="JBeam Slot",
        description="The slot for this part",
        default="main")
    nodename: bpy.props.StringProperty(
        name="Nodes Prefix",
        description="String prefix used to give names to nodes",
        default="n")


class JBEAM_Obj(bpy.types.Panel):
    bl_label = "JBeam parameter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_default_closed = True

    def draw(self, context):
        layout = self.layout
        if not context.active_object.type == "MESH":
            # print("Object not mesh")
            row = layout.row()
            row.prop(context.scene.jbeam, "incompatible")
        else:
            object_data = context.active_object.data

            row = layout.row()
            row.prop(object_data.jbeam, "name")

            row = layout.row()
            row.prop(object_data.jbeam, "slot")

            row = layout.row()
            row.prop(object_data.jbeam, "nodename")


classes = (
    BeamGen,
    MENU_MT_jbeam_export,
    JBEAM_Scene,
    Jbeam_SceneProps,
    Jbeam_ObjProps,
    JBEAM_Obj,
    export_jbeam.SCRIPT_OT_jbeam_export,
    updater.SCRIPT_OT_jbeam_update,
    updater.MENU_MT_jbeam_updated
)


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    def make_pointer(prop_type):
        return bpy.props.PointerProperty(name="Jbeam settings", type=prop_type)

    bpy.types.Scene.jbeam = make_pointer(Jbeam_SceneProps)
    bpy.types.Mesh.jbeam = make_pointer(Jbeam_ObjProps)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    del bpy.types.Scene.jbeam
    del bpy.types.Mesh.jbeam


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
