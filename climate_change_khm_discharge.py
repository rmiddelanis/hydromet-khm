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

season_months = {
    'pre-monsoon': [2, 3, 4],
    'monsoon': [5, 6, 7, 8, 9, 10],
    'post-monsoon': [11, 12, 1]
}

def process_file(filepath, station_lon, station_lat):
    """Process a single NetCDF file and return (monthly_df, seasonal_df)."""
    if not filepath.split('.')[-1] in ['nc', 'nc4']:
        return None, None

    impact_model, climate_model, _, ssp, *_ = filepath.split('/')[-1].split('.')[0].split('_')
    ds = xr.open_dataset(filepath, use_cftime=True)
    ds = ds.rio.write_crs("EPSG:4326")

    ds = ds.sel(lon=station_lon, lat=station_lat, method="nearest")

    # discharge = area_weighted_mean(ds["dis"]).drop("spatial_ref")
    discharge = xr.decode_cf(ds, use_cftime=True)["dis"]
    discharge["time"] = ("time", [pd.Timestamp(t.strftime("%Y-%m-%d")) for t in discharge["time"].values])
    discharge = discharge.to_dataframe(name="discharge")

    if '_daily' in filepath:
        discharge = discharge['discharge'].resample('MS').mean().to_frame()

    discharge["year"] = discharge.index.year
    discharge["season"] = discharge.index.to_series().apply(
        lambda dt: next((s for s, months in season_months.items() if dt.month in months), "annual")
    )

    discharge_seasonal = (discharge.groupby(["year", "season"]).discharge.sum() / discharge.groupby("season").discharge.count()).to_frame()

    discharge[["GHM", "GCM", "ssp"]] = impact_model, climate_model, ssp
    discharge = discharge.reset_index().set_index(["ssp", "GCM", "GHM", "time"]).discharge

    discharge_seasonal[["GHM", "GCM", "ssp"]] = impact_model, climate_model, ssp
    discharge_seasonal = discharge_seasonal.reset_index().set_index(["ssp", "GCM", "GHM", "year", "season"]).discharge

    return discharge, discharge_seasonal


def plot_result(result_seasonally_):
    # season_colors = {
    #     'pre-monsoon': sns.color_palette("Set2")[0],
    #     'monsoon': sns.color_palette("Set2")[1],
    #     'post-monsoon': sns.color_palette("Set2")[2],
    # }
    seasons = result_seasonally_.index.get_level_values('season').unique()
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
            # palette=season_colors if season_colors else None,
        )
        # Add trend line for each season
        for season_idx, season in enumerate(seasons):
            df_season = df_ssp[df_ssp['season'] == season]
            mean_per_year = df_season.groupby('year')['discharge'].mean().reset_index()
            # Fit linear trend
            z = np.polyfit(mean_per_year['year'], mean_per_year['discharge'], 1)
            p = np.poly1d(z)
            ax.plot(
                mean_per_year['year'], p(mean_per_year['year']), linestyle='--',
                # color=season_colors[season]
            )

            slope, intercept = z
            ax.text(
                x=.01,
                y=.99 - season_idx * .05,
                s=f'{"+" if p(2050) - p(2020) > 0 else "-"}{(p(2050) - p(2020)) / p(2020) * 100:.1f}% between 2020-2050 ({season})',
                fontsize=9,
                verticalalignment='top',
                horizontalalignment='left',
                transform = ax.transAxes,
                # color=season_colors[season],
            )

        ax.set_ylabel(r'Average discharge [$m^3s^{-1} / km^2$]')
        ax.set_xlabel('Year')
        ax.set_title(f'{ssp}')

    axs[1].legend(title='Season', frameon=False, loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


def process_isimip_files(files_list, lon_coord, lat_coord):
    result_monthly_list = []
    result_seasonally_list = []
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
    # with ProcessPoolExecutor(1) as executor:
        futures = {executor.submit(process_file, file, lon_coord, lat_coord): file for file in files_list}
        for future in tqdm(as_completed(futures), total=len(futures)):
            monthly, seasonal = future.result()
            if monthly is not None:
                result_monthly_list.append(monthly)
                result_seasonally_list.append(seasonal)
    result_monthly = pd.concat(result_monthly_list, axis=0)
    result_seasonally = pd.concat(result_seasonally_list, axis=0)
    return result_monthly, result_seasonally


def load_isimip_data(isimip_path, station_coords_):
    hist_isimip_path = os.path.join(isimip_path, 'historical_histsoc')
    hist_files = [os.path.join(hist_isimip_path, f) for f in os.listdir(hist_isimip_path) if f.split(".")[-1] in ["nc", "nc4"]]

    if 'ISIMIP3b' in isimip_path:
        projections_isimip_path = os.path.join(isimip_path, 'projections_2015soc_from_histsoc')
    elif 'ISIMIP2b' in isimip_path:
        projections_isimip_path = os.path.join(isimip_path, 'projections_2005soc')
    projections_files = [os.path.join(projections_isimip_path, f) for f in os.listdir(projections_isimip_path) if f.split(".")[-1] in ["nc", "nc4"]]

    projections_monthly, projections_seasonal = process_isimip_files(projections_files, *station_coords_)
    hist_monthly, hist_seasonal = process_isimip_files(hist_files, *station_coords_)

    common_models = hist_monthly.droplevel(['ssp', 'time']).index.unique().intersection(projections_monthly.droplevel(['ssp', 'time']).index.unique())

    hist_monthly = hist_monthly[hist_monthly.index.droplevel(['ssp', 'time']).isin(common_models)]
    projections_monthly = projections_monthly[projections_monthly.index.droplevel(['ssp', 'time']).isin(common_models)]
    # hist_seasonal = hist_seasonal[hist_seasonal.index.droplevel(['ssp', 'year', 'season']).isin(common_models)]
    # projections_seasonal = projections_seasonal[projections_seasonal.index.droplevel(['ssp', 'year', 'season']).isin(common_models)]

    # data_seasonally = pd.concat([hist_seasonal, projections_seasonal], axis=0)

    data_monthly = pd.concat([hist_monthly, projections_monthly], axis=0)
    data_monthly = data_monthly.to_frame()
    data_monthly['year'] = data_monthly.index.get_level_values('time').year
    data_monthly['month'] = data_monthly.index.get_level_values('time').month
    data_monthly = data_monthly.droplevel('time').set_index(['year', 'month'], append=True).squeeze()

    # add GCM mean as additional GCM
    data_montly_gcm_mean = data_monthly.groupby(['ssp', 'GHM', 'year', 'month']).mean().to_frame()
    data_montly_gcm_mean['GCM'] = 'gcm_mean'
    data_montly_gcm_mean = data_montly_gcm_mean.reset_index().set_index(data_monthly.index.names).squeeze()
    data_monthly = pd.concat([data_monthly, data_montly_gcm_mean], axis=0)

    # data_seasonally_gcm_mean = data_seasonally.groupby(['ssp', 'GHM', 'year', 'season']).mean().to_frame()
    # data_seasonally_gcm_mean['GCM'] = 'gcm_mean'
    # data_seasonally_gcm_mean = data_seasonally_gcm_mean.reset_index().set_index(data_seasonally.index.names).squeeze()
    # data_seasonally = pd.concat([data_seasonally, data_seasonally_gcm_mean], axis=0)

    return data_monthly#, data_seasonally


def evaluate_models(hist_simulated_monthly_, hist_observed_monthly_, plot=False):
    # following Wang et al. (2024), using R2, NSE, Pbias as evalutation metrics

    hist_simulated_monthly_ = hist_simulated_monthly_.unstack(['GCM', 'GHM']).loc['historical'].copy()
    hist_observed_monthly_ = hist_observed_monthly_.squeeze().to_frame()
    hist_observed_monthly_.columns = pd.MultiIndex.from_tuples([('observed', '')])
    merged = pd.merge(hist_simulated_monthly_, hist_observed_monthly_, left_index=True, right_index=True)
    metrics = (merged.corr()**2)['observed'].drop('observed').rename('R2').to_frame().sort_index()

    for (gcm, ghm) in merged.drop(columns='observed').columns:
        # drop any rows with NaN in either series
        df = merged[[('observed', ''), (gcm, ghm)]].dropna()
        obs = df[('observed', '')]
        sim = df[(gcm, ghm)]
        metrics.loc[(gcm, ghm), 'NSE'] = 1 - np.sum((sim - obs) ** 2) / np.sum((obs - obs.mean()) ** 2)
        metrics.loc[(gcm, ghm), 'Pbias (%)'] = 100 * np.sum(sim - obs) / np.sum(obs)

    metrics.index.names = ['GCM', 'GHM']

    if plot:
        fig, axs = plt.subplots(ncols=3, figsize=(12, 4.5), sharex=True, sharey=True)
        for ax, metric in zip(axs, metrics.columns):
            sns.heatmap(
                metrics.loc[:, metric].unstack('GHM'),
                annot=True,
                fmt='.2f',
                cmap='viridis',
                ax=ax,
                cbar_kws={'label': metric},
            )
            ax.set_ylabel('')
            ax.set_title(metric)
        axs[0].set_ylabel('GHM')
        plt.tight_layout()
        plt.show()
    return metrics


def plot_monthly_deviation(simulated_data_monthly_, selected_gcm_, selected_ghm_, plot_=False, ref_period_=None, future_period_=None):
    if ref_period_ is None:
        ref_period_ = np.arange(1999, 2019)
    if future_period_ is None:
        future_period_ = np.arange(2045, 2055)

    baseline = simulated_data_monthly_[simulated_data_monthly_.index.get_level_values('year').isin(ref_period_)].loc['historical']
    baseline = baseline.groupby(['GCM', 'GHM', 'month']).mean()
    baseline = baseline.xs(selected_ghm_, level='GHM').xs(selected_gcm_, level='GCM')

    scenario = simulated_data_monthly_[simulated_data_monthly_.index.get_level_values('year').isin(future_period_)]
    # scenario = scenario.groupby(['ssp', 'GCM', 'GHM', 'month']).mean()
    scenario = scenario.xs(selected_ghm_, level='GHM').xs(selected_gcm_, level='GCM')

    rel_change = (scenario.squeeze().div(baseline.squeeze(), axis=0) - 1) * 100
    rel_change_statistics = rel_change.groupby(['ssp', 'month']).describe()[['mean', 'std']]
    print(rel_change_statistics)

    seasons = {
        1: 'post-monsoon',
        2: 'pre-monsoon',
        3: 'pre-monsoon',
        4: 'pre-monsoon',
        5: 'monsoon',
        6: 'monsoon',
        7: 'monsoon',
        8: 'monsoon',
        9: 'monsoon',
        10: 'monsoon',
        11: 'post-monsoon',
        12: 'post-monsoon',
    }

    baseline_seasonally = baseline.to_frame().copy()
    baseline_seasonally['season'] = baseline_seasonally.index.get_level_values('month').map(seasons).values
    baseline_seasonally = baseline_seasonally.groupby(['season']).discharge.mean()

    scenario_seasonally = scenario.to_frame().copy()
    scenario_seasonally['season'] = scenario_seasonally.index.get_level_values('month').map(seasons).values
    scenario_seasonally = scenario_seasonally.groupby(['ssp', 'year', 'season']).discharge.mean()

    rel_change_seasonally = scenario_seasonally.div(baseline_seasonally, axis=0)
    rel_change_seasonally_statistics = rel_change_seasonally.groupby(['ssp', 'season']).describe()[['mean', 'std']]
    print(rel_change_seasonally_statistics)

    if plot_:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.pointplot(
            data=scenario.reset_index(),
            x="month",
            y="discharge",
            hue="ssp",
            errorbar="sd",
            dodge=0.2,
            linestyles="",
            estimator='mean',
            linewidth=1,
            ax=ax,
        )

        # now add baseline bars
        for m, (_, bl) in enumerate(baseline.squeeze().items()):
            ax.hlines(
                y=bl,
                xmin=m - 0.2,  # adjust length of bar
                xmax=m + 0.2,
                colors="black",
                linewidth=1,
            )


def load_station_data(station_data_path="/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/data/Hydropower/GRDC/Stung_Treng_Discharge-Monthly.nc"):
    observed_station_data = xr.open_dataset(station_data_path)
    station_coords_ = observed_station_data.geo_x.values.item(), observed_station_data.geo_y.values.item()
    observed_station_data = observed_station_data['runoff_mean'].to_dataframe().droplevel('id')
    observed_station_data['year'] = observed_station_data.index.get_level_values('time').year
    observed_station_data['month'] = observed_station_data.index.get_level_values('time').month
    observed_station_data = observed_station_data.reset_index().set_index(['year', 'month']).runoff_mean.rename('discharge')
    return observed_station_data, station_coords_


if __name__ == '__main__':
    station_data, station_coords = load_station_data()

    # station_coords = (105.75, 13.25)  # use for ISIMIP2b simulations
    # simulated_data_monthly, simulation_data_seasonally = load_isimip_data(os.path.join(script_path, "../../data/Hydropower/ISIMIP/KHM-discharge/ISIMIP2b"), station_coords)

    station_coords = (105.75, 13.75)  # use for ISIMIP3b simulations
    simulated_data_monthly = load_isimip_data(os.path.join(script_path, "../../data/Hydropower/ISIMIP/KHM-discharge/ISIMIP3b"), station_coords)

    # simulation_data_seasonally.to_csv(f"~/Desktop/tmp/simulation_data_seasonally_StungTreng_{station_coords[0]}-{station_coords[1]}.csv")
    # simulated_data_monthly.to_csv(f"~/Desktop/tmp/simulation_data_monthly_StungTreng_{station_coords[0]}-{station_coords[1]}.csv")
    model_performance = evaluate_models(simulated_data_monthly, station_data, True)

    selected_ghm = 'watergap2-2e'
    # selected_ghm = 'watergap2-2c'
    selected_gcm = 'gcm_mean'

    print('stop')
    # plot_result(result_seasonally)
    print('done')
