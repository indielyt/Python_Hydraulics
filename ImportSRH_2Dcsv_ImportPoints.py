# WORKING 1/25/2017
# Script for automating import of csv results from srh-2d modeling and creating point and polygon features
# Assumes pre-requisites of data format as listed below

# IMPROVEMENTS TO MAKE: 
# simplify output file structure/workspaces to more easily adapt to other tasks
# Update metadata of files created

### CSV names must be in format: "Proposed_100yr.csv" or "Existing_100yr.csv" for split function.  Bankfull must be shortened to "bkf" for raster naming (max 13 characters)
### CSV format must only have one row of column names.
### A separate CSV is required for each recurrence interval event.  
### CSV Must be cleaned and formated with "X", "Y", and "Depth" column headings.  OR, script must be edited below
### File paths must not exceed esri best practices (Maximum of 6 folders deep)

import os
import arcpy

# Environment Settings: Workspace, and two output workspaces depending on type of modeling result
arcpy.env.workspace = r"C:\DanielProjects\temp\av_proposed100"
existing_outworkspace = r"C:\DanielProjects\temp\av_proposed100"
proposed_outworkspace = r"C:\DanielProjects\temp\av_proposed100"
arcpy.env.overwriteOutput = True

# Define coordinate system
CSV_coordinate_system = r"C:\Users\Daniel.Aragon\AppData\Roaming\ESRI\Desktop10.4\ArcMap\Coordinate Systems\NAD 1983 (2011) StatePlane Colorado North FIPS 0501 (US Feet).prj" 


# For each csv in file, generate a point file and polygon file of results

for csv_file in arcpy.ListFiles("*.csv"):

    # define file names  and pathways for temporary features
    file_name = (os.path.splitext(csv_file)[0])
    temp1 = os.path.join("in_memory", file_name + "_temp1")
    temp2 = os.path.join("in_memory", file_name + "_temp2")
    temp2a = "temp2a"
    temp3 = os.path.join("in_memory", file_name + "_temp3")
    
    # define file names and pathways for output files (existing or proposed)
    if "existing" in file_name: # exsisting ends up here
        output1 = os.path.join(existing_outworkspace, file_name + "_pt.shp")
        output2 = os.path.join(existing_outworkspace, file_name + "_poly.shp")
    else: # proposed ends up here
        output1 = os.path.join(proposed_outworkspace, file_name + "_pt.shp")
        output2 = os.path.join(proposed_outworkspace, file_name + "_poly.shp")

    # define local variables from the CSV headings
    CSV_x = "X"
    CSV_y = "Y"
    CSV_z = "D"

    # make the event layer
    arcpy.MakeXYEventLayer_management(csv_file, CSV_x, CSV_y, temp1, CSV_coordinate_system, CSV_z)
    # save to temporary shapefile
    arcpy.CopyFeatures_management(temp1, temp2)
    # make feature layer for select by attribute tool
    arcpy.MakeFeatureLayer_management(temp2, temp2a)


    # select only depths greater than 0.05 ft
    arcpy.SelectLayerByAttribute_management(temp2a, "NEW_SELECTION", "D>0.05")
    # save only selected features to shapefile
    arcpy.CopyFeatures_management(temp2a, output1)

    # clear selection
    arcpy.SelectLayerByAttribute_management(temp2a,"CLEAR_SELECTION")

    # aggregate point features to create temporary polygon
    arcpy.AggregatePoints_cartography(output1, temp3, "50")

    # smooth temporary polygon
    arcpy.SmoothPolygon_cartography(temp3, output2, "PAEK", 30)

    # delete in_memory objects (temps)
    arcpy.Delete_management("in_memory")




