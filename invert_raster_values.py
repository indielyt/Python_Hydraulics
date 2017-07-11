# WORKING 1/31/2017
# Script for subtracting existing from proposed rasters.  Highly dependent on naming conventions, 
# both existing and proposed rasters being in same folder...use with caution.  

# Positive Values indicate increase from "e" (existing) to "p" (proposed)

# IMPROVEMENTS TO MAKE: 
# Update metadata of files created

### Rasters must be in same folder
### File paths must not exceed esri best practices (Maximum of 6 folders deep)

import os
import arcpy
from arcpy import env
from arcpy.sa import *

# Environment Settings: Workspace setting and a variable called workspace for constructing file names
arcpy.env.workspace = r"R:\xxxxxx_Creek Rehabilitation Plan for Apple Valley\05_Design\02_Hydraulics\Working\Comparison_Existing_to_Final30%\wsel"
outworkspace = r"R:\xxxxxx_Creek Rehabilitation Plan for Apple Valley\05_Design\02_Hydraulics\Working\Comparison_Existing_to_Final30%\wsel_inverted"
arcpy.env.overwriteOutput = True

#check out Spatial Analyst Extension
arcpy.CheckOutExtension("Spatial") # check out ArcGIS Spatial Analyst

# create list of rasters in workspace
rasters = arcpy.ListRasters("","GRID")

# iterate through each point feature
for raster in rasters:
	outname = os.path.join(outworkspace, raster)
	outtimes = Times(raster,-1)
	outtimes.save(outname)



