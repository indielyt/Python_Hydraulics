# WORKING 1/31/2017... use with caution. 
# Script for subtracting existing from proposed rasters.  Highly dependent on naming conventions, 
# both existing and proposed rasters being in same folder... 

# IMPROVEMENTS TO MAKE: 

### Rasters must be in same folder
### File paths must not exceed esri best practices (Maximum of 6 folders deep)

import os
import arcpy
from arcpy import env
from arcpy.sa import *

# Environment Settings: Workspace setting and a variable called workspace for constructing file names
arcpy.env.workspace = r"C:\DanielProjects\AV_temp_RasterProcessing_FullExtent_Save"
outworkspace = r"C:\DanielProjects\AV_temp_con_rasters"
arcpy.env.overwriteOutput = True

# Define coordinate system
CSV_coordinate_system = r"C:\Users\Daniel.Aragon\AppData\Roaming\ESRI\Desktop10.4\ArcMap\Coordinate Systems\NAD 1983 (2011) StatePlane Colorado North FIPS 0501 (US Feet).prj" 

#check out Spatial Analyst Extension
arcpy.CheckOutExtension("Spatial") # check out ArcGIS Spatial Analyst

# create list of rasters in workspace
rasters = arcpy.ListRasters("","GRID")

# define topo raster:
topo = r"C:\DanielProjects\AV_temp_con_rasters\topo_ft"

# create list of comparison rasters populated when one is completed.  Prevents repetitions in this nested loop
created = []

# iterate through each point feature
for raster1 in rasters:
	# Define event and output name
	split1 = raster1.split("_") # split input feature path at underscores
	temp_name1 = split1[0] # identify scenario
	design = temp_name1[0] # identify existing or proposed
	temp_name2 = split1[1] # identify raster type
	event1 = temp_name1[1:] # scrub "e" or "p" from scenario
	outname = "c_" + event1 + "_" + temp_name2

	if design == "p":  # only proceed for 1/2 of data, proposed
		# Iterate through raster list again, comparing to current raster in outer loop... if event analysis type match, but are different design scenarios, minus.
		for raster2 in rasters:
			split2 = raster2.split("_") # split input feature path at underscores
			temp_name3 = split2[0] # identify scenario
			temp_name4 = split2[1] # identify raster type
			event2 = temp_name3[1:] # scrub "e" or "p" from scenario

			if (event1 == event2) and (temp_name2 == temp_name4): 
				if outname not in created:
					created.append(outname)
					outpath = os.path.join(outworkspace, outname)
					if temp_name1 == "wsel":
						con_raster = arcpy.sa.Con(raster1==0,topo-raster2,Con(raster==0,raster1-topo,arcpy.Minus_3d(raster1, raster2)))
						con_raster.save(outpath)
					else:
					    arcpy.Minus_3d(raster1, raster2, outpath)



print len(created), " rasters created: ", created

			

	

# Check in spatial analyst
arcpy.CheckInExtension("Spatial")


