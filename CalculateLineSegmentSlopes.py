# WORKS!!!
# Script calculates line slopes by segment. Output is a percent slope: (ft/ft)*100.
# Script to calculate slope of channel line, generalized at a distance defined by previously created points along the channel line
# NOTES: Requires an input point feature class of points along the line at specified distance (5x bankfull for example) which can be created from script cited below.

import arcpy
import math

# Environment Settings
arcpy.env.workspace = r"R:\138067_BoulderCounty_Trans_Flood\TO2 - 138368\05_Design\Habitat Restoration\839_GoldRun\GIS"
arcpy.env.overwriteOutput = True

# Define input variables
inFeature = "tributary_centerline.shp" # Channel centerline
inFeaturePoints = "pointsAlongCenterline_20ft.shp" # Channel pts
rasterSurface = r"R:\138067_BoulderCounty_Trans_Flood\TO2 - 138368\05_Design\Habitat Restoration\839_GoldRun\GIS\Terrain.c839existing.tif"

# Define output variables
outfeature1a = "channeldissolve.shp"
outFeature1 = "channelsplit.shp"
outFeature2 = "channelslopes.shp"

# Define parameter variables
newField = "slope"
dissolveField = "FID"

# Make backup copy of the feature layer
channelbackup = "channel_backup.shp"
arcpy.CopyFeatures_management(inFeature, channelbackup)
print(arcpy.GetMessages())

# Dissolve polyline input feature into one polyline feature
arcpy.Dissolve_management(inFeature, outfeature1a, dissolveField,"","","UNSPLIT_LINES")
print(arcpy.GetMessages())

# Split the dissolved channel line at points which have been created using the script CreatePointsOnLine available from www.ianbroad.com, < http://ianbroad.com/download/script/CreatePointsLines.py >
# and also from < http://gis.stackexchange.com/questions/91287/using-construct-points-on-all-lines-in-a-shapefile-arcpy >
arcpy.SplitLineAtPoint_management(outfeature1a, inFeaturePoints, outFeature1,"10 Feet")
print(arcpy.GetMessages())

# Convert segements to 3D shape.  Requires checking out #3D Analyst to perform operation, then checking back in. Borrowed from <http://desktop.arcgis.com/en/arcmap/10.3/analyze/python/access-to-licensing-and-extensions.htm>
class LicenseError(Exception):
    pass
try:
    if arcpy.CheckExtension("3D") == "Available":
        arcpy.CheckOutExtension("3D")
    else:
        # Raise a custom exception
        raise LicenseError
    # Convert segements to 3D shape
    arcpy.InterpolateShape_3d(rasterSurface,outFeature1, outFeature2)
    print(arcpy.GetMessages())
except LicenseError:
    print("3D Analyst license is unavailable")
except arcpy.ExecuteError:
    print(arcpy.GetMessages())
finally:
    # Check in the ArcGIS 3D Analyst extension
    arcpy.CheckInExtension("3D")

# Add new field to outFeature2 that will hold slope values
arcpy.AddField_management(outFeature2, newField, "FLOAT")
print(arcpy.GetMessages())

# Calculate slopes in the new field of outFeature2. Must be done with by creating a new function that calculates slope (%). Uses cursor to update slope field
def CalculateSlope(shape):
	slopevalue = abs(shape.lastPoint.Z- shape.firstPoint.Z)/ shape.length*100
	return slopevalue

with arcpy.da.UpdateCursor(outFeature2, ['SHAPE@', newField]) as cursor:
	for row in cursor:
		row[1] = CalculateSlope(row[0])
		cursor.updateRow(row)
print(arcpy.GetMessages())
