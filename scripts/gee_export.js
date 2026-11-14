// OPTIONAL national GLO-30 extraction. NOT run in this package.
// Upload earth_entities.gpkg converted to shapefile/GeoJSON as your own asset.
// Set asset and enable Earth Engine in a Cloud project. Never hard-code tokens.
var ASSET = 'projects/YOUR_PROJECT/assets/earth_entities';
var polygons = ee.FeatureCollection(ASSET);
var dem = ee.ImageCollection('COPERNICUS/DEM/GLO30').select('DEM').mosaic();
// Mosaic has no useful default projection. Compute terrain per local UTM zone.
for (var zone = 18; zone <= 21; zone++) {
  var crs = 'EPSG:' + (32700 + zone);
  var subset = polygons.filter(ee.Filter.eq('utm_zone', zone));
  var local = dem.reproject({crs: crs, scale: 30});
  var terrain = ee.Terrain.products(local);
  var aspect = terrain.select('aspect').multiply(Math.PI / 180);
  var bands = local.rename('elevation_m')
    .addBands(terrain.select('slope').rename('slope_deg'))
    .addBands(aspect.sin().rename('aspect_sin'))
    .addBands(aspect.cos().rename('aspect_cos'));
  var reducer = ee.Reducer.mean().combine({reducer2: ee.Reducer.minMax(), sharedInputs: true})
    .combine({reducer2: ee.Reducer.count(), sharedInputs: true});
  var stats = bands.reduceRegions({collection: subset, reducer: reducer, scale: 30, crs: crs, tileScale: 4});
  Export.table.toDrive({collection: stats, description: 'ING_GLO30_UTM' + zone, fileFormat: 'CSV',
    selectors: ['glacier_id','elevation_m_mean','elevation_m_min','elevation_m_max','elevation_m_count',
    'slope_deg_mean','slope_deg_count','aspect_sin_mean','aspect_cos_mean']});
}
// Reconstruct circular aspect with atan2(mean_sin, mean_cos), modulo 360.
// Preserve glacier_id. Inspect counts, nodata and small features before joining.
// Reprocessing 7719 polygons may require batching by province/basin.
