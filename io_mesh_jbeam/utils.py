import sys
import bpy


# By default, prints the current addon version.
# If a version tuple parameter is specified, it is printed instead of the current one.
def print_version(version_int_tuple=None):
    if version_int_tuple is not None:
        return ".".join(map(str, version_int_tuple))
    else:
        return ".".join(map(str, get_addon_version()))


def get_addon_version():
    return sys.modules.get(__name__.split(".")[0]).bl_info['version']


def get_exportable_mesh_count():
    num = 0

    for selectable_object in bpy.context.selectable_objects:
        if selectable_object.type == 'MESH':
            if '.jbeam' in selectable_object.name:
                num += 1

    return num


def get_vertex_group_id(groups):
    if len(groups) == 0:
        return -1
    else:
        return groups[0].group


def get_vertex_group_name(obj, groups):
    if len(groups) == 0:
        return ""
    else:
        return obj.vertex_groups[groups[0].group].name