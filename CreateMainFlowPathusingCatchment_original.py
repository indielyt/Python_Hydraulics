'''***********************************************************************************************
Tool Name:  CreateMainFlowPath.py)
Version:  ArcGIS 10.1
Author:  CD 8/28/2014 (Environmental Systems Research Institute Inc.)
ConfigFile: AHPyConfig.xml located in the same place as source .py file. 
 
Required Arguments:
    (0) Input DrainageLine with RiverOrder populated
    (1) Input FlowDir raster
    (2) Input DEM
    (6) Output Main FLow Path feature class

Optional Arguments:
              
Description: for a given input catchment feature class, generate main flow path for Watershed associated 
to each catchment.

History:  Initial coding -  CD 02/03/2015
                            CD 02/1/8/2016 Issue with input or intermediate later not found (raster)
                                           Issue seems to be with mask - sometimes works the second  time sometimes not
                                           Remove the mask before watershed, did a con on fdr to get a mask fdr and use that one as input
       
Usage:  CreateMainFlowPath.py inDrainageLine inCatchment inCatchmentRaster inFlowDirRaster inFacRaster inStrLnkRaster outMFPFC
********************************************************************************************'''
import sys
import os
import time 
import datetime
import xml.dom.minidom
import xml
import math
import ArcHydroTools as ah

import arcpy
from arcpy import env
#import apwrutils


def trace():
    import traceback, inspect
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    # script name + line number
    line = tbinfo.split(", ")[1]
    filename = inspect.getfile(inspect.currentframe())
    # Get Python syntax error
    synerror = traceback.format_exc().splitlines()[-1]
    return line, filename, synerror


class CreateMainFlowPath:
    #variables:
    def __init__(self):
        self.DebugLevel = 3

    # def thisFileName(self):
        # import inspect
        # return inspect.getfile(inspect.currentframe())


    # def LoadConfigXML(self, sFileName):
        # if(sFileName.find(os.sep) < 0):
            # sXmlFile = sys.path[0] + os.sep + sFileName
        # else:
            # sXmlFile = sFileName

        # doc = xml.dom.minidom.parse(sXmlFile) 
        # try:
            # oNode = doc.getElementsByTagName("DebugLevel")[0]
            # if(oNode!=None):
                # self.DebugLevel=int(oNode.firstChild.nodeValue)
        # except:
            # self.DebugLevel=3
        # if((self.DebugLevel & 1)==1):
            # apwrutils.Utils.ShowMsg("Configuration Location:" + sXmlFile)
       


    def CreateMainFlowPath(self, inDrainageLine,inCatchment,inCatchmentRaster,inFlowDirRaster,inFacRaster,inStrLnkRaster,outMFPFC):

        try:

            #Set scratch workspace to scratchFolder
            arcpy.env.scratchWorkspace = arcpy.env.scratchFolder
     
            listtodel=[]

            if outMFPFC == os.path.basename(outMFPFC):
                desc = arcpy.Describe(inDrainageLine)
                outMFPFC = os.path.join(desc.dataElement.path,outMFPFC)   
   
            #Set environment
            arcpy.env.snapRaster = inFlowDirRaster
            arcpy.env.overwriteOutput = True
            
            #Get raster workspace
            rasterDescribe = arcpy.Describe(inFlowDirRaster)
            rd1 = rasterDescribe.path

            arcpy.MakeFeatureLayer_management(inCatchment,"Catchment_View1")
            listtodel.append("Catchment_View1")
            arcpy.SelectLayerByAttribute_management("Catchment_View1","NEW_SELECTION",'"RiverOrder" = 1')

            arcpy.CopyFeatures_management("Catchment_View1","in_memory\Catchment_View")
            arcpy.MakeFeatureLayer_management("in_memory\Catchment_View","Catchment_View")
            
            catchmentview = "Catchment_View"
            listtodel.append(catchmentview)

            catexpextent = arcpy.Describe(catchmentview).Extent
            fdr = arcpy.sa.Raster(arcpy.Describe(inFlowDirRaster).catalogPath)
            cellsize = fdr.meanCellWidth
            catexpextent.XMin = catexpextent.XMin - cellsize
            catexpextent.YMin = catexpextent.YMin - cellsize
            catexpextent.XMax = catexpextent.XMax + cellsize
            catexpextent.YMax = catexpextent.YMax + cellsize

            #Set selected catchment as output extent
            arcpy.env.extent = catexpextent
            arcpy.env.SnapRaster = inCatchmentRaster

            
            #Convert to raster
            catlevname = arcpy.CreateUniqueName("catlev1",arcpy.env.scratchFolder)
            firstlevcat = os.path.join(arcpy.env.scratchFolder, catlevname)
            listtodel.append(firstlevcat)

            arcpy.PolygonToRaster_conversion("Catchment_View","RiverOrder",firstlevcat, "CELL_CENTER","NONE",inFlowDirRaster)

            #Set as mask (build raster attribute table)
            arcpy.management.BuildRasterAttributeTable(firstlevcat)
            arcpy.env.mask = firstlevcat
            
            #Get minfac value under strlink grid
            strlnkfac = arcpy.sa.Con(inStrLnkRaster, inFacRaster)
            #strlnkfac.save(os.path.join(arcpy.env.scratchFolder,"strlnkfac"))

            #Convert to int
            strlnkfacint=arcpy.sa.Int(strlnkfac)

            #strlnkfacint.save(os.path.join(arcpy.env.scratchFolder,"strlnkfacint"))
            
            arcpy.AddMessage("Identifying lowest flow accumulation along strlink in first level catchments...")
            #Compute zonal min for strlnkfac in each strlnkfac
            strlnkzmin = arcpy.sa.ZonalStatistics(inStrLnkRaster,"VALUE", strlnkfacint,"MINIMUM","DATA")
            arcpy.management.BuildRasterAttributeTable(strlnkzmin)
            #strlnkzmin.save(os.path.join(arcpy.env.scratchFolder,"strlnkzmin"))
            
            #Find cell in strlnkfacint that is equal to the min value
            #minfacptgrname = arcpy.CreateUniqueName("minfacptgr",arcpy.env.scratchFolder)
            #minfacptgrraster = os.path.join(arcpy.env.scratchFolder,minfacptgrname)
            #listtodel.append(minfacptgrraster)
            minfacptgr=arcpy.sa.EqualTo(strlnkfacint,strlnkzmin)
            #arcpy.management.BuildRasterAttributeTable(minfacptgr)
            #minfacptgr.save(minfacptgrraster)
             
            #Keep only the cells with VALUE = 1 and set them to strlnkint value
            #minfacptfgrname = arcpy.CreateUniqueName("minfacptfgr",arcpy.env.scratchGDB)
            #minfacptfgrraster = os.path.join(arcpy.env.scratchGDB,minfacptfgrname)
            #listtodel.append(minfacptfgrraster)
            minfacptfgr = arcpy.sa.Con(minfacptgr,inStrLnkRaster,"#",'"Value" =1')
            #minfacptfgr.save(minfacptfgrraster)
            #arcpy.AddMessage("saving " + str(minfacptfgrraster))

                                    
            arcpy.AddMessage("Delineating first level catchments...")
            #Delineate subwatersheds for all from 
            #arcpy.management.BuildRasterAttributeTable(minfacptfgrraster)
            #arcpy.management.BuildRasterAttributeTable(inFlowDirRaster)

            #fdrpath = arcpy.Describe(inFlowDirRaster).catalogPath
            #arcpy.management.CopyRaster(inFlowDirRaster,

            #Set as mask
            arcpy.env.mask = ""

            fdrfistlevel = arcpy.sa.Con(firstlevcat,inFlowDirRaster)
            
            outMFPCatGrid = arcpy.sa.Watershed(fdrfistlevel,minfacptfgr) #minfacptfgr)
            #outMFPCatGrid1.save(outMFPCatGrid)

                    
            #Get first level flow direction
            #fdrfistlevel = arcpy.sa.Con(outMFPCatGrid,inFlowDirRaster)
            #fdrfistlevel.save(os.path.join(arcpy.env.scratchFolder,"fdrfistlevel"))
            #arcpy.management.BuildRasterAttributeTable(fdrfistlevel)
            
            #Compute flow length
            arcpy.AddMessage("Computing flow length...")
            firstlevleng=arcpy.sa.FlowLength(fdrfistlevel,"DOWNSTREAM") 
            #firstlevleng.save(rd1 + "\\firstlevleng")
            
    
            #Identify catchment boundary
            arcpy.AddMessage("Identifying catchment boundaries...")
            #Identify intersection of catchment boundary and firstlevelcat boundary

            #Find nodata area in catchment (to deal with external boundaries)
            isnullcat = arcpy.sa.IsNull(inCatchmentRaster)
            #isnullcat.save(rd1 + "\\isnullcat")

            #Set nodata areas in catchment to -9999
            conisnullcat = arcpy.sa.Con(isnullcat,inCatchmentRaster,-9999,'"Value" =0')
            #conisnullcat.save(rd1 + "\\conisnullcat")
            
            #Use focal stats to identify boundary cells
            focalstcat = arcpy.sa.FocalStatistics(conisnullcat,"Rectangle 3 3 CELL","VARIETY","NODATA")
            #focalstcat.save(rd1 + "\\focalstcat")
            arcpy.env.mask = firstlevcat
            
            #Identify boundary cells asa cells located near cells of different value			
            confolcat= arcpy.sa.Con(focalstcat,outMFPCatGrid,"#",'"Value" >1')
            #confolcat.save(rd1 + "\\confolcat")
            
            arcpy.AddMessage("Identifying maximum flow length cells along boundaries...")
            #Compute maximum flow length per zone along catchment boundary intersected with first level catchment boundary
            maxlen=arcpy.sa.ZonalStatistics(confolcat,"VALUE", firstlevleng,"MAXIMUM","DATA")
            
            #Find cells along catchment boundary with max flow length
            maxlencell = arcpy.sa.EqualTo(firstlevleng,maxlen)
            maxlencell1 = arcpy.sa.Con(maxlencell,outMFPCatGrid,"#",'"Value" =1')
            #maxlencell1.save(rd1 + "\\maxlencell1")
            
            #Need to look for duplicate
            maxlenpointname = arcpy.CreateUniqueName("maxlenpoint",arcpy.env.scratchGDB)
            maxlenpointlayer = os.path.join(arcpy.env.scratchGDB,maxlenpointname)
            listtodel.append( maxlenpointlayer)
            maxlenpoint = arcpy.RasterToPoint_conversion(maxlencell1,  maxlenpointlayer,"VALUE")
            
            #Make feature layer
            listtodel.append("maxlenpoint_lyr")
            arcpy.MakeFeatureLayer_management(maxlenpoint,"maxlenpoint_lyr")
            
            #Stats on
            maxlenpoint_statsname = arcpy.CreateUniqueName("maxlenpoint_stats",arcpy.env.scratchGDB)
            maxlenpoint_statstable= os.path.join(arcpy.env.scratchGDB,maxlenpoint_statsname)
            listtodel.append(maxlenpoint_statstable)
            maxlenpoint_stats=arcpy.Statistics_analysis("maxlenpoint_lyr",maxlenpoint_statstable,"pointid MIN","grid_code")

            #join with point
            arcpy.JoinField_management("maxlenpoint_lyr","grid_code", maxlenpoint_stats,"grid_code","FREQUENCY;MIN_pointid")
            
            #Select by attribute
            arcpy.SelectLayerByAttribute_management("maxlenpoint_lyr","NEW_SELECTION", "FREQUENCY> 1 and pointid<> MIN_pointid")

            #Delete selected features
            if int(arcpy.GetCount_management("maxlenpoint_lyr").getOutput(0)) > 0:
                arcpy.DeleteFeatures_management("maxlenpoint_lyr")
                arcpy.SelectLayerByAttribute_management("maxlenpoint_lyr","CLEAR_SELECTION")
                #Convert to raster
                maxlengthcell2name = arcpy.CreateUniqueName("maxlencell2",arcpy.env.scratchFolder)
                maxlenghtraster = os.path.join(arcpy.env.scratchFolder,maxlengthcell2name )
                #maxlenghtraster = rd1 + "\\maxlencell2"
                listtodel.append(maxlenghtraster)
                maxlencell1 = arcpy.PointToRaster_conversion("maxlenpoint_lyr","grid_code",maxlenghtraster,"MOST_FREQUENT","NONE", inFlowDirRaster)
                
            #Compute cost path from maxlencell
            arcpy.AddMessage("Computing cost paths...")
            costpath = arcpy.sa.CostPath(maxlencell1,fdrfistlevel,fdrfistlevel)
            #costpath.save(rd1 + "\\costpath")

            #Setting value of cost path to corresponding zone
            costpathlnk = arcpy.sa.Con(costpath,outMFPCatGrid)
            #costpathlnk.save(rd1 + "\\newlink")

            #Mosaic with strlnk
            #newlink = arcpy.sa.Con(inStrLnkRaster,inStrLnkRaster,costpathlnk)
            arcpy.Mosaic_management(inStrLnkRaster,costpathlnk, 'FIRST', 'FIRST', '#', '#', 'NONE', '0', 'NONE')
            
            #Generate line for costpathlnk
            ah.DrainageLineProcessing(costpathlnk,inFlowDirRaster,outMFPFC)

            #Add DrainID and DrainArea fields from DrainageLines
            arcpy.JoinField_management(outMFPFC,"GridID",inDrainageLine,"GridID","DrainID;DRAINAREA")

            #Add RiverOrder field
            arcpy.JoinField_management(outMFPFC,"GridID",inCatchment,"GridID","RiverOrder")

            #Loop through each features having RiverOrder = 1 and update from node so that line starts in middle of a cell and 
            #not on the boundary
            fdr = arcpy.sa.Raster(arcpy.Describe(inFlowDirRaster).catalogPath)
            cellsize = fdr.meanCellWidth
            # Create update cursor for feature class 
            fields = ['SHAPE@']
            whereclause = "RiverOrder=1"
            with arcpy.da.UpdateCursor(outMFPFC,fields,whereclause) as cursor1:
                for row1 in cursor1:
                    shape1 = row1[0]
                    part = shape1.getPart(0)
                    pointcount = len(part)
                    #Check direction of first segment
                    pPointGeomFirst = part[0]
                    pPointGeomSecond = part[1]
                    if pPointGeomFirst.Y <> pPointGeomSecond.Y:
                        #arcpy.AddMessage("diff y " + str(pPointGeomFirst.Y) + " " + str(pPointGeomSecond.Y))
                        #arcpy.AddMessage(str(pPointGeomFirst.Y -pPointGeomSecond.Y))
                        dl = pPointGeomFirst.Y - pPointGeomSecond.Y
                        if abs(dl) > cellsize:
                            if dl > 0:
                                #Move first point by cellsize/2
                                pPointGeomFirst.Y=pPointGeomFirst.Y - cellsize/2
                            else:
                                pPointGeomFirst.Y=pPointGeomFirst.Y + cellsize/2
                                
                    if pPointGeomFirst.X <> pPointGeomSecond.X:
                        #arcpy.AddMessage("diff x " + str(pPointGeomFirst.X) + " " + str(pPointGeomSecond.X))
                        #arcpy.AddMessage(str(pPointGeomFirst.X -pPointGeomSecond.X))
                        dl = pPointGeomFirst.X - pPointGeomSecond.X
                        #arcpy.AddMessage(abs(dl))
                        if abs(dl) > cellsize:
                            if dl > 0:
                                #Move first point by cellsize/2
                                pPointGeomFirst.X=pPointGeomFirst.X - cellsize/2
                            else:
                                pPointGeomFirst.X=pPointGeomFirst.X + cellsize/2
                    #Update 
                    row1[0]=arcpy.Polyline(part)
                    cursor1.updateRow(row1)

            #Loop through each features for a given river order in outMPFFC and update mfp shape
            #River Order = 1 already processed

            #Get max RiverOrder
            rovalues =[]
            with arcpy.da.SearchCursor(outMFPFC, "RiverOrder") as cursorro:
                for rowro in cursorro:
                    rovalues.append(rowro[0])
            rovalues.sort()
            riverordermax = rovalues[-1]
            arcpy.AddMessage("Maximum river order " + str(riverordermax))
            
            iriverorder = 1
            while iriverorder < riverordermax:
                iriverorder = iriverorder + 1
                #arcpy.AddMessage("Processing riverorder " + str(iriverorder))
                whereclause = "RiverOrder= " + str(iriverorder)
                # Create update cursor for feature class 
                fields = ['SHAPE@','HydroID']
                upfields = ['SHAPE@','NextDownID','DRAINAREA']
                #arcpy.AddMessage("whereclause " + whereclause)
                with arcpy.da.UpdateCursor(outMFPFC, fields,whereclause) as cursor:
                    #arcpy.AddMessage("in update")
                    for row in cursor:
                        hydroid = row[1]
                        #arcpy.AddMessage("in row hid=" + str(hydroid))
                        #Look for feature having NextDownID = hydroid and maximizing DRAINAREA
                        whereclauseup = "NextDownID=" + str(hydroid)
                        upshape=""
                        with arcpy.da.SearchCursor(outMFPFC, upfields,whereclauseup) as cursorup:
                            #arcpy.AddMessage("in search cursor")
                            maxdrainarea=0
                            for rowup in cursorup:
                                #arcpy.AddMessage("in cursorup")
                                drainarea = rowup[2]
                                if drainarea > maxdrainarea:
                                    upshape = rowup[0]
                                    maxdrainarea=drainarea
                        #if upshape<>"":
                        #arcpy.AddMessage("proceed")
                        #arcpy.AddMessage("ndid " + str(hydroid) + " area " + str(maxdrainarea))
                        partup = upshape.getPart(0)
                        #pointcount = len(partup)
                        #arcpy.AddMessage("lenup " + str(pointcount))
                        #arrayup=arcpy.Array(partup)
                        shape = row[0]
                        part = shape.getPart(0)
                        pointcount = len(part)
                        #arcpy.AddMessage("len " + str(pointcount))
                        #array = arcpy.Array(part)

                        icount=1
                        while icount < pointcount:
                            mypoint=part[icount]
                            partup.add(mypoint)
                            #arcpy.AddMessage(mypoint.X)
                            icount=icount+1

                        partarray = arcpy.Array()
                        partarray.add(partup)

                        #Mergeshape
                        #arcpy.AddMessage("updating cursor for feature " + str(hydroid))
                        row[0] = arcpy.Polyline(partarray)	
                        cursor.updateRow(row)		
                        
            #Loop through each line and trim line so that it stops in the middle of the closest cell within the zone
            #Loop through each features and update to node so that line ends in middle of cell within the catcment (outlet)
                       
            # Create update cursor for feature class 
            fields = ['SHAPE@']
            with arcpy.da.UpdateCursor(outMFPFC,fields) as cursorend:
                for rowend in cursorend:
                    shape = rowend[0]
                    part = shape.getPart(0)
                    pointcount = len(part)
                    #Check direction of last segment
                    pPointGeomLast = part[pointcount-1]
                    pPointGeomLastbutOne = part[pointcount-2]
                    iRemove = 0
                    if pPointGeomLast.Y <> pPointGeomLastbutOne.Y:
                        #arcpy.AddMessage("diff y " + str(pPointGeomLast.Y) + " " + str(pPointGeomLastbutOne.Y))
                        #arcpy.AddMessage(str(pPointGeomLast.Y -pPointGeomLastbutOne.Y))
                        dl = pPointGeomLast.Y - pPointGeomLastbutOne.Y
                        if abs(dl) > cellsize:
                            if dl > 0:
                                #Move last point by cellsize
                                pPointGeomLast.Y=pPointGeomLast.Y - cellsize
                            else:
                                pPointGeomLast.Y=pPointGeomLast.Y + cellsize
                        else:
                            #Remove last point as drainageline will stop at boundary
                            iRemove = 1
                            
                    if pPointGeomLast.X <> pPointGeomLastbutOne.X:
                        #arcpy.AddMessage("diff x " + str(pPointGeomLast.X) + " " + str(pPointGeomLastbutOne.X))
                        #arcpy.AddMessage(str(pPointGeomLast.X -pPointGeomLastbutOne.X))
                        dl = pPointGeomLast.X - pPointGeomLastbutOne.X
                        #arcpy.AddMessage(abs(dl))
                        if abs(dl) > cellsize:
                            if dl > 0:
                                #Move last point by cellsize
                                pPointGeomLast.X=pPointGeomLast.X - cellsize
                            else:
                                pPointGeomLast.X=pPointGeomLast.X + cellsize
                        else:
                            #Remove last point as drainageline will stop at boundary
                            iRemove = 1

                    if iRemove==1:
                        part.remove(pointcount-1)
                    #Update 
                    rowend[0]=arcpy.Polyline(part)
                    cursorend.updateRow(rowend)	

            #Delete attributes
            arcpy.DeleteField_management(outMFPFC, ["arcid", "from_node", "to_node","GridID","NextDownID","DrainArea","RiverOrder"])

            
            #Set output parameter
            #arcpy.AddWarning("set parameter " + outMFPFC)
            arcpy.SetParameterAsText(6,outMFPFC)

        except arcpy.ExecuteError:
            arcpy.AddError(str(arcpy.GetMessages(2)))
        except:
            arcpy.AddError(str(trace()))
            arcpy.AddError(str(arcpy.GetMessages(2)))
        finally:
            #Cleanup
            for s in listtodel:
                try:
                    if arcpy.Exists(s):arcpy.Delete_management(s)
                        #arcpy.AddMessage("Deleted " + str(s))
                except:
                    arcpy.AddMessage("Cannot delete " + str(s))
                    pass

            #Reset environment
            arcpy.ResetEnvironments()


        
         
if __name__ == '__main__':
    try:
        inDrainageLine = arcpy.GetParameterAsText(0)
        inCatchment = arcpy.GetParameterAsText(1)
        inCatchmentRaster = arcpy.GetParameterAsText(2)
        inFlowDirRaster = arcpy.GetParameterAsText(3)
        inFacRaster = arcpy.GetParameterAsText(4)
        inStrLnkRaster = arcpy.GetParameterAsText(5)
        outMFPFC = arcpy.GetParameterAsText(6)

        oProcessor = CreateMainFlowPath()
        #oProcessor.LoadConfigXML("AHPyConfig.xml")
        rslt = oProcessor.CreateMainFlowPath(inDrainageLine,inCatchment,inCatchmentRaster,inFlowDirRaster,inFacRaster, inStrLnkRaster,outMFPFC)
 
    except arcpy.ExecuteError:
        print str(arcpy.GetMessages(2))
        arcpy.AddError(str(arcpy.GetMessages(2)))
    except:
        print trace()
        arcpy.AddError(str(trace()))
        arcpy.AddError(str(arcpy.GetMessages(2)))
    finally:
        dt = datetime.datetime.now()
        print  'Finished at ' + dt.strftime("%Y-%m-%d %H:%M:%S")



