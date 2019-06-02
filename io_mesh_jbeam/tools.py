#!/usr/bin/env python

__version__ = "0.3.0"

# By default, prints the current addon version.
# If a version tuple parameter is specified, it is printed instead of the current one.
def print_version(version_tuple=None):
    if version_tuple is not None:
        return ".".join(map(str, version_tuple))
    else:
        return __version__
