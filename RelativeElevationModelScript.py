# Seems to be working correctly

# Improvements:
# Define a larger area than currently used as a clipping boundary.  Some of the stream area is clipped by the channel line extent rectangle


# Develops a relative elevation raster from inputs of streamline and elevation raster.  Used to determine risk of stream avulsion.

# Uses inverse distance weighting to create a detrended water surface grid from which the elevation grid is subtracted.
# The search radius determines extent of raster as well as applicability to specific project/site conditions.  Iterations will likely be useful.
# IDW search distance depends on floodplain characteristics.  Maximum IDW search distance should reach edge of floodplain.  Minimum IDW search distance should be approximately 2x bankfull

# Averaging multiple REM outputs can also provide an improved product with reduced model noise.
# Additional effort symbolizing output will help with avulsion hazard delineations.

# Source: Olson, Patricia L., Nicholas T. Legg, Timothy B. Abbe, Mary Ann Reinhart, and Judith K. Radloff. "A Methodology for Delineating Planning-Level Channel Migration Zones," 2014.

import arcpy
from arcpy.sa import *

# Delete in memory data that was written previously
arcpy.Delete_management("in_memory")

# Environment Settings
# arcpy.env.workspace = r"C:\DanielProjects\GIS\GIS Scripts\Stream Related Scripts\test2"
arcpy.env.workspace = r"C:\Users\Daniel.Aragon\Desktop\DJA_TEMP\ChannelMigrationZone_AI\Data_Created\REM"
arcpy.env.overwriteOutput = True
# arcpy.env.ScratchWorkspace = r"C:\DanielProjects\GIS\CdriveScratchFolder"  Once script is working, direct the intermediate IDW rasters to scratch folder and delete scratch folder at end of script

# Define input parameters
bankfull = 13  # channel bankfull drives geoprocessing extents
idwSearchRadius1 = 2 * bankfull  # minimum idw search radius
idwSearchRadius2 = 4 * bankfull  # intermediate idw search radius
dissolveField = "FID"  # dissolves the channel line based on FID i.e. all lines are dissolved and give FID of 0
outputCellSize = 3.2808333  # output cell size of idw raster surface


# Define input variables
# rasterSurface = r"C:\DanielProjects\GIS\GIS Scripts\Stream Related Scripts\test2\surface_clip"  # Terrain
rasterSurface = r"C:\Users\Daniel.Aragon\Desktop\DJA_TEMP\ChannelMigrationZone_AI\Data_Created\Raster\2011_clip"
# channelLine = r"C:\DanielProjects\GIS\GIS Scripts\Stream Related Scripts\test2\channel_clip.shp" # Line or polyline feature layer along channel thalweg
channelLine = r"C:\Users\Daniel.Aragon\Desktop\DJA_TEMP\ChannelMigrationZone_AI\Data_Created\Gold_Run.shp"

# intermediate variables, stored "in memory" if shapefiles, stored in workspace folder if raster
channelbuffer = "temp_channel_buffer.shp"  # buffer polygon around channel line
channelbufferdissolve = "temp_channelbufferdissolve.shp"
channeldissolve = "temp_channel_dissolve.shp"  # dissolves channel line into single features as long as they share an end vertices
channelpoints = "temp_channel_points.shp"  # channel points created from channel feature vertices
channelpoints3d = "temp_channel_3Dpoints.shp"  # channel points with elevation data derived from terrain
IDWboundary1 = "temp_idwboundary1.shp"

# intermediate rasters, name must be less than 13 characters
IDW0 = "IDW_0"
IDW1 = "IDW_1" 
IDW2 = "IDW_2"

# final raster
REM = "REM_1"

# Dissolve polyline input feature into one polyline feature
arcpy.Dissolve_management(channelLine, channeldissolve, dissolveField,"","","UNSPLIT_LINES")
print(arcpy.GetMessages())

# Create a buffer line around channel input equal to IDW search distance to use later as idw boundary line
arcpy.Buffer_analysis(channeldissolve, channelbuffer, idwSearchRadius1)
arcpy.Dissolve_management(channelbuffer,channelbufferdissolve)
arcpy.FeatureToLine_management(channelbufferdissolve, IDWboundary1)
print(arcpy.GetMessages())

# Densify Line (Creates extra vertices at the specified distance, for this process distance equals bankfull)
arcpy.Densify_edit(channeldissolve, "DISTANCE", bankfull)
print(arcpy.GetMessages())


# Create vertices from the channel line that was densified in previous step
arcpy.FeatureVerticesToPoints_management(channeldissolve, channelpoints, "ALL")
print(arcpy.GetMessages())


# Extract elevation values from raster surface to point features.  Must first check out Spatial Analyst Extension
from arcpy.sa import *
class LicenseError(Exception):
    pass
try:
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
        arcpy.CheckOutExtension("3D")
    else:
        #Raise a custom exception
        raise LicenseError
    # Run Extract Values to Points Tool
    ExtractValuesToPoints(channelpoints, rasterSurface, channelpoints3d)
    print(arcpy.GetMessages())

    # Create a "detrended" surface that approximates water surface/channel surface (ambiguous depending on raster creation) using inverse distance weighting. Must first check out 3D Analyst
    # NOTE: may have to run tool on test point features first to get one of IDW inputs - Z field.
    # Create detrended surface using IDW tool for both search radius. User can define power

    
    # arcpy.Idw_3d(channelpoints3d, "RASTERVALU", IDW1, outputCellSize, 2, idwSearchRadius1, IDWboundary1)
    arcpy.Idw_3d(channelpoints3d, "RASTERVALU", "IDW1", outputCellSize, 2, idwSearchRadius1)
    print(arcpy.GetMessages())

    # IDW = arcpy.Idw(channelpoints3d,"RASTERVALU")


   # Create REM by subtracting detrended surface from elevation raster. Must first check out Spatial Analyst Extension
   # Complete map algebra geoprocessing
    outRaster = Raster(rasterSurface) - Raster("IDW1")
    outRaster.save("REM")
    print(arcpy.GetMessages())

    # Extract REM from buffer
    extraction = ExtractByMask("REM", channelbufferdissolve)
    extraction.save = ("REM_final")
    print(arcpy.GetMessages())

except LicenseError:
    print("Spatial Analyst license is unavailable")
except arcpy.ExecuteError:
    print(arcpy.GetMessages())
finally:
    # Check in the ArcGIS 3D Analyst extension
    arcpy.CheckInExtension("Spatial")
    arcpy.CheckInExtension("3D")



# Delete in memory data
arcpy.Delete_management("in_memory")

# Print message of completion
print ("Relative elevation model script has finished")
