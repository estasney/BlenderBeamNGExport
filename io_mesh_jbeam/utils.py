import sys


# By default, prints the current addon version.
# If a version tuple parameter is specified, it is printed instead of the current one.
def print_version(version_int_tuple=None):
    if version_int_tuple is not None:
        return ".".join(map(str, version_int_tuple))
    else:
        return ".".join(map(str, get_addon_version()))


def get_addon_version():
    return sys.modules.get(__name__.split(".")[0]).bl_info['version']
