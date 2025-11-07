import pandas as pd
import xarray as xr
import rioxarray
import os
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
from openpyxl.styles.alignment import horizontal_alignments
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

script_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
isimip_path = os.path.join(script_path, "../../data/Hydropower/ISIMIP/KHM-discharge")

khm_area_weights = xr.open_dataset(os.path.join(script_path, "../../data/Hydropower/ISIMIP/KHM_area_weights.nc"))

def area_weighted_mean(ds, mask=None):
    """Compute area-weighted mean over a masked region."""
    lat_radians = np.deg2rad(ds.lat)
    weights = np.cos(lat_radians)
    if mask is not None:
        masked = ds.where(mask)
        weights = weights.where(mask)
    else:
        masked = ds
        weights = weights.broadcast_like(ds)
    weighted = masked * weights
    return weighted.sum(dim=["lat", "lon"]) / weights.sum(dim=["lat", "lon"])

def area_avg(ds):
    return ds.dis.sum(dim=['lon', 'lat']) / khm_area_weights.cellarea.sum()

seasons = {
    'pre-monsoon': [2, 3, 4],
    'monsoon': [5, 6, 7, 8, 9, 10],
    'post-monsoon': [11, 12, 1]
}

def process_file(file):
    """Process a single NetCDF file and return (monthly_df, seasonal_df)."""
    if not file.endswith(".nc"):
        return None, None

    impact_model, climate_model, _, ssp, *_ = file.split('.')[0].split('_')
    ds = xr.open_dataset(os.path.join(isimip_path, file), use_cftime=True)
    ds = ds.rio.write_crs("EPSG:4326")

    assert (ds.lon == khm_area_weights.lon).all()
    assert (ds.lat == khm_area_weights.lat).all()

    # discharge = area_weighted_mean(ds["dis"]).drop("spatial_ref")
    discharge = area_avg(ds).drop("spatial_ref")
    discharge = xr.decode_cf(discharge.to_dataset(name="discharge"), use_cftime=True)["discharge"]
    discharge["time"] = ("time", [pd.Timestamp(t.strftime("%Y-%m-%d")) for t in discharge["time"].values])
    discharge = discharge.to_dataframe(name="discharge")

    discharge["year"] = discharge.index.year
    discharge["season"] = discharge.index.to_series().apply(
        lambda dt: next((s for s, months in seasons.items() if dt.month in months), "annual")
    )

    discharge_seasonal = (discharge.groupby(["year", "season"]).discharge.sum() / discharge.groupby("season").discharge.count()).to_frame()

    discharge[["model", "ssp"]] = impact_model + "_" + climate_model, ssp
    discharge = discharge.reset_index().set_index(["ssp", "model", "time"]).discharge

    discharge_seasonal[["model", "ssp"]] = impact_model + "_" + climate_model, ssp
    discharge_seasonal = discharge_seasonal.reset_index().set_index(["ssp", "model", "year", "season"]).discharge


    return discharge, discharge_seasonal

def plot_result(result_seasonally_):
    season_colors = {
        'pre-monsoon': sns.color_palette("Set2")[0],
        'monsoon': sns.color_palette("Set2")[1],
        'post-monsoon': sns.color_palette("Set2")[2],
    }
    df = result_seasonally_.reset_index()
    fig, axs = plt.subplots(1, 2, figsize=(8, 8), sharey=True, sharex=True)
    for ssp, ax in zip(['ssp126', 'ssp585'], axs):
        df_ssp = df[df['ssp'] == ssp]
        sns.lineplot(
            data=df_ssp,
            x='year',
            y='discharge',
            hue='season',
            errorbar=lambda x: np.percentile(x, [10, 90]),
            estimator='mean',
            marker='o',
            ax=ax,
            legend=ax==axs[0],
            palette=season_colors,
        )
        # Add trend line for each season
        for season_idx, season in enumerate(seasons):
            df_season = df_ssp[df_ssp['season'] == season]
            mean_per_year = df_season.groupby('year')['discharge'].mean().reset_index()
            # Fit linear trend
            z = np.polyfit(mean_per_year['year'], mean_per_year['discharge'], 1)
            p = np.poly1d(z)
            ax.plot(mean_per_year['year'], p(mean_per_year['year']), linestyle='--', color=season_colors[season])

            slope, intercept = z
            ax.text(
                x=.01,
                y=.99 - season_idx * .05,
                s=f'{"+" if p(2050) - p(2020) > 0 else "-"}{(p(2050) - p(2020)) / p(2020) * 100:.1f}% between 2020-2050 ({season})',
                fontsize=9,
                verticalalignment='top',
                horizontalalignment='left',
                transform = ax.transAxes,
                color=season_colors[season],
            )

        ax.set_ylabel(r'Average discharge [$m^3s^{-1} / km^2$]')
        ax.set_xlabel('Year')
        ax.set_title(f'{ssp}')

    axs[1].legend(title='Season', frameon=False, loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    result_monthly_list = []
    result_seasonally_list = []

    files = [f for f in os.listdir(isimip_path) if f.endswith(".nc")]

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
    # with ProcessPoolExecutor(1) as executor:
        futures = {executor.submit(process_file, file): file for file in files}

        for future in tqdm(as_completed(futures), total=len(futures)):
            monthly, seasonal = future.result()
            if monthly is not None:
                result_monthly_list.append(monthly)
                result_seasonally_list.append(seasonal)

    result_monthly = pd.concat(result_monthly_list, axis=0)
    result_seasonally = pd.concat(result_seasonally_list, axis=0)
    plot_result(result_seasonally)
    print('done')
