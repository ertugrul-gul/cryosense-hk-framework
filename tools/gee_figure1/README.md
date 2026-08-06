# Figure 1 rebuild (copyright-clean for CC BY 4.0)

An earlier draft of Figure 1 used two Esri rasters (`turkey_esri_world_physical_wgs84.tif`,
`cilo_sat_esri_world_imagery_wgs84.tif`). Esri imagery is proprietary and **not**
CC BY 4.0 compatible, so an open-access journal cannot publish it and attribution
alone does not resolve that. These steps rebuild the same layout from
public-domain and CC-compatible sources.

## Step 1 — Country relief (public domain, Natural Earth)
The published figure uses the **Natural Earth I — Land Cover + Shaded Relief + Water**
raster (`NE1_HR_LC_SR_W`, 1:10m, public domain), which reproduces the soft physical-map
look of the original basemap without any proprietary imagery:
https://www.naturalearthdata.com/downloads/10m-raster-data/10m-natural-earth-1/

Crop it to the Turkey view (the rebuild reads it as `natural_earth_shaded_relief_wgs84.tif`).
With GDAL:
```bash
gdal_translate -projwin 25.0 42.7 45.6 35.3 NE1_HR_LC_SR_W/NE1_HR_LC_SR_W.tif \
  data/spatial/natural_earth_shaded_relief_wgs84.tif
```
(`-projwin` is ulx uly lrx lry in degrees.) Without GDAL, crop the same bounds with
`rasterio.windows.from_bounds` and write bands 1–3 as an RGB GeoTIFF.

Public-domain alternatives, used the same way: Natural Earth II (`NE2_HR_LC_SR_W`, paler),
the cross-blended hypsometric tints (`HYP_HR_SR_W`, more saturated), or the grey
**Shaded Relief** (`SR_HR`).

## Step 2 — Cilo-Sat satellite inset (Copernicus Sentinel-2, CC BY compatible)
Run **either** `gee_sentinel2_export.js` (GEE Code Editor) **or** `gee_sentinel2_export.py`
(Python `ee`, same environment as `Hakkari_Glacier_GEE.ipynb`). Run the export task,
download the GeoTIFF from Drive, and save it as:
```
data/spatial/cilo_sat_sentinel2_wgs84.tif
```
Default is a late-summer (snow-minimal) composite; switch to Dec-Feb in the script for a snow scene.

## Step 3 — Render the figure
```bash
export CRYO_SPATIAL_DIR=/path/to/data/spatial
Run the Figure 1 cell of `CryoSENSE_HK_pipeline.ipynb` (section 2.1b).
```
Outputs `Fig1.tiff` (600 dpi, LZW) and a PNG preview to `outputs/figures/fig1_manuscript/`.

## New figure caption (with required source attribution)

> **Fig 1.** Study area in Hakkari Province, Türkiye, showing the Cilo-Sat glacier
> region of interest, GLIMS glacier polygons and the ERA5-Land extraction point
> (44.000 E, 37.500 N). Country basemap from Natural Earth I (public domain); the
> Cilo-Sat inset uses Copernicus Sentinel-2 imagery (contains modified Copernicus
> Sentinel-2 data [2023], processed by the European Space Agency); administrative
> boundaries from Natural Earth (public domain); glacier outlines from GLIMS.

This caption gives the direct source and licence of every layer, which is what an
open-access map attribution requires. No content permission form is needed once
the Esri layers are replaced.
