# WORKING 1/31/2017
# Script for automating creation of depth grids from point and polygon features generated from srh-2d modeling resultS.
# Assumes csv of results has been run through "ImportSRH2Dcsv_ImportPoints.py" script (or equivalent)

# IMPROVEMENTS TO MAKE: 

### CSV format must only have one row of column names.
### A separate CSV is required for each recurrence interval event.  
### CSV Must be cleaned and formated with "X", "Y", and "Depth" column headings.  OR, script must be edited below
### File paths must not exceed esri best practices (Maximum of 6 folders deep)

import os
import arcpy
from arcpy import env
from arcpy.sa import *

# Environment Settings: Workspace setting and a variable called workspace for constructing file names
arcpy.env.workspace = r"C:\DanielProjects\AV_HabitatSuitability\habitat_lf_data_proposed"
workspace = r"C:\DanielProjects\AV_HabitatSuitability\habitat_lf_data_proposed"
arcpy.env.overwriteOutput = True

# Define coordinate system
CSV_coordinate_system = r"C:\Users\Daniel.Aragon\AppData\Roaming\ESRI\Desktop10.4\ArcMap\Coordinate Systems\NAD 1983 (2011) StatePlane Colorado North FIPS 0501 (US Feet).prj" 

# Define depth field
depthfield = "D"

# create list of point features used to create depth grid
point_features = arcpy.ListFeatureClasses('',"Point")
poly_features = arcpy.ListFeatureClasses('',"Polygon")

#check out Spatial Analyst Extension
arcpy.CheckOutExtension("Spatial") # check out ArcGIS Spatial Analyst

# iterate through each point feature
for feature in point_features:
	# define names of intermediary rasters and output raster (must be less than 13 characters)
	abbreviation = feature[0] # get first letter
	split = feature.split("_") # split input feature path at underscores
	event = split[1] # fetch event designation
	#print (event)

	# define file pathways and names as inputs/outputs for geoprocessing
	temp_raster1 = os.path.join("in_memory", abbreviation + event + "_temp1") # store in_memory 
	temp_raster2 = os.path.join("in_memory", abbreviation + event + "_temp2") # store in_memory 
	temp_raster3 = os.path.join("in_memory", abbreviation + event + "_temp3") # store in_memory 
	temp_poly = os.path.join("in_memory", abbreviation + event + "_poly")
	depth_grid = os.path.join(workspace,abbreviation + event +"_d")

	# create raster from point feature and Depth field with cell size 5
	arcpy.FeatureToRaster_conversion(feature,depthfield, temp_raster1, 5)
	# Set this raster as the snap raster for other operations
	arcpy.env.snapRaster = temp_raster1

	# Create a raster using focal statistics by taking mean of surrounding cells
	neighborhood = NbrRectangle(5,5,"CELL") # set method for filling no data cells (in this case, mean of cells within 5x5 rectangle of nullvalue cell)	
	mean_raster = FocalStatistics(temp_raster1, neighborhood,"MEAN","")
	# Save the output 
	mean_raster.save(temp_raster2)

	# Create a con raster where null areas of in_raster are filled by mean_raster
	con_raster = Con(IsNull(temp_raster1),mean_raster,temp_raster1) 
	# Save the output
	con_raster.save(temp_raster3)

	# Extract the results based on limits of floodplain polygon
	for feature in poly_features:
		split = feature.split("_") # split input feature path at underscores
		if event == split[1]: # designate if previously defined "event" (for current iteration) corresponds to polygon feature
			extraction = ExtractByMask(temp_raster3,feature)
			extraction.save(depth_grid)

# Check in spatial analyst
arcpy.CheckInExtension("Spatial")



### This method for clipping raster didn't clip to feature geometry, but may be useful elsewhere for extracting extents with describe object

	# Clip to floodplain boundary, must match polygon to original point feature in current for loop (must have use ImportSRH_2Dcsv_Points.py to develop polygons)
	# for feature in poly_features:
	# 	split = feature.split("_") # split input feature path at underscores
	# 	if event == split[1]: # designate if previously defined "events" correspond to polygon feature
	# 		# get extent, from a describe object
	# 		polyattributes = arcpy.Describe(feature) # create "describe object"
	# 		ExtObject = polyattributes.extent
	# 		clip = "%d %d %d %d" % (ExtObject.XMin, ExtObject.YMin, ExtObject.XMax, ExtObject.YMax)
	# 		print (clip)
	# 		# arcpy.Clip_management(temp_raster3,clip,depth_grid,"","ClippingGeometry")
	# 		arcpy.Clip_management(temp_raster3,clip,depth_grid, "","ClippingGeometry")


		# identify clip feature in workspace, relies on script "ImportSRH_2Dcsv_Points.py" having previously created polygon data 
		# clip_feature = os.path.join(workspace, file_name + "_poly.shp")

		# #get extent of clip feature for clip geoprocessing tool
		# extent = clip_feature.extent
		# print extent

		# clip depth raster with boundaries of inundation (polygon feature)

		#arcpy.Clip_management(temp_raster2,)


		## delete in_memory objects (temps)
		# arcpy.Delete_management("in_memory")
		#arcpy.CheckInExtension("Spatial")