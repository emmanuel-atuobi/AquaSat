import pandas as pd
import os

# Load the full AquaSat CSV
df = pd.read_csv('C:/Users/atuob/Downloads/sr_wq_rs_join.csv')

# Keep only the columns the GEE pull script needs
cols_needed = ['SiteID', 'date', 'date_unity', 'lat', 'long', 'path', 'row']
df = df[cols_needed].dropna(subset=['lat', 'long', 'path', 'row', 'date'])

# Convert path and row to integers
df['path'] = df['path'].astype(int)
df['row'] = df['row'].astype(int)

# Output directory
outdir = '2_rsdata/tmp/split_wide/'
os.makedirs(outdir, exist_ok=True)

# Group by path/row and split into chunks of 5000
chunk_size = 5000
total_files = 0

for (path, row), group in df.groupby(['path', 'row']):
    group = group.reset_index(drop=True)
    
    # Split into chunks of 5000 if large
    chunks = [group.iloc[i:i+chunk_size] for i in range(0, len(group), chunk_size)]
    
    for idx, chunk in enumerate(chunks):
        chunk = chunk.reset_index(drop=True)
        if len(chunks) == 1:
            filename = f'{path}_{row}.feather'
        else:
            filename = f'{path}_{row}_{idx+1}.feather'
        
        chunk.to_feather(outdir + filename)
        total_files += 1

print(f'Done. Created {total_files} feather files in {outdir}')