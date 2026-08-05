"""CryoSENSE-HK Figure 1 inset: copyright-clean Sentinel-2 export (Python ee API).

Sentinel-2 is Copernicus open data and is CC BY 4.0 compatible, unlike the Esri
World Imagery currently used in the figure inset. Run this in the same environment
as the existing Hakkari_Glacier_GEE.ipynb (which already authenticates Earth Engine).
"""

import ee

ee.Initialize()

# ROI around the ERA5-Land grid point (44.000 E, 37.500 N), slightly larger than
# the figure inset extents (43.940-44.050, 37.474-37.524).
roi = ee.Geometry.Rectangle([43.90, 37.44, 44.10, 37.56])


def mask_s2(img: "ee.Image") -> "ee.Image":
    """Mask clouds/cirrus via QA60 and scale reflectance to 0-1."""
    qa = img.select("QA60")
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))
    return img.updateMask(mask).divide(10000)


# Late-summer composite (minimal seasonal snow). Switch to Dec-Feb for a snowy scene.
collection = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(roi)
    .filterDate("2023-07-01", "2023-09-30")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    .map(mask_s2)
)

composite = collection.median().clip(roi)
vis = {"min": 0.0, "max": 0.30, "gamma": 1.1}
rgb = composite.select(["B4", "B3", "B2"]).visualize(**vis)

task = ee.batch.Export.image.toDrive(
    image=rgb,
    description="cilo_sat_sentinel2_truecolor",
    fileNamePrefix="cilo_sat_sentinel2_truecolor",
    region=roi,
    scale=10,
    crs="EPSG:4326",
    maxPixels=int(1e9),
)
task.start()
print("Export task started. Check the Earth Engine Tasks tab / your Drive.")
print("Then save the GeoTIFF as data/spatial/cilo_sat_sentinel2_wgs84.tif")
