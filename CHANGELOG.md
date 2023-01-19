# Release Notes

## 0.3.4
 - removed `Export edges from faces` property and implementation. Another cause of duplicate Beams
 - fix `Could not create export directories` when using scene property for Export path

## 0.3.3
 - fix exception/crash when using NodesConnector  operator (Previously named `BeamGen`)
 - fix duplicated Beans attached to polygons

## 0.3.2
 - Fix for Blender 2.9x (removed unused and outdated argument)

## 0.3.1
 - Fix for Blender 2.83 (removed unused and outdated argument)

## 0.3.0
 - Blender 2.80 support!


 - User Interface
    - Major UI rework, cleaner and more user friendly
    - Added JBeam property overrides: Enable or disable JBeam sections/properties per object or from the scene
    - Added an automatic backup before export feature
    - Added an 'About' section in the scene JBeam panel
    - Added an optional cost value property
    - BeamGen can now be run from `Mesh > JBeam > BeamGen` in edit mode
    - Added a notification when the export succeeded or when BeamGen successfully executed


 - Exporter
    - Vertex Groups can now be used to export Node Groups!
    - JBeam indentation fixes for the exported files
    - Bugfixes and lots of code cleanup!

## 0.2.1
 - fix updater exception when printing outdated blender version

## 0.2.0
A lot of source code and ideas comes from https://github.com/Artfunkel/BlenderSourceTools/
 - Added Updater
 - Added GUI for Exporting

## 0.1.1
- Changed file layout

## 0.1.0
- Generate beams/edges between all selected nodes/vertices

## 0.0.1
- Use the export menu from Blender
- Export collision triangles
- Can export with jbeam syntax (json)

## Initial version from [rmikebaker](https://github.com/rmikebaker/BlenderBeamNGExport)
- Export beams and nodes has a list
