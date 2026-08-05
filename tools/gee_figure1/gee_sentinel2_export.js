// =====================================================================
// CryoSENSE-HK Figure 1 inset: copyright-clean Sentinel-2 export
// Google Earth Engine Code Editor (JavaScript).
// Sentinel-2 is Copernicus open data and is compatible with CC BY 4.0,
// unlike the Esri World Imagery currently used in the figure.
// Output: a true-colour GeoTIFF of the Cilo-Sat ROI written to Drive.
// =====================================================================

// Region of interest around the ERA5-Land grid point (44.000 E, 37.500 N).
// Slightly larger than the figure inset extents (43.940-44.050, 37.474-37.524).
var roi = ee.Geometry.Rectangle([43.90, 37.44, 44.10, 37.56]);

// Cloud mask using the Scene Classification + QA60 cirrus/cloud bits.
function maskS2(img) {
  var qa = img.select('QA60');
  var cloudBit = 1 << 10;
  var cirrusBit = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBit).eq(0).and(qa.bitwiseAnd(cirrusBit).eq(0));
  return img.updateMask(mask).divide(10000);
}

// Late-summer composite (minimal seasonal snow -> clearest terrain/glacier context).
// Change the months to Dec-Feb if a snow-covered scene is preferred.
var collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2023-07-01', '2023-09-30')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2);

var composite = collection.median().clip(roi);

// True colour (B4 red, B3 green, B2 blue), gently stretched for print.
var trueColour = composite.select(['B4', 'B3', 'B2']);
var visParams = {min: 0.0, max: 0.30, gamma: 1.1};
Map.centerObject(roi, 12);
Map.addLayer(trueColour, visParams, 'Sentinel-2 true colour');

// Export an 8-bit RGB GeoTIFF in WGS84 to Drive.
var rgb = trueColour.visualize(visParams);
Export.image.toDrive({
  image: rgb,
  description: 'cilo_sat_sentinel2_truecolor',
  fileNamePrefix: 'cilo_sat_sentinel2_truecolor',
  region: roi,
  scale: 10,
  crs: 'EPSG:4326',
  maxPixels: 1e9
});

// After running: open the Tasks tab, run the export, download the .tif from Drive,
// place it in data/spatial/cilo_sat_sentinel2_wgs84.tif, then run figure1_rebuild.py.
