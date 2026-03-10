#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Google Earth Engine Reflectance Pull Functions
Created on Mon Apr  9 14:24:13 2018
@author: simontopp
"""

# Add filler panchromatic band to landsat 5 images.
def addPan(img):
  wPan = img.addBands(ee.Image(-999).rename('B8'))
  return wPan

###These are functions for unpacking the bit quality assessment band for TOA  
def Unpack(bitBand, startingBit, bitWidth):
  #unpacking bit bands
  #see: https://groups.google.com/forum/#!starred/google-earth-engine-developers/iSV4LwzIW7A
  return (ee.Image(bitBand)\
  .rightShift(startingBit)\
  .bitwiseAnd(ee.Number(2).pow(ee.Number(bitWidth)).subtract(ee.Number(1)).int()))
  
def UnpackAll(bitBand, bitInfo):
  unpackedImage = ee.Image.cat([Unpack(bitBand, bitInfo[key][0], bitInfo[key][1]).rename([key]) for key in bitInfo])
  return unpackedImage

####  This function maps across all the sites in a given Path/Row file and 
# extracts reflectance data for each in situ sampling date after creating a water mask.
def sitePull(i):

  date = ee.Date(i.get('date'))
  sdist = i.geometry().buffer(dist)

  # Filter to +/- 1 day window
  filtered = lsover.filterDate(date.advance(-1,'day'), date.advance(1,'day'))

  # Only proceed if there is at least one image
  def processImage(dummy):
    lsSample = ee.Image(filtered.first()).clip(sdist)

    mission = ee.String(lsSample.get('SPACECRAFT_ID')).split('_').get(1)

    bitAffected = {
      'Cloud': [3, 1],
      'CloudShadow': [4, 1],
      'CirrusConfidence': [8, 2]
    }

    road = ee.FeatureCollection("TIGER/2016/Roads").filterBounds(sdist)\
    .geometry().buffer(30)

    qa = lsSample.select('qa')
    qaUnpack = UnpackAll(qa, bitAffected)

    mask = qaUnpack.select('Cloud').eq(1)\
    .Or(qaUnpack.select('CloudShadow').eq(1))\
    .Or(qaUnpack.select('CirrusConfidence').eq(3))\
    .paint(road,1).Not()

    wateronly = water.clip(sdist)

    lsSample = lsSample.addBands(pekel.select('occurrence'))\
    .updateMask(wateronly).updateMask(mask)

    lsout = lsSample.reduceRegion(ee.Reducer.median(), sdist, 30)
    lsdev = lsSample.reduceRegion(ee.Reducer.stdDev(), sdist, 30)

    output = i.set({'sat': mission})\
    .set({"blue": lsout.get('Blue')})\
    .set({"green": lsout.get('Green')})\
    .set({"red": lsout.get('Red')})\
    .set({"nir": lsout.get('Nir')})\
    .set({"swir1": lsout.get('Swir1')})\
    .set({"swir2": lsout.get('Swir2')})\
    .set({"qa": lsout.get('qa')})\
    .set({"blue_sd": lsdev.get('Blue')})\
    .set({"green_sd": lsdev.get('Green')})\
    .set({"red_sd": lsdev.get('Red')})\
    .set({"nir_sd": lsdev.get('Nir')})\
    .set({"swir1_sd": lsdev.get('Swir1')})\
    .set({"swir2_sd": lsdev.get('Swir2')})\
    .set({"qa_sd": lsdev.get('qa')})\
    .set({"pixelCount": lsSample.reduceRegion(ee.Reducer.count(), sdist, 30).get('Blue')})\
    .set({'path': lsSample.get('WRS_PATH')})\
    .set({'row': lsSample.get('WRS_ROW')})

    return output

  # If no image exists for this date, return the feature unchanged with null values
  def returnNull(dummy):
    return i.set({'sat': None, 'blue': None, 'green': None, 'red': None,
                  'nir': None, 'swir1': None, 'swir2': None, 'qa': None,
                  'blue_sd': None, 'green_sd': None, 'red_sd': None,
                  'nir_sd': None, 'swir1_sd': None, 'swir2_sd': None,
                  'qa_sd': None, 'pixelCount': None, 'path': None, 'row': None})

  return ee.Feature(ee.Algorithms.If(filtered.size().gt(0), processImage(1), returnNull(1)))

##Function for limiting the max number of tasks sent to
#earth engine at one time to avoid time out errors

def maximum_no_of_tasks(MaxNActive, waitingPeriod):
  ##maintain a maximum number of active tasks
  time.sleep(10)
  ## initialize submitting jobs
  ts = list(ee.batch.Task.list())

  NActive = 0
  for task in ts:
       if ('RUNNING' in str(task) or 'READY' in str(task)):
           NActive += 1
  ## wait if the number of current active tasks reach the maximum number
  ## defined in MaxNActive
  while (NActive >= MaxNActive):
      time.sleep(waitingPeriod) # if reach or over maximum no. of active tasks, wait for 2min and check again
      ts = list(ee.batch.Task.list())
      NActive = 0
      for task in ts:
        if ('RUNNING' in str(task) or 'READY' in str(task)):
          NActive += 1
  return()
    
