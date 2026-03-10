import time
import ee
import os
import pandas as pd
ee.Initialize()

# Source necessary functions
exec(open("2_rsdata/src/GEE_pull_functions.py").read())

# Load Pekel water occurrence layer
pekel = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')

# Load Landsat Collection 2 collections
l8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
l7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
l5 = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')

# Apply Collection 2 scale factors
def applyScaleFactors(image):
    optical = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    return image.addBands(optical, None, True)

l8 = l8.map(applyScaleFactors)
l7 = l7.map(applyScaleFactors)
l5 = l5.map(applyScaleFactors)

# Identify collection for use in sourced functions
collection = 'SR'

# Standardize band names across collections
bn8 = ['SR_B2','SR_B3', 'SR_B4', 'SR_B5', 'SR_B6','SR_B7', 'QA_PIXEL']
bn57 = ['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5','SR_B7', 'QA_PIXEL']
bns = ['Blue', 'Green', 'Red', 'Nir', 'Swir1', 'Swir2', 'qa']

ls5 = l5.select(bn57, bns)
ls7 = l7.select(bn57, bns)
ls8 = l8.select(bn8, bns)

ls = ee.ImageCollection(ls5.merge(ls7).merge(ls8))

# Water mask from Pekel (80% occurrence threshold)
threshold = 80
water = pekel.select('occurrence').gt(threshold)
water = water.updateMask(water)

# Buffer distance in meters around each sample point
dist = 200

# Folder with in situ data split into chunks by path/row
ULdir = '2_rsdata/tmp/split_wide/'

# Get list of files to process
filesUp = os.listdir(ULdir)
filesUp = [x for x in filesUp if x != '.DS_Store']

for x in range(0, len(filesUp)):

    inv = pd.read_feather(ULdir + filesUp[x])

    path = int(filesUp[x].replace('.','_').split('_')[0])
    row = int(filesUp[x].replace('.','_').split('_')[1])

    if filesUp[x].replace('.','_').split('_')[2] == 'feather':
        count = ''
    else:
        count = '_'+str(int(filesUp[x].replace('.','_').split('_')[2]))

    task_name = str(path)+'_'+str(row)+count

    invOut = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([inv['long'][i],
    inv['lat'][i]]),{'SiteID':inv['SiteID'][i],
    'date':inv['date'][i],'date_unity':inv['date_unity'][i]}) for i in range(0,len(inv))])

    lsover = ee.ImageCollection(ls.filter(ee.Filter.eq('WRS_PATH',
    path)).filter(ee.Filter.eq('WRS_ROW', row)))

    data = ee.FeatureCollection(invOut.map(sitePull))

    dataOut = ee.batch.Export.table.toDrive(collection = data,
                                            description = task_name,
                                            folder = 'AquaSat_SR_MatchUps_C2',
                                            fileFormat = 'csv')
    maximum_no_of_tasks(15, 60)
    dataOut.start()
    print(f'Submitted task: {task_name}')

maximum_no_of_tasks(1, 300)
print('All tasks submitted and completed')