# Data acquisition

No dataset is bundled with this repository (per the journal's instruction that only source code is required). Every input is public. This file documents the exact source, access route and citation for each, plus the schema of the single processed table the notebook consumes.

## Expected local layout

```
data/
├── hakkari_gunluk_tum_degiskenler.csv          # processed daily ERA5-Land (1950-2025), ";"-separated
├── hakkari_glacier_area_2000_2024_gee_executed.csv
├── hakkari_spei_sonuclari.csv                   # precomputed SPEI-12, ";"-separated
└── spatial/
    ├── natural_earth_turkey.geojson
    ├── natural_earth_turkey_provinces.geojson
    ├── hakkari_glaciers_glims.gpkg
    ├── <country shaded-relief raster>.tif        # Natural Earth (public domain)
    └── <Cilo-Sat satellite raster>.tif           # Sentinel-2 / Landsat (public domain / CC BY)
nc_cilo_sat/
├── *.nc                                          # raw ERA5-Land NetCDF (provenance)
└── SSP/
    └── *EC-Earth3-CC*.nc                          # CMIP6 SSP forcing (2015-2099)
```

## Sources

| Dataset | Provider / access | License |
|---|---|---|
| ERA5-Land hourly/daily | Copernicus Climate Data Store, https://cds.climate.copernicus.eu | Copernicus licence (free, redistribution of derived data permitted) |
| EC-Earth3-CC CMIP6 (tas, pr, prsn, snd; SSP2-4.5, SSP5-8.5) | ESGF, https://esgf.llnl.gov | CMIP6 terms of use |
| Landsat glacier area | Google Earth Engine / USGS, https://earthengine.google.com | USGS public domain |
| GLIMS glacier polygons | https://www.glims.org | GLIMS data use policy |
| Natural Earth boundaries & shaded relief | https://www.naturalearthdata.com | Public domain |

## Processed daily table schema (`hakkari_gunluk_tum_degiskenler.csv`)

Separator `;`, datetime column `time`. Columns used by the framework:

| Column | Meaning | Unit |
|---|---|---|
| `t2m_C`, `d2m_C`, `tsn_C` | 2 m air, dewpoint, snow-surface temperature | °C |
| `sp_hPa` | surface pressure | hPa |
| `ws` | wind speed | m/s |
| `tp_mm`, `sf_mm`, `e_mm` | total precipitation, snowfall, evaporation | mm |
| `ssrd_W`, `strd_W`, `ssr_W`, `str_W` | down/net short- and long-wave radiation | W/m² |
| `slhf_W`, `sshf_W` | latent / sensible heat flux | W/m² |
| `snowc` | snow cover | % |
| `sd`, `sde_mm` | snow depth, snow-depth water equivalent | m, mm |
| `smlt_mm` | snowmelt | mm/day |
| `rsn`, `sro_mm`, `ro_mm`, `ssro_mm` | snow density, surface/total/sub-surface runoff (Set C only) | mixed |

The raw-to-processed extraction (point 44.000 E, 37.500 N) is performed from the NetCDF inventory in `nc_cilo_sat/`. The glacier-area CSV has columns `year, area_km2, n_images, ndsi_threshold` (NDSI threshold = 0.20), transcribed from the executed `Hakkari_Glacier_GEE.ipynb` workflow.
