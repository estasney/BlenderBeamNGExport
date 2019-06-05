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

import io
import bpy
import os

from .utils import *

updater_supported = True
try:
    import urllib.request, urllib.error, zipfile
except:
    updater_supported = False


class MENU_MT_jbeam_updated(bpy.types.Menu):
    bl_label = "JBeam Exporter successfully updated"

    def draw(self, context):
        self.layout.operator("wm.url_open", text="Change log available at Github",
                             icon='TEXT').url = "https://github.com/50thomatoes50/BlenderBeamNGExport/blob/master/changelod.md"


class SCRIPT_OT_jbeam_update(bpy.types.Operator):
    bl_idname = "script.jbeam_update"
    bl_label = "JBeam Exporter updater"
    bl_description = "Updater for the Blender JBeam Exporter addon."

    @classmethod
    def poll(self, context):
        return updater_supported

    def execute(self, context):
        print("Checking JBeam Exporter addon updates...")

        cur_version = get_addon_version()

        try:
            data = urllib.request.urlopen(
                "https://raw.githubusercontent.com/50thomatoes50/BlenderBeamNGExport/master/io_mesh_jbeam/version.json").read().decode(
                'ASCII').split("\n")
            remote_ver = data[0].strip().split(".")
            remote_bpy = data[1].strip().split(".")
            download_url = data[2].strip()

            for i in range(min(len(remote_bpy), len(bpy.app.version))):
                if int(remote_bpy[i]) > bpy.app.version[i]:
                    self.report({'ERROR'}, "Blender is outdated. min ver:" + print_version(remote_bpy))
                    return {'FINISHED'}

            for i in range(min(len(remote_ver), len(cur_version))):
                try:
                    diff = int(remote_ver[i]) - int(cur_version[i])
                except ValueError:
                    continue

                if diff > 0:
                    print(
                        "Found new version {}, downloading from {}...".format(print_version(remote_ver), download_url))

                    zip = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(download_url).read()))
                    zip.extractall(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

                    self.report({'INFO'}, "Update done " + print_version(remote_ver))
                    bpy.ops.wm.call_menu(name="MENU_MT_jbeam_updated")
                    return {'FINISHED'}

            self.report({'INFO'}, "Addon is up to date: " + print_version())
            return {'FINISHED'}

        except urllib.error.URLError as err:
            self.report({'ERROR'}, " ".join(["update err download failed : " + str(err)]))
            return {'CANCELLED'}

        except zipfile.BadZipfile:
            self.report({'ERROR'}, "update err corruption")
            return {'CANCELLED'}

        except IOError as err:
            self.report({'ERROR'}, " ".join(["update err unknown : ", str(err)]))
            return {'CANCELLED'}
