import json
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter
import seaborn as sns
import itertools
import statsmodels.api as sm
from matplotlib.transforms import blended_transform_factory
from sklearn.metrics import r2_score

def process_temperature_data(raw_data_path, output_path):
    # Load raw temperature data
    df = pd.read_csv(raw_data_path).rename(columns={'Category': 'year'}).set_index('year')

    df = df.rename(columns={'Hist. Ref. Period, 1950-2014': 'Historical'})

    df['Optimistic'] = df['SSP1-2.6 10-90th Percentile Range (low)'].rolling(window=10, center=True).mean()
    df['Pessimistic'] = df['SSP5-8.5 10-90th Percentile Range (high)'].rolling(window=10, center=True).mean()

    df['SSP1-2.6-rolling'] = pd.concat([df[df.index < 2015]['Historical'], df[df.index >= 2015]['SSP1-2.6']]).rolling(window=10, center=True).mean()
    df['SSP5-8.5-rolling'] = pd.concat([df[df.index < 2015]['Historical'], df[df.index >= 2015]['SSP5-8.5']]).rolling(window=10, center=True).mean()

    plot_range = (df.index >= 1970) & (df.index <= 2085)

    fig, axs = plt.subplots(nrows=1, figsize=(5.5, 3.5), sharex=True)
    axs = [axs]
    for scenario, color in zip(['Historical', 'SSP1-2.6', 'SSP5-8.5'], ['k', 'tab:blue', 'tab:red']):
        axs[0].plot(df.loc[plot_range].index, df.loc[plot_range, scenario], label=scenario, color=color, alpha=.25)
        axs[0].fill_between(df.loc[plot_range].index, df.loc[plot_range, scenario + ' 10-90th Percentile Range (low)'], df.loc[plot_range, scenario + ' 10-90th Percentile Range (high)'], color=color, alpha=0.1, lw=0)
    df.loc[simulation_range, 'Optimistic'].plot(ax=axs[0], label='Optimistic', color='tab:blue', linestyle='--')
    df.loc[simulation_range, 'Pessimistic'].plot(ax=axs[0], label='Pessimistic', color='tab:red', linestyle='--')
    # axs[0].plot([], [], color='k', linestyle='--', label='10-y rolling mean')
    axs[0].set_ylabel('Mean temperature (°C)')
    axs[0].legend(loc='upper left', frameon=False)
    axs[0].set_ylim((27, 31))

    # offset = (df.loc[2020, 'SSP1-2.6-rolling'] + df.loc[2020, 'SSP5-8.5-rolling']) / 2
    # ax2 = axs[0].twinx()
    # ylim_left = axs[0].get_ylim()
    # ax2.set_ylim([ylim_left[0] - offset, ylim_left[1] - offset])
    # ax2.set_ylabel("Temperature increase (°C)")
    # ax2.axhline(0, color='gray', linestyle='--', linewidth=0.8)

    x_pos = df.index[plot_range][-1] + 5
    for i, (scenario, color) in enumerate(zip(['Optimistic', 'Pessimistic'], ['tab:blue', 'tab:red'])):
        scenario_data = df.loc[simulation_range, scenario]
        increase = scenario_data.iloc[-1] - scenario_data.iloc[0]
        axs[0].vlines(x=x_pos, ymin=scenario_data.iloc[0], ymax=scenario_data.iloc[-1], color=color, linewidth=3)
        axs[0].text(x_pos + 1, scenario_data.iloc[[0, -1]].mean(), f"+{increase:.1f}", color=color, va='center', ha='left', fontsize=8)

    # drop x labels above the plot_range
    axs[0].set_xticks(axs[0].get_xticks()[(axs[0].get_xticks() <= df.index[plot_range][-1]) & (axs[0].get_xticks() >= df.index[plot_range][0])])

    axs[0].set_ylabel('Mean temperature (°C)')
    axs[0].set_xlabel('Year')
    axs[0].legend(loc='upper left', frameon=False)
    axs[0].set_ylim((27, 31))
    axs[0].set_xlim((axs[0].get_xlim()[0], axs[0].get_xlim()[1] + 5))

    plt.tight_layout()
    fig.savefig(os.path.join(output_path, 'temperature_projections_KHM.pdf'), dpi=300)

    temperature_change_to_base_year = (df - df.loc[2020])[['Historical', 'Optimistic', 'Pessimistic', 'SSP1-2.6-rolling', 'SSP5-8.5-rolling']]
    temperature_change_to_base_year.drop(columns='Historical').dropna(how='all').to_csv(os.path.join(output_path, 'temperature_change_to_2020.csv'))
    # for scenario, color in zip(['Historical', 'SSP1-2.6', 'SSP5-8.5'], ['k', 'tab:blue', 'tab:red']):
    #     axs[1].plot(temperature_change_to_base_year.index, temperature_change_to_base_year[scenario], label=scenario, color=color)
    # axs[1].set_ylabel('Temperature Change to 2020 (°C)')
    # axs[1].set_xlabel('Year')


def calculate_drr_impact_channel(temperature_increases_path, implementation_year=2031, implementation_duration=10, outpath=None):
    current_aal = 0.9290
    optimistic_aal_2050 = 1.0130
    pessimistic_aal_2050 = 2.9740

    tau = 10.91

    potential_ew_benefit = .097

    current_ew_coverage = 0.6923
    current_ew_lead_time = 7
    current_ew_benefits = potential_ew_benefit * current_ew_coverage * (1 - np.exp(-current_ew_lead_time / tau))

    perfect_ew_coverage = 1
    perfect_ew_lead_time = 12
    perfect_ew_benefits = potential_ew_benefit * perfect_ew_coverage * (1 - np.exp(-perfect_ew_lead_time / tau))

    temperature_increases = pd.read_csv(temperature_increases_path, index_col='year').loc[simulation_range]

    res = pd.DataFrame(index=simulation_range)
    res['Optimistic - Control'] = (temperature_increases / temperature_increases.loc[2050])['Optimistic'] * (optimistic_aal_2050 - current_aal) + current_aal
    res['Pessimistic - Control'] = (temperature_increases / temperature_increases.loc[2050])['Pessimistic'] * (pessimistic_aal_2050 - current_aal) + current_aal

    res['Optimistic - Status quo'] = res['Optimistic - Control'] * (1 - current_ew_benefits)
    res['Pessimistic - Status quo'] = res['Pessimistic - Control'] * (1 - current_ew_benefits)

    implementation_level = pd.Series(np.clip((res.index - (implementation_year - 1)) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
    res['Optimistic - Improvement'] = res['Optimistic - Control'] * (1 - (current_ew_benefits + implementation_level * (perfect_ew_benefits - current_ew_benefits)))
    res['Pessimistic - Improvement'] = res['Pessimistic - Control'] * (1 - (current_ew_benefits + implementation_level * (perfect_ew_benefits - current_ew_benefits)))

    res = res[['Optimistic - Control', 'Optimistic - Status quo', 'Optimistic - Improvement', 'Pessimistic - Control', 'Pessimistic - Status quo', 'Pessimistic - Improvement']]
    fig, ax = plt.subplots(figsize=(7, 3))
    for col in res.columns:
        ax.plot(res.index, res[col], label=col)
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual average flood damage\n(% national capital stock)')
    plt.tight_layout()

    res.columns = pd.MultiIndex.from_tuples([tuple(col.split(' - ')) for col in res.columns], names=['Climate scenario', 'Forecast scenario'])
    res = res.sort_index(axis=1, level='Climate scenario', sort_remaining=False)
    if outpath:
        fig.savefig(os.path.join(outpath, 'drr_impact_channel_KHM.pdf'), dpi=300)
        res.to_csv(os.path.join(outpath, 'drr_impact_channel_KHM.csv'))
        latex = res.to_latex(float_format="%.2f", index=True, header=True, na_rep="",
                             caption="Annual average flood damage (\% national capital stock).", label="tab:drr_impact_channel_KHM", multicolumn=True,
                             multicolumn_format='c')
        latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
        with open(os.path.join(outpath, "drr_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)



def calc_agri_impact_channel(temperature_increases_path, implementation_year=2031, implementation_duration=10, outpath=None):
    temperature_increases = pd.read_csv(temperature_increases_path, index_col='year')
    temperature_increases = temperature_increases[temperature_increases.index <= 2050]

    # values obtained from Roson and Sartori (2016) - values are relatie to the baseline with central year 1992
    productivity_loss_lookup = {
        0: 0.0,
        1: -2.51,
        2: -5.27,
        3: -8.2,
        4: -11.33,
        5: -14.66,
    }

    def get_productivity_loss(temp_increase, lookup_dict):
        if temp_increase < min(lookup_dict.keys()) or temp_increase > max(lookup_dict.keys()):
            raise ValueError("Temperature increase out of bounds for productivity loss lookup.")
        else:
            return np.interp(temp_increase, list(lookup_dict.keys()), list(lookup_dict.values())) / 100

    # translate productivity loss to values relative to 2020
    delta_t_since_1992 = (temperature_increases.loc[2020] - temperature_increases.loc[1992])[['SSP1-2.6-rolling', 'SSP5-8.5-rolling']].mean()

    productivity_increase_no_forecasts = 0
    productivity_increase_current_forecasts = 0.1034
    productivity_increase_perfect_forecasts = 0.1686

    res = pd.DataFrame(index=simulation_range)
    for scenario in ['Optimistic', 'Pessimistic']:
        temp_increase = temperature_increases.loc[res.index, scenario]
        productivity_loss = temp_increase.map(lambda x: (1 + get_productivity_loss(x + delta_t_since_1992, productivity_loss_lookup)) / (1 + get_productivity_loss(delta_t_since_1992, productivity_loss_lookup)) - 1)
        res[f'{scenario} - Control'] = productivity_loss
        res[f'{scenario} - Status quo'] = (1 + res[f'{scenario} - Control']) * (1 + productivity_increase_current_forecasts) - 1
        implementation_level = pd.Series(np.clip((res.index - (implementation_year - 1)) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
        res[f'{scenario} - Improvement'] = (1 + res[f'{scenario} - Control']) * (1 + productivity_increase_current_forecasts + implementation_level * (productivity_increase_perfect_forecasts - productivity_increase_current_forecasts)) - 1
    res *= 100  # convert to percentage
    res = res[['Optimistic - Control', 'Optimistic - Status quo', 'Optimistic - Improvement', 'Pessimistic - Control', 'Pessimistic - Status quo', 'Pessimistic - Improvement']]

    fig, ax = plt.subplots(figsize=(7, 3))
    for col in res.columns:
        ax.plot(res.index, res[col], label=col)
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel('Agricultural productivity\nchange  (%)')
    plt.tight_layout()

    res.columns = pd.MultiIndex.from_tuples([tuple(col.split(' - ')) for col in res.columns], names=['Climate scenario', 'Forecast scenario'])
    if outpath:
        fig.savefig(os.path.join(outpath, 'agri_impact_channel_KHM.pdf'), dpi=300)
        res.to_csv(os.path.join(outpath, 'agri_impact_channel_KHM.csv'))
        latex = res.to_latex(float_format="%.2f", index=True, header=True,
                     na_rep="", caption="Agricultural productivity change (\%).", label="tab:agri_impact_channel_KHM", multicolumn=True,
                             multicolumn_format='c',
        )
        latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
        with open(os.path.join(outpath, "agri_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)


def prepare_hydropower_channel(hydropower_input_data_path_, temperature_increases_path, implementation_year, implementation_duration, outpath=None, seasonally=True, weighted=False):
    seasons_mapping = {
        1: 'Post-monsoon',
        2: 'Pre-monsoon',
        3: 'Pre-monsoon',
        4: 'Pre-monsoon',
        5: 'Monsoon',
        6: 'Monsoon',
        7: 'Monsoon',
        8: 'Monsoon',
        9: 'Monsoon',
        10: 'Monsoon',
        11: 'Post-monsoon',
        12: 'Post-monsoon',
    }

    costs = pd.read_csv(os.path.join(hydropower_input_data_path_, "monthly", "syscost_m.csv"))
    costs = costs.rename(columns={'Ensemble mean': 'Ensemble Mean'})
    costs['Month'] = costs['Date'].apply(lambda x: x.split('-')[0]).map({'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12})
    costs['Year'] = costs['Date'].apply(lambda x: x.split('-')[1])
    costs['Season'] = costs['Month'].map(seasons_mapping)
    costs = costs.set_index(['Year', 'Month']).drop(columns=['Date']).sort_index()

    scenario_col_mapping = {
        'Control': ['No forecast'],
        'Improvement': ['No forecast', 'Perfect', 'Ensemble Mean'],
    }
    costs = pd.concat([costs[cols].stack().groupby(['Year', 'Month']).min().squeeze().rename(scenario_name) for scenario_name, cols in scenario_col_mapping.items()], axis=1)
    costs = costs.groupby('Year').sum()
    forecast_benefit = (1 - costs['Improvement'] / costs['Control']) * 100
    forecast_benefit = forecast_benefit.rename('cost_reduction')
    print(f"Average cost reduction: {forecast_benefit.mean():.2}%")

    discharge = pd.read_csv(os.path.join(hydropower_input_data_path_, "monthly", "Q_m_avg.csv"))
    discharge['Month'] = discharge['Date'].apply(lambda x: x.split('-')[0]).map({'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12})
    discharge['Year'] = discharge['Date'].apply(lambda x: x.split('-')[1])
    discharge = discharge.set_index(['Month', 'Year']).drop(columns=['Date']).squeeze().unstack('Month').dropna()

    # monthly changes in (2070 - 2099) from baseline (1991 - 2020) from Wang et al. (2024)
    monthly_changes = {
        'Optimistic': {1: 0.042, 2: 0.015, 3: 0.001, 4: 0.04, 5: -0.025, 6: -0.061, 7: 0.014, 8: 0.107, 9: 0.012, 10: 0.035, 11: 0.074, 12: 0.049},
        'Pessimistic': {1: 0.084, 2: 0.021, 3: 0.011, 4: -0.09, 5: -0.188, 6: -0.168, 7: 0.068, 8: 0.053, 9: 0.011, 10: 0.105, 11: 0.174, 12: 0.098}
    }

    seasonal_changes = discharge.mean().rename('baseline').to_frame()
    seasonal_changes['Season'] = seasonal_changes.index.map(seasons_mapping)
    seasonal_changes['Optimistic'] = seasonal_changes['baseline'] * (1 + seasonal_changes.index.map(monthly_changes['Optimistic']))
    seasonal_changes['Pessimistic'] = seasonal_changes['baseline'] * (1 + seasonal_changes.index.map(monthly_changes['Pessimistic']))
    seasonal_changes = seasonal_changes.groupby('Season').mean()
    seasonal_changes = (seasonal_changes[['Optimistic', 'Pessimistic']].div(seasonal_changes['baseline'], axis=0) - 1).to_dict()

    def find_best_subset(data_points, target_coords, min_points=1, max_points=None, weights=None):
        n = data_points.shape[0]
        if max_points is None:
            max_points = n
        best_err = float("inf")
        best_subset = None
        for r in range(min_points, max_points + 1):
            for idx in itertools.combinations(range(n), r):
                mean_vals = data_points.iloc[list(idx)].mean().values
                if weights is None:
                    rmse = np.sqrt(np.sum((mean_vals - np.array(target_coords)) ** 2) / len(target_coords))
                else:
                    rmse = np.sqrt(np.sum((weights * (mean_vals - np.array(target_coords)) ** 2)) / np.sum(weights))
                if rmse < best_err:
                    best_err = rmse
                    best_subset = idx
        return best_subset, best_err

    best_fit_result = {}
    if not seasonally:
        target_change_rates = monthly_changes
    else:
        target_change_rates = seasonal_changes

    if seasonally:
        fit_on = ['Pre-monsoon', 'Monsoon', 'Post-monsoon']
        discharge = discharge.rename(columns=seasons_mapping).stack().groupby(['Year', 'Month']).mean().unstack('Month')[fit_on]
    else:
        fit_on = np.arange(1, 13)

    discharge_deviation = discharge / discharge.mean() - 1

    merged = pd.concat([discharge_deviation, forecast_benefit], axis=1)
    print("Correlation matrix:")
    print(merged.corr())

    r2_scores = {}
    for col in merged.columns[:-1]:
        X = sm.add_constant(merged[col])
        model = sm.OLS(merged['cost_reduction'], X).fit()
        r2_scores[col] = model.rsquared

    # regression model
    X = merged.iloc[:, :-1]
    Y = merged.iloc[:, -1]
    X = sm.add_constant(X)
    ols_model = sm.OLS(Y, X)
    ols_result = ols_model.fit()
    print(ols_result.summary())

    for climate_scenario, change_rates in target_change_rates.items():
        target = [(1 + change_rates[s]) * discharge[s].mean() for s in fit_on]
        weights = np.array([r2_scores[col] for col in fit_on]) if weighted else None
        subset, err = find_best_subset(discharge[fit_on], target, 1, weights=weights)
        years = list(discharge.index[list(subset)])
        # selected_years_avg_cost_red = (1 - costs.loc[years].mean()['Improvement'] / costs.loc[years].mean()['Control']) * 100
        selected_years_avg_cost_red = forecast_benefit.loc[years].mean()
        print(f"## {climate_scenario} ## selected years: {years}, RMSE: {err}, average forecast benefit: {selected_years_avg_cost_red}")
        print(f"Target mean: {target}, subset mean: {discharge[fit_on].loc[years].mean().values}")
        best_fit_result[climate_scenario] = {
            'subset': years,
            'RMSE': err,
            'cost_reduction': selected_years_avg_cost_red,
            'mean_shift': (discharge.loc[years, fit_on].mean() / discharge[fit_on].mean() - 1).to_dict()
        }
    with open(os.path.join(outpath, f'best_fit_result_{"+".join(fit_on)}.json'), 'w') as f:
        json.dump(best_fit_result, f, indent=2)

    # fig, axs = plt.subplots(ncols=3, nrows=4 if period=='monthly' else 1, figsize=(12, 14 if period == 'monthly' else 3.5), sharey=True)
    fig, axs = plt.subplots(ncols=2, nrows=2, figsize=(6, 6), sharey=True)
    axs = axs.flatten()
    handles, labels = [], []
    for ax, col in zip(axs, merged.columns[:-1]):
        # ax.scatter(merged[col], merged['cost_reduction'], facecolors='k', alpha=.8, s=30, edgecolors='none')
        ax.set_xlabel(col)
        sns.regplot(x=merged[col], y=merged['cost_reduction'], ax=ax, scatter_kws={'s': 20, 'alpha': .5, 'edgecolor': 'none'}, line_kws={'alpha': .5, 'linewidth': .8}, label='Full sample' if ax == axs[0] else '__none__')
        # for x, y, text in zip(merged[col], merged['cost_reduction'], merged.reset_index()['Year']):
        #     ax.text(x, y, str(text), fontsize=7, alpha=0.5, ha='center', va='bottom')
        ax.set_ylabel('')
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1))
        ax.text(.01, .99, f"R2={r2_scores[col]:.2f}", ha='left', va='top', transform=ax.transAxes)

        # full_sample_mean_discharge_deviation = (discharge.mean() / discharge.mean()).loc[col] - 1
        full_sample_mean_cost_reduction = (1 - costs.mean()['Improvement'] / costs.mean()['Control']) * 100
        ax.scatter(0, full_sample_mean_cost_reduction, color='blue', s=100, marker='x', zorder=10, label='__none__')
        # ax.axhline(full_sample_mean_cost_reduction, color='blue', linestyle='--', linewidth=0.8)
        if col in fit_on:
            ax.axvline(target_change_rates['Optimistic'][col], color='orange', linestyle='--', linewidth=0.8, label='__none__')
            ax.text(target_change_rates['Optimistic'][col], 0.01, f"{'  +' if target_change_rates['Optimistic'][col] > 0 else '  '}{target_change_rates['Optimistic'][col] * 100:.1f}%  ", ha='left' if target_change_rates['Optimistic'][col] > target_change_rates['Pessimistic'][col] else 'right', va='bottom', fontsize=7, color='orange', transform=blended_transform_factory(ax.transData, ax.transAxes))
            ax.scatter(merged[col].loc[best_fit_result['Optimistic']['subset']].values, merged['cost_reduction'].loc[best_fit_result['Optimistic']['subset']].values, color='orange', s=50, facecolors='none', label='__none__')
            ax.axvline(target_change_rates['Pessimistic'][col], color='red', linestyle='--', linewidth=0.8, label='__none__')
            ax.text(target_change_rates['Pessimistic'][col], 0.01, f"{'  +' if target_change_rates['Pessimistic'][col] > 0 else '  '}{target_change_rates['Pessimistic'][col] * 100:.1f}%  ", ha='right' if target_change_rates['Optimistic'][col] > target_change_rates['Pessimistic'][col] else 'left', va='bottom', fontsize=7, color='red', transform=blended_transform_factory(ax.transData, ax.transAxes))
            ax.scatter(merged[col].loc[best_fit_result['Pessimistic']['subset']].values, merged['cost_reduction'].loc[best_fit_result['Pessimistic']['subset']].values, color='red', s=100, facecolors='none', label='__none__')
            ax.axvline(target_change_rates['Pessimistic'][col], color='red', linestyle='--', linewidth=0.8, label='__none__')
            ax.scatter(best_fit_result['Optimistic']['mean_shift'][col], best_fit_result['Optimistic']['cost_reduction'], color='orange', s=100, marker='x', zorder=10, label='__none__')
            ax.scatter(best_fit_result['Pessimistic']['mean_shift'][col], best_fit_result['Pessimistic']['cost_reduction'], color='red', s=100, marker='x', zorder=10, label='__none__')
        ax_handles, ax_labels = ax.get_legend_handles_labels()
        handles.extend(ax_handles)
        labels.extend(ax_labels)
    # fig.text('Cost reduction (%)')
    handles.extend([
        Line2D([0], [0], marker='o', linestyle='None', markersize=8, markeredgecolor='orange', markerfacecolor='none'),
        Line2D([0], [0], marker='o', linestyle='None', markersize=10, markeredgecolor='red', markerfacecolor='none'),
        Line2D([0], [0], marker='x', color='black', linestyle='None', markersize=8),
        Line2D([0], [0], color='black', linestyle='--', linewidth=0.8),
    ])
    labels.extend(['Optimistic sample', 'Pessimistic sample', 'Sample means', 'Projected discharge change'])
    axs[-1].legend(handles=handles, labels=labels, loc='upper left', bbox_to_anchor=(0, 1), frameon=False)
    axs[-1].axis('off')
    fig.tight_layout()
    if outpath is not None:
        fig.savefig(os.path.join(outpath, f'hydropower_cc_year_selection_{"+".join(fit_on)}.pdf'), dpi=300)

    temperature_increases = pd.read_csv(temperature_increases_path, index_col='year')
    current_potential_benefit = forecast_benefit.mean()
    rel_temp_change = temperature_increases / temperature_increases.loc[2085]
    rel_temp_change = rel_temp_change[rel_temp_change.index <= 2050]

    res = pd.DataFrame(index=simulation_range)
    res[f'Control / Status quo'] = 0
    for scenario in ['Optimistic', 'Pessimistic']:
        implementation_level = pd.Series(np.clip((res.index - (implementation_year - 1)) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
        res[f'{scenario} - Improvement'] = ((current_potential_benefit + (best_fit_result[scenario]['cost_reduction'] - current_potential_benefit) * rel_temp_change[scenario]) * implementation_level).loc[simulation_range]
    res = res[['Control / Status quo', 'Optimistic - Improvement', 'Pessimistic - Improvement']]

    fig, ax = plt.subplots(figsize=(7, 3))
    for col in res.columns:
        ax.plot(res.index, res[col], label=col)
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel('Electricity generation\ncost reduction (%)')
    plt.tight_layout()

    res = res.rename(columns={'Control / Status quo': ' - Control / Status quo'})
    res.columns = pd.MultiIndex.from_tuples([tuple(col.split(' - ')) for col in res.columns], names=['Climate scenario', 'Forecast scenario'])
    if outpath:
        fig.savefig(os.path.join(outpath, 'hydropower_impact_channel_KHM.pdf'), dpi=300)
        res.to_csv(os.path.join(outpath, 'hydropower_impact_channel_KHM.csv'))
        latex = res.to_latex(float_format="%.2f", index=True, header=True,
                     na_rep="", caption="Electricity generation\ncost reduction (\%).", label="tab:hydropower_impact_channel_KHM", multicolumn=True,
                             multicolumn_format='c',
        )
        latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
        with open(os.path.join(outpath, "hydropower_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)

if __name__ == "__main__":
    simulation_range = np.arange(2020, 2051)
    temperature_data_path = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/data/Temperature/projected-average-mean-s.csv"
    temperature_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Temperature/"
    process_temperature_data(temperature_data_path, temperature_outpath)
    temperature_change_path = os.path.join(temperature_outpath, 'temperature_change_to_2020.csv')

    drr_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/DRR/"
    calculate_drr_impact_channel(temperature_change_path, implementation_year=2021, implementation_duration=30, outpath=drr_outpath)

    agri_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Agriculture/"
    calc_agri_impact_channel(temperature_change_path, implementation_year=2021, implementation_duration=30, outpath=agri_outpath)

    hydropower_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Hydropower/"
    hydropower_input_data_path = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/data/Hydropower/Koh_Galelli"
    # prepare_hydropower_channel(hydropower_input_data_path_=hydropower_input_data_path, fit_on_=['Pre-monsoon', 'Monsoon', 'Post-monsoon'], outpath_=hydropower_outpath)
    # prepare_hydropower_channel(hydropower_input_data_path_=hydropower_input_data_path, fit_on_=['Monsoon'], outpath_=hydropower_outpath)
    prepare_hydropower_channel(hydropower_input_data_path_=hydropower_input_data_path, temperature_increases_path=temperature_change_path, implementation_year=2021, implementation_duration=30, outpath=hydropower_outpath)

