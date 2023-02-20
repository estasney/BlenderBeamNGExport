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
    "author": "Mike Baker (rmikebaker), Thomas Portassau (50thomatoes50), Julien Vanelian (Distrikt64/Juju)",
    "location": "File > Import-Export",
    "version": (0, 3, 5),
    "blender": (2, 80, 0),
    "wiki_url": 'http://wiki.beamng.com/Blender_Exporter_plugin',
    "tracker_url": "https://github.com/50thomatoes50/BlenderBeamNGExport/issues",
    "description": "Export nodes, beams and collision triangles for BeamNG.drive (.jbeam)",
    "category": "Import-Export"
}

import bpy
import imp
import os
import bmesh

from bpy.props import *
from bpy.utils import *
from bpy.app.handlers import persistent
from .utils import *
from . import export_jbeam
from . import updater

for filename in [f for f in os.listdir(os.path.dirname(os.path.realpath(__file__))) if f.endswith(".py")]:
    if filename == os.path.basename(__file__):
        continue

    mod = sys.modules.get("{}.{}".format(__name__, filename[:-3]))

    if mod:
        imp.reload(mod)


class OBJECT_OT_nodes_connector(bpy.types.Operator):
    bl_idname = 'object.nodes_connector'
    bl_description = 'Create beams/edges between selected nodes/vertices\nBlenderBeamNGExport v.' + print_version()
    bl_label = 'NodesConnector (Previously named `BeamGen`)'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_object = context.edit_object

        if active_object is None:
            self.report({'ERROR'}, 'NodesConnector only operates in edit mode')
            return {'CANCELLED'}

        if not isinstance(active_object, bpy.types.Object) or not isinstance(active_object.data, bpy.types.Mesh):
            self.report({'ERROR'}, 'NodesConnector only operates on Meshes')
            return {'CANCELLED'}

        #from doc, python manage memory. no need to free manually or else it will crash
        bm = bmesh.from_edit_mesh(active_object.data)

        selected_vertices = [] #array of BMVert

        for vertex in bm.verts:
            if vertex.select:
                selected_vertices.append(vertex)

        vertex_count = len(selected_vertices)

        if vertex_count <= 1:
            self.report({'ERROR'}, 'Select more than 1 vertex')
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}

        edge_created = 0
        edge_existed = 0

        for n1 in selected_vertices:
            for n2 in selected_vertices:
                if n1 != n2 and n2.index > n1.index:
                    if bm.edges.get([n1,n2]) is None: #this already check for edges in the other direction, eg:[n2,n1] would return the same edge
                        edge_created += 1
                        bm.edges.new([n1,n2])
                    else:
                        edge_existed +=1

        if edge_created > 0:
            bmesh.update_edit_mesh(active_object.data)

        self.report({'INFO'}, 'NodesConnector successfully created %d edge(s), %d already existed'%(edge_created, edge_existed))
        return {'FINISHED'}


class MENU_MT_jbeam_mesh(bpy.types.Menu):
    bl_label = 'JBeam'

    def draw(self, context):
        self.layout.operator(OBJECT_OT_nodes_connector.bl_idname)


def menu_func_mesh(self, context):
    layout = self.layout

    layout.separator()
    layout.menu("MENU_MT_jbeam_mesh")


class PREFERENCES_PF_jbeam_addon(bpy.types.AddonPreferences):
    bl_idname = __name__

    default_export_path = get_beamng_mod_path()

    default_export_path: bpy.props.StringProperty(
        name="Default Export Path",
        description="Where all the .jbeam files will be saved by default " +
                    "the next time you start blender or you open a new file",
        subtype='DIR_PATH',
        default=default_export_path,
        update=utils.save_prefs)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "default_export_path")


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
                group_layout.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname, text=single_object[0].name,
                                      icon='MESH_DATA')

        exportable_mesh_count = get_exportable_mesh_count()

        row = layout.row()
        row.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname,
                     text="Scene (selectable): all mesh like *.jbeam (" + str(exportable_mesh_count) + ")",
                     icon='SCENE_DATA').export_scene = True
        row.enabled = exportable_mesh_count > 0


def menu_func_export(self, context):
    self.layout.menu("MENU_MT_jbeam_export", text='JBeam (.jbeam)')


class PANEL_PT_jbeam_scene(bpy.types.Panel):
    bl_label = "JBeam Exporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        layout.operator(export_jbeam.SCRIPT_OT_jbeam_export.bl_idname, text="Export JBeam", icon="EXPORT")

        row = layout.row()
        row.alert = len(scene.jbeam.export_path) == 0
        row.prop(scene.jbeam, "export_path")

        row = layout.row()
        row.prop(scene.jbeam, "export_format", expand=True)

        row = layout.row()
        row.prop(scene.jbeam, 'backup')


class PANEL_PT_jbeam_scene_information(bpy.types.Panel):
    bl_label = "Information"
    bl_parent_id = "PANEL_PT_jbeam_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        self.layout.prop(context.scene.jbeam, "export_information", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False
        layout.active = scene.jbeam.export_information and scene.jbeam.export_format == 'jbeam'

        row = layout.row()
        row.prop(scene.jbeam, "author_names")


class PANEL_PT_jbeam_scene_nodes(bpy.types.Panel):
    bl_label = "Nodes"
    bl_parent_id = "PANEL_PT_jbeam_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        self.layout.prop(context.scene.jbeam, "export_nodes", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False
        layout.active = scene.jbeam.export_nodes

        col = layout.column()
        col.prop(scene.jbeam, "export_node_groups")


class PANEL_PT_jbeam_scene_beams(bpy.types.Panel):
    bl_label = "Beams"
    bl_parent_id = "PANEL_PT_jbeam_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        self.layout.prop(context.scene.jbeam, "export_beams", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False
        layout.active = scene.jbeam.export_beams

        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        column = flow.column()
        column.prop(scene.jbeam, "export_face_diagonals")


class PANEL_PT_jbeam_scene_collision_triangles(bpy.types.Panel):
    bl_label = "Collision Triangles"
    bl_parent_id = "PANEL_PT_jbeam_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        self.layout.prop(context.scene.jbeam, "export_collision_triangles", text="")

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False
        layout.active = context.scene.jbeam.export_collision_triangles

        column = layout.column()
        column.label(text="No properties yet.")


class PANEL_PT_jbeam_scene_about(bpy.types.Panel):
    bl_label = "About"
    bl_parent_id = "PANEL_PT_jbeam_scene"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        row = layout.row()
        row.operator(updater.SCRIPT_OT_jbeam_update.bl_idname, text="Check For Updates", icon="QUESTION")

        column = layout.column()
        split = column.split()
        sub = split.row()
        sub.operator("wm.url_open", text="Documentation", icon="HELP").url = bl_info['wiki_url']
        sub.operator("wm.url_open", text="Report a Bug", icon='URL').url = bl_info['tracker_url']

        column = layout.column()
        column.label(text="Blender BeamNG Jbeam Exporter v" + print_version())
        column.separator()
        column.label(text="Maintainers : Thomas Portassau (50thomatoes50), Julien Vanelian (Distrikt64/Juju)")
        column.label(text="Orginal addon : Mike Baker (rmikebaker)")


class PANEL_PT_jbeam_object(bpy.types.Panel):
    bl_label = "JBeam Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        if not context.active_object.type == "MESH":
            column = layout.column()
            column.label(text='Non-mesh objects are not compatible with the exporter.',
                         icon='ERROR')


class PANEL_PT_jbeam_object_information(bpy.types.Panel):
    bl_label = "Information"
    bl_parent_id = "PANEL_PT_jbeam_object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        if context.active_object.type == "MESH":
            self.layout.prop(context.active_object.data.jbeam, "export_information", text="")

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        # Don't load the properties as they don't exist in the objects's data
        if not active_object.type == "MESH" or not active_object.data.jbeam.export_information:
            layout.active = False
        else:
            layout.active = context.scene.jbeam.export_format == 'jbeam' and context.scene.jbeam.export_information

            object_data = active_object.data

            col = layout.column()
            col.prop(object_data.jbeam, "name")

            flow = layout.column_flow()

            column = flow.column()
            column.prop(active_object.data.jbeam, "export_value")

            column = flow.column()
            column.active = active_object.data.jbeam.export_value
            column.prop(object_data.jbeam, "value", text="")


class PANEL_PT_jbeam_object_slots(bpy.types.Panel):
    bl_label = "Slots"
    bl_parent_id = "PANEL_PT_jbeam_object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        # Don't load the properties as they don't exist in the objects's data
        if not active_object.type == "MESH":
            layout.active = False
        else:
            layout.active = context.scene.jbeam.export_format == 'jbeam'
            col = layout.column()
            col.prop(active_object.data.jbeam, "slot_type")


class PANEL_PT_jbeam_object_nodes(bpy.types.Panel):
    bl_label = "Nodes"
    bl_parent_id = "PANEL_PT_jbeam_object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        if context.active_object.type == "MESH":
            self.layout.prop(context.active_object.data.jbeam, "export_nodes", text="")

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active_object = context.active_object

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        # Don't load the properties as they don't exist in the objects's data
        if not active_object.type == "MESH" or not active_object.data.jbeam.export_nodes:
            layout.active = False
        else:
            layout.active = scene.jbeam.export_nodes

            col = layout.column()
            col.prop(active_object.data.jbeam, "node_prefix")

            col = layout.column()
            col.active = scene.jbeam.export_node_groups
            col.prop(active_object.data.jbeam, "export_node_groups")


class PANEL_PT_jbeam_object_beams(bpy.types.Panel):
    bl_label = "Beams"
    bl_parent_id = "PANEL_PT_jbeam_object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"

    def draw_header(self, context):
        if context.active_object.type == "MESH":
            self.layout.prop(context.active_object.data.jbeam, "export_beams", text="")

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        # Don't load the properties as they don't exist in the objects's data
        if not active_object.type == "MESH" or not active_object.data.jbeam.export_beams:
            layout.active = False
        else:
            layout.active = context.scene.jbeam.export_beams

            flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

            column = flow.column()
            column.prop(active_object.data.jbeam, "export_face_diagonals")


class PANEL_PT_jbeam_object_collision_triangles(bpy.types.Panel):
    bl_label = "Collision Triangles"
    bl_parent_id = "PANEL_PT_jbeam_object"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        if context.active_object.type == "MESH":
            self.layout.prop(context.active_object.data.jbeam, "export_collision_triangles", text="")

    def draw(self, context):
        layout = self.layout
        active_object = context.active_object

        layout.use_property_split = True  # Active single-column layout
        layout.use_property_decorate = False

        # Don't load the properties as they don't exist in the objects's data
        if not active_object.type == "MESH" or not active_object.data.jbeam.export_collision_triangles:
            layout.active = False
        else:
            layout.active = context.scene.jbeam.export_collision_triangles

            column = layout.column()
            column.label(text="No properties yet.")


class PROPERTIES_PG_jbeam_scene(bpy.types.PropertyGroup):
    #default_export_path = get_beamng_mod_path()

    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Where all the .jbeam files will be saved",
        subtype='DIR_PATH',
        default="//jbeam_exported/")
    export_format: bpy.props.EnumProperty(
        name="Export Format",
        items=[("jbeam", "JBeam", "Export as a JBeam file"),
               ("list", "List", "Export as a bare list of nodes, beams and collision triangles"),
               ])
    backup: bpy.props.BoolProperty(
        name="Backup Before Exporting",
        description="Backup the old JBeam file before exporting the new one",
        default=False)
    export_information: bpy.props.BoolProperty(
        name="Information",
        description="Export basic part information",
        default=True)
    export_nodes: bpy.props.BoolProperty(
        name="Nodes",
        description="Export vertices to nodes",
        default=True)
    export_node_groups: bpy.props.BoolProperty(
        name="Node Groups",
        description="Export vertex groups to node groups",
        default=True)
    export_beams: bpy.props.BoolProperty(
        name="Beams",
        description="Export edges to beams",
        default=True)
    export_collision_triangles: bpy.props.BoolProperty(
        name="Collision Triangles",
        description="Export faces to collision triangles",
        default=True)
    export_face_diagonals: bpy.props.BoolProperty(
        name="Diagonal Quad Faces",
        description="Edge on quad face (automatic diagonals)",
        default=True)
    author_names: bpy.props.StringProperty(
        name="Authors",
        description="Author names")


class PROPERTIES_PG_jbeam_object(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Name",
        description="Part name",
        default="")
    value: bpy.props.IntProperty(
        name="Value",
        description="Part cost",
        min=0)
    slot_type: bpy.props.StringProperty(
        name="Type",
        description="Slot type for this part",
        default="main")
    node_prefix: bpy.props.StringProperty(
        name="Prefix",
        description="String prefix used for node names",
        default="n")
    export_information: bpy.props.BoolProperty(
        name="Information",
        description="Export basic part information",
        default=True)
    export_value: bpy.props.BoolProperty(
        name="Value",
        description="Enable/Disable part value (cost)",
        default=False)
    export_nodes: bpy.props.BoolProperty(
        name="Nodes",
        description="Export vertices to nodes",
        default=True)
    export_node_groups: bpy.props.BoolProperty(
        name="Node Groups",
        description="Export vertex groups to node groups",
        default=True)
    export_beams: bpy.props.BoolProperty(
        name="Beams",
        description="Export edges to beams",
        default=True)
    export_face_diagonals: bpy.props.BoolProperty(
        name="Diagonal Quad Faces",
        description="Edge on quad face (automatic diagonals)",
        default=True)
    export_collision_triangles: bpy.props.BoolProperty(
        name="Collision Triangles",
        description="Export faces to collision triangles",
        default=True)


classes = (
    OBJECT_OT_nodes_connector,
    MENU_MT_jbeam_mesh,
    MENU_MT_jbeam_export,
    PREFERENCES_PF_jbeam_addon,
    PANEL_PT_jbeam_scene,
    PROPERTIES_PG_jbeam_scene,
    PROPERTIES_PG_jbeam_object,
    PANEL_PT_jbeam_object,
    PANEL_PT_jbeam_object_information,
    PANEL_PT_jbeam_object_slots,
    PANEL_PT_jbeam_object_nodes,
    PANEL_PT_jbeam_object_beams,
    PANEL_PT_jbeam_object_collision_triangles,
    PANEL_PT_jbeam_scene_information,
    PANEL_PT_jbeam_scene_nodes,
    PANEL_PT_jbeam_scene_beams,
    PANEL_PT_jbeam_scene_collision_triangles,
    PANEL_PT_jbeam_scene_about,
    export_jbeam.SCRIPT_OT_jbeam_export,
    updater.SCRIPT_OT_jbeam_update,
    updater.MENU_MT_jbeam_updated
)


# Ran each time a .blend file loads
@persistent
def load_post_handler(scene): #DISABLED FOR NOW
    scene = bpy.context.scene

    # If it's a new file, or it doesn't have the scene export path property, get the export path from the preferences
    if not bpy.data.filepath or not scene.jbeam.export_path or bpy.data.filepath and not scene.jbeam.export_path:
        addon = bpy.context.preferences.addons.get('io_mesh_jbeam')
        scene.jbeam.export_path = addon.preferences.default_export_path


def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_edit_mesh.append(menu_func_mesh)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

    def make_pointer(prop_type):
        return bpy.props.PointerProperty(name="Jbeam settings", type=prop_type)

    bpy.types.Scene.jbeam = make_pointer(PROPERTIES_PG_jbeam_scene)
    bpy.types.Mesh.jbeam = make_pointer(PROPERTIES_PG_jbeam_object)
    #bpy.app.handlers.load_post.append(load_post_handler)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_edit_mesh.remove(menu_func_mesh)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    del bpy.types.Scene.jbeam
    del bpy.types.Mesh.jbeam
    #bpy.app.handlers.load_post.remove(load_post_handler)


# This allows you to run the script directly from blenders text editor
# to test the addon without having to install it.
if __name__ == "__main__":
    register()
