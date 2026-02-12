import pandas as pd
import xarray as xr
import rioxarray
import os
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

script_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
print(script_path)
isimip_path = os.path.join(script_path, "../../data/Agriculture/ISIMIP")
worldbank_shapes_path = os.path.join(script_path, "../../data/Agriculture/WB_shapes/WB_GAD_ADM0.zip")


def area_weighted_mean(ds, mask):
    """Compute area-weighted mean over a masked region."""
    lat_radians = np.deg2rad(ds.lat)
    weights = np.cos(lat_radians)
    masked = ds.where(mask)
    weighted = masked * weights
    return weighted.sum(dim=["lat", "lon"]) / weights.where(mask).sum(dim=["lat", "lon"])

world_shapes = gpd.read_file(worldbank_shapes_path).to_crs("EPSG:4326")
khm_shape = world_shapes[world_shapes['ISO_A3'] == 'KHM'].geometry.union_all()

result = None
for file in os.listdir(isimip_path):
    if file.endswith(".nc"):
        impact_model, climate_model, _, ssp, _, _, growing_period_irrigation, _, _, _, _= file.split('.')[0].split('_')
        growing_period, irrigation = growing_period_irrigation.split('-')[1:]
        ds = xr.open_dataset(os.path.join(isimip_path, file), decode_times=False)
        if ds.time.units == 'growing seasons since 1601-01-01 00:00:00':
            ds['time'] = (ds['time'] + 1601).astype(int)
        else:
            raise ValueError("Unknown time units.")
        ds = ds.rio.write_crs("EPSG:4326").fillna(0)
        mask = ds.rio.clip([khm_shape], world_shapes.crs, drop=False)

        land_productivity = area_weighted_mean(mask[f"yield-{growing_period}-{irrigation}"], mask[f"yield-{growing_period}-{irrigation}"].notnull()).drop('spatial_ref').to_dataframe(name='land_productivity')
        for var, var_name in zip([impact_model, climate_model, ssp, growing_period, irrigation], ['impact_model', 'climate_model', 'ssp', 'growing_period', 'irrigation']):
            land_productivity[var_name] = var
        land_productivity.set_index(['impact_model', 'climate_model', 'ssp', 'growing_period', 'irrigation'], append=True, inplace=True)
        land_productivity = land_productivity.squeeze().unstack('time')
        if result is None:
            result = land_productivity
        else:
            result = pd.concat([result, land_productivity], axis=0)
result = result.sort_index()
print(result)

fig, ax = plt.subplots(figsize=(10, 6))
for (_, _, ssp, irrigation), year_data in result.xs('ri1', level='growing_period').iterrows():
    year_data.plot(ax=ax, label=f'SSP {ssp} - {irrigation}')
ax.legend()
plt.show()
print('finished')
