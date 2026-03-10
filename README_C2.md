# AquaSat-C2

**A Landsat Collection 2 Update of the AquaSat Inland Water Quality Matchup Dataset**

**Author:** Emmanuel Atuobi Agyekum
**Institution:** Indiana University Indianapolis  
**GitHub:** [emmanuel-atuobi/AquaSat](https://github.com/emmanuel-atuobi/AquaSat)  
**Based on:** Ross et al. (2019) — AquaSat: A Data Set to Enable Remote Sensing of Water Quality for Inland Waters. *Water Resources Research*, 55, 10012–10025. DOI: [10.1029/2019WR024883](https://doi.org/10.1029/2019WR024883)

---

## Overview

AquaSat-C2 is a updated version of the original AquaSat matchup dataset (Ross et al., 2019) in which all Landsat surface reflectance data have been re-extracted using **Landsat Collection 2 Level-2 (C02/T1_L2)** imagery via Google Earth Engine. The original AquaSat dataset used Landsat Collection 1 (C01/T1_SR), which was officially deprecated by the USGS in January 2022 and is no longer available on Google Earth Engine.

The motivation for this update is radiometric consistency: machine learning models trained on Collection 1 reflectance and applied to Collection 2 imagery introduce a systematic cross-collection bias. AquaSat-C2 eliminates this bias by ensuring that training data and application data share the same radiometric baseline — the improved atmospheric correction algorithms and updated processing chain of Landsat Collection 2.

**Final dataset:** 588,888 matchups of in situ water quality observations paired with same-day (±1 day) Landsat Collection 2 surface reflectance, covering inland waters across the contiguous United States and Alaska from 1984–2019.

---

## Dataset Contents

| Column | Description |
|--------|-------------|
| `SiteID` | Unique site identifier from WQP/LAGOS-NE |
| `date` | Date of in situ sampling |
| `blue` | Median blue band surface reflectance (SR_B1/SR_B2) |
| `green` | Median green band surface reflectance (SR_B2/SR_B3) |
| `red` | Median red band surface reflectance (SR_B3/SR_B4) |
| `nir` | Median NIR band surface reflectance (SR_B4/SR_B5) |
| `swir1` | Median SWIR1 band surface reflectance (SR_B5/SR_B6) |
| `swir2` | Median SWIR2 band surface reflectance (SR_B7) |
| `*_sd` | Standard deviation of each band across buffer pixels |
| `qa` | Median QA_PIXEL value |
| `pixelCount` | Number of valid water pixels used in median calculation |
| `sat` | Landsat satellite (5, 7, or 8) |
| `path` | Landsat WRS-2 path |
| `row` | Landsat WRS-2 row |
| `lat` / `long` | Sample site coordinates |
| `chl_a` | Chlorophyll-a concentration (µg/L) |
| `tss` | Total suspended solids (mg/L) |
| `doc` | Dissolved organic carbon (mg/L) |
| `secchi` | Secchi disk depth (m) |
| `type` | Water body type (Lake, River, Estuary) |
| `source` | Data source (WQP or LAGOS-NE) |

---

## Key Differences from Original AquaSat (Collection 1)

### 1. Landsat Collection IDs

| Sensor | Collection 1 (original) | Collection 2 (this dataset) |
|--------|--------------------------|------------------------------|
| Landsat 5 | `LANDSAT/LT05/C01/T1_SR` | `LANDSAT/LT05/C02/T1_L2` |
| Landsat 7 | `LANDSAT/LE07/C01/T1_SR` | `LANDSAT/LE07/C02/T1_L2` |
| Landsat 8 | `LANDSAT/LC08/C01/T1_SR` | `LANDSAT/LC08/C02/T1_L2` |

### 2. Reflectance Scale Factor

Collection 1 and Collection 2 use different scaling formulas to convert raw digital numbers to surface reflectance:

- **Collection 1:** `SR = DN × 0.0001` (divide by 10,000)
- **Collection 2:** `SR = (DN × 0.0000275) + (−0.2)`

The Collection 2 formula was applied in GEE before band extraction using:

```python
def applyScaleFactors(image):
    optical = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    return image.addBands(optical, None, True)
```

This means Collection 2 reflectance values can be slightly negative for very dark surfaces such as clear water. This is expected behavior and consistent with USGS Collection 2 documentation.

### 3. Band Naming Convention

Collection 2 Level-2 bands carry an `SR_` prefix:

| Collection 1 | Collection 2 |
|--------------|--------------|
| `B1`, `B2`, `B3`... | `SR_B1`, `SR_B2`, `SR_B3`... |

### 4. Cloud Masking Band and Bit Positions

Collection 1 used the `pixel_qa` band for cloud masking. Collection 2 uses `QA_PIXEL` with updated bit positions:

| Flag | Collection 1 bit | Collection 2 bit |
|------|-----------------|-----------------|
| Cloud | Bit 5 | Bit 3 |
| Cloud Shadow | Bit 3 | Bit 4 |
| Cirrus Confidence | Bit 8-9 | Bit 8-9 |

### 5. Image Metadata Property

The satellite identifier property changed between collections:

- **Collection 1:** `SATELLITE`
- **Collection 2:** `SPACECRAFT_ID`

### 6. Temporal Window

The original AquaSat code used a 0 to +1 day window (`filterDate(date, date.advance(1,'day'))`). AquaSat-C2 correctly implements the ±1 day window described in Ross et al. (2019):

```python
filtered = lsover.filterDate(date.advance(-1,'day'), date.advance(1,'day'))
```

---

## Quality Filtering Applied

After GEE extraction and merging, the following filters were applied:

1. **Null reflectance removal:** Observations where all six reflectance bands were null (no valid Landsat overpass within ±1 day) were removed. This affected 12,192 rows (~2% of total).

2. **High reflectance outlier removal:** Rows where any band exceeded 0.6 were removed as likely cloud/land contamination that passed through the water and cloud masks. This affected 1,831 rows (0.31%).

3. **Extreme negative removal:** Rows where any band fell below −0.05 were removed. Small negatives (> −0.05) were retained as they are physically plausible for clear water under Collection 2 scaling.

**Final row counts:**

| Stage | Rows |
|-------|------|
| Raw GEE output | 603,432 |
| After null reflectance removal | 591,240 |
| After outlier filtering | 588,888 |

---

## Repository Structure

```
AquaSat/
├── 2_rsdata/
│   └── src/
│       ├── GEE_pull_functions.py      ← Updated for Collection 2
│       ├── 5_surface_reflectance_pull.Rmd  ← Updated collection IDs
│       ├── run_aquasat_c2.py          ← Standalone Python GEE pull script
│       ├── prepare_split_wide.py      ← Reconstructs path/row feather files
│       └── merge_c2_csvs.py           ← Merges GEE output CSVs + WQ join
```

---

## How to Reproduce

### Requirements
- Python 3.11+
- Google Earth Engine account (register at https://earthengine.google.com)
- Conda (recommended)

### Setup

```bash
# Clone the repo
git clone https://github.com/emmanuel-atuobi/AquaSat.git
cd AquaSat

# Create environment
conda create -n aquasat python=3.11
conda activate aquasat
pip install earthengine-api pandas feather-format

# Authenticate GEE
earthengine authenticate
```

### Step 1 — Prepare input feather files

Download the original AquaSat matchup CSV from Figshare (Ross et al., 2019):  
DOI: [10.6084/m9.figshare.8139383](https://doi.org/10.6084/m9.figshare.8139383)

```bash
python 2_rsdata/src/prepare_split_wide.py
# Outputs 556 feather files to 2_rsdata/tmp/split_wide/
```

### Step 2 — Run the GEE pull

```bash
python 2_rsdata/src/run_aquasat_c2.py
# Submits ~556 export tasks to GEE
# Results exported to Google Drive folder: AquaSat_SR_MatchUps_C2
# Runtime: approximately 3 days for full CONUS dataset
```

Monitor task progress at: https://code.earthengine.google.com (Tasks tab)

### Step 3 — Merge and clean

Download all CSVs from Google Drive into a local folder, then:

```bash
python 2_rsdata/src/merge_c2_csvs.py
# Merges all CSVs, joins water quality parameters, applies quality filters
# Outputs: aquasat_c2_final.csv
```

---

## Caveats and Limitations

1. **Small negative reflectance values are expected.** The Collection 2 offset of −0.2 means very dark water pixels can return slightly negative SR values. Values between −0.05 and 0.0 are retained in the dataset as physically plausible. Users should be aware of this when computing band ratios or indices.

2. **Cross-collection comparability.** While the satellite overpass dates and geographic locations are identical between AquaSat (C1) and AquaSat-C2, the reflectance values are not directly comparable due to differences in atmospheric correction algorithms. Collection 2 uses improved LEDAPS (Landsat 5/7) and LaSRC (Landsat 8) corrections relative to Collection 1.

3. **Pekel water mask version.** This dataset uses `JRC/GSW1_4/GlobalSurfaceWater` for the water occurrence mask (80% threshold), which is an improvement over the `JRC/GSW1_0` version used in the original AquaSat. The updated Pekel dataset extends surface water occurrence records and improves water pixel identification for some water bodies.

4. **Null overpass observations.** Approximately 2% of observations had no valid Collection 2 overpass within ±1 day of the sampling date. These were removed. The original AquaSat pipeline pre-filtered observations to confirmed overpass dates, which is why this was not an issue in the original dataset.

5. **Landsat 9 not included.** This dataset covers 1984–2019 using Landsat 5, 7, and 8 only, consistent with the original AquaSat temporal coverage. Landsat 9 (launched September 2021) is not included.

6. **In situ data unchanged.** All water quality measurements (Chl-a, TSS, DOC, Secchi) are sourced directly from the original AquaSat dataset and have not been reprocessed. Only the Landsat reflectance values have been updated.

---

## Citation

If you use AquaSat-C2 in your research, please cite both this dataset and the original AquaSat paper:

**This dataset:**
> Agyekum, E.A. (2026). AquaSat-C2: A Landsat Collection 2 Update of the AquaSat Inland Water Quality Matchup Dataset. Indiana University Indianapolis. GitHub: https://github.com/emmanuel-atuobi/AquaSat

**Original AquaSat:**
> Ross, M.R.V., Topp, S.N., Appling, A.P., Yang, X., Kuhn, C., Butman, D., Simard, M., & Pavelsky, T.M. (2019). AquaSat: A Data Set to Enable Remote Sensing of Water Quality for Inland Waters. *Water Resources Research*, 55, 10012–10025. https://doi.org/10.1029/2019WR024883

---

## Contact

Emmanuel Atuobi  Agyekum
Indiana University Indianapolis  
GitHub: [@emmanuel-atuobi](https://github.com/emmanuel-atuobi)
