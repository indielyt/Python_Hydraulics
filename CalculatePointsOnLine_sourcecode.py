#-------------------------------------------------------------------------------
# Purpose:     Creates points on lines at a specified distance, percentage, or
#              interval using a fixed or field-based value. All polyline fields
#              are included in the output Point feature class. Points can be
#              created starting from the beginning, or end of the line.
#
# Author:      Ian Broad
# Website:     www.ianbroad.com
#
# Created:     09/17/2017
#-------------------------------------------------------------------------------

import arcpy

arcpy.env.overwriteOutput = True

polyline = arcpy.GetParameterAsText(0)
choice = str(arcpy.GetParameterAsText(1))
start_from = str(arcpy.GetParameterAsText(2))
use_field_for_value = str(arcpy.GetParameterAsText(3))
field_with_value = str(arcpy.GetParameterAsText(4))
distance = float(arcpy.GetParameterAsText(5))
end_points = str(arcpy.GetParameterAsText(6))
output = arcpy.GetParameterAsText(7)

spatial_ref = arcpy.Describe(polyline).spatialReference

mem_point = arcpy.CreateFeatureclass_management("in_memory", "mem_point", "POINT", "", "DISABLED", "DISABLED", spatial_ref)
arcpy.AddField_management(mem_point, "LineOID", "LONG")
arcpy.AddField_management(mem_point, "Value", "FLOAT")

result = arcpy.GetCount_management(polyline)
features = int(result.getOutput(0))

arcpy.SetProgressor("step", "Creating Points on Lines...", 0, features, 1)

search_fields = ["SHAPE@", "OID@"]
insert_fields = ["SHAPE@", "LineOID", "Value"]

if use_field_for_value == "YES":
    search_fields.append(field_with_value)

reverse_line = False
if start_from == "END":
    reverse_line = True

with arcpy.da.SearchCursor(polyline, (search_fields)) as search:
    with arcpy.da.InsertCursor(mem_point, (insert_fields)) as insert:
        for row in search:
            try:
                line_geom = row[0]
                length = float(line_geom.length)
                count = distance
                oid = str(row[1])
                start = arcpy.PointGeometry(line_geom.firstPoint)
                end = arcpy.PointGeometry(line_geom.lastPoint)

                if reverse_line == True:
                   reversed_points = []
                   for part in line_geom:
                       for p in part:
                           reversed_points.append(p)

                   reversed_points.reverse()
                   array = arcpy.Array([reversed_points])
                   line_geom = arcpy.Polyline(array, spatial_ref)

                if use_field_for_value == "YES":
                    count = float(row[2])
                    distance = float(row[2])

                ################################################################

                if choice == "DISTANCE":
                    point = line_geom.positionAlongLine(count, False)
                    insert.insertRow((point, oid, count))

                elif choice == "PERCENTAGE":
                    point = line_geom.positionAlongLine(count, True)
                    insert.insertRow((point, oid, count))

                elif choice == "INTERVAL BY DISTANCE":
                    while count <= length:
                        point = line_geom.positionAlongLine(count, False)
                        insert.insertRow((point, oid, count))

                        count += distance

                elif choice == "INTERVAL BY PERCENTAGE":
                    percentage = float(count * 100.0)
                    total_runs = int(100.0 / percentage)

                    run = 1
                    while run <= total_runs:
                        current_percentage = float((percentage * run) / 100.0)
                        point = line_geom.positionAlongLine(current_percentage, True)

                        insert.insertRow((point, oid, current_percentage))

                        run += 1

                elif choice == "START/END POINTS":
                    insert.insertRow((start, oid, 0))
                    insert.insertRow((end, oid, length))

                ################################################################

                if end_points == "START":
                    insert.insertRow((start, oid, 0))

                elif end_points == "END":
                    insert.insertRow((end, oid, length))

                elif end_points == "BOTH":
                    insert.insertRow((start, oid, 0))
                    insert.insertRow((end, oid, length))

                arcpy.SetProgressorPosition()

            except Exception as e:
                arcpy.AddMessage(str(e.message))


                ################################################################


line_keyfield = str(arcpy.ListFields(polyline, "", "OID")[0].name)

mem_point_fl = arcpy.MakeFeatureLayer_management(mem_point, "Points_memory")

arcpy.AddJoin_management(mem_point_fl, "LineOID", polyline, line_keyfield)

if "in_memory" in output:
    arcpy.SetParameter(8, mem_point_fl)

else:
    arcpy.CopyFeatures_management(mem_point_fl, output)

    arcpy.Delete_management(mem_point)
    arcpy.Delete_management(mem_point_fl)

arcpy.ResetProgressor()
arcpy.GetMessages()