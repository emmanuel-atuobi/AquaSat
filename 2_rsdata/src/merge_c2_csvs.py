import pandas as pd
import os
import re

# Path to your local folder containing all 556 CSVs
# Change this to wherever you saved them
input_dir = 'C:/Users/atuob/Downloads/AquaSat_SR_MatchUps_C2/'

output_path = 'C:/Users/atuob/Downloads/aquasat_c2_reflectance.csv'

# Find all CSVs matching path/row pattern
pattern = re.compile(r'^\d+_\d+(_\d+)?\.csv$')
files = [f for f in os.listdir(input_dir) if pattern.match(f)]
print(f'Found {len(files)} CSV files')

# Merge
dfs = []
skipped = 0
for f in files:
    try:
        df = pd.read_csv(os.path.join(input_dir, f))
        dfs.append(df)
    except Exception as e:
        print(f'Skipping {f}: {e}')
        skipped += 1

merged = pd.concat(dfs, ignore_index=True)
print(f'Total rows before filtering: {len(merged)}')

# Drop rows where all reflectance values are null (no overpass)
ref_cols = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2']
merged = merged.dropna(subset=ref_cols, how='all')
print(f'Total rows after dropping null reflectance: {len(merged)}')

# Join with original water quality parameters
wq = pd.read_csv('C:/Users/atuob/Downloads/sr_wq_rs_join.csv')
wq_cols = ['SiteID', 'date', 'chl_a', 'doc', 'secchi', 'tss',
           'lat', 'long', 'type', 'source', 'endtime', 'date_only',
           'p_sand', 'tis', 'TZID', 'date_utc', 'clouds', 'time',
           'landsat_id', 'timediff', 'pwater', 'id']
wq = wq[wq_cols].drop_duplicates(subset=['SiteID', 'date'])

final = merged.merge(wq, on=['SiteID', 'date'], how='left')
print(f'Total rows after joining water quality: {len(final)}')
print(f'Columns: {final.columns.tolist()}')
print(f'Skipped files: {skipped}')

final.to_csv(output_path, index=False)
print(f'Saved to {output_path}')