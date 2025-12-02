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

script_dir = os.path.dirname(os.path.realpath(__file__))


def process_temperature_data(raw_temperatures_data_path_, temperature_outpath_, paper_outpath_):
    df = pd.read_csv(raw_temperatures_data_path_).rename(columns={'Category': 'year'}).set_index('year')

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

    os.makedirs(temperature_outpath_, exist_ok=True)

    plt.tight_layout()
    fig.savefig(os.path.join(temperature_outpath_, 'temperature_projections_KHM.pdf'), dpi=300)
    fig.savefig(os.path.join(paper_outpath_, 'figures/temperature_projections_KHM.pdf'), dpi=300)

    temperature_change_to_base_year = (df - df.loc[2020])[['Historical', 'Optimistic', 'Pessimistic', 'SSP1-2.6-rolling', 'SSP5-8.5-rolling']]
    temperature_change_to_base_year.drop(columns='Historical').dropna(how='all').to_csv(os.path.join(temperature_outpath_, 'temperature_change_to_2020.csv'))


def calculate_drr_impact_channel(drr_outpath_, paper_outpath_, temperature_path_, implementation_year_=2031, implementation_duration_=10):
    current_aal = 0.9290
    optimistic_aal_2050 = 1.0130
    pessimistic_aal_2050 = 2.9740

    tau = 10.91

    potential_ew_benefit = .097

    current_ew_coverage = 0.6923
    current_ew_lead_time = 7
    current_ew_benefits = potential_ew_benefit * current_ew_coverage * (1 - np.exp(-current_ew_lead_time / tau))

    future_ew_coverage = 1

    status_quo_future_benefits = potential_ew_benefit * future_ew_coverage * (1 - np.exp(-current_ew_lead_time / tau))

    improvement_future_lead_time = 12
    improvement_future_benefits = potential_ew_benefit * future_ew_coverage * (1 - np.exp(-improvement_future_lead_time / tau))

    print(f"Current EW benefits: {current_ew_benefits * 100:.2f}%, Status quo benefits (2050): {status_quo_future_benefits * 100:.2f}%, Improvement benefits (2050): {improvement_future_benefits * 100:.2f}%")

    temperature_increases = pd.read_csv(temperature_path_, index_col='year').loc[simulation_range]

    res = pd.DataFrame(index=simulation_range)
    res.index.name = 'Year'
    res['Optimistic - Control'] = (temperature_increases / temperature_increases.loc[2050])['Optimistic'] * (optimistic_aal_2050 - current_aal) + current_aal
    res['Pessimistic - Control'] = (temperature_increases / temperature_increases.loc[2050])['Pessimistic'] * (pessimistic_aal_2050 - current_aal) + current_aal

    implementation_level = pd.Series(np.clip((res.index - (implementation_year_ - 1)) / implementation_duration_, 0, 1), index=res.index, name='implementation_level')
    res['Optimistic - Status quo'] = res['Optimistic - Control'] * (1 - (current_ew_benefits + (status_quo_future_benefits - current_ew_benefits) * implementation_level))
    res['Pessimistic - Status quo'] = res['Pessimistic - Control'] * (1 - (current_ew_benefits + (status_quo_future_benefits - current_ew_benefits) * implementation_level))
    res['Optimistic - Improvement'] = res['Optimistic - Control'] * (1 - (current_ew_benefits + (improvement_future_benefits - current_ew_benefits) * implementation_level))
    res['Pessimistic - Improvement'] = res['Pessimistic - Control'] * (1 - (current_ew_benefits + (improvement_future_benefits - current_ew_benefits) * implementation_level))

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

    os.makedirs(drr_outpath_, exist_ok=True)

    fig.savefig(os.path.join(drr_outpath_, 'drr_impact_channel_KHM.pdf'), dpi=300)
    fig.savefig(os.path.join(paper_outpath_, 'figures/drr_impact_channel_KHM.pdf'), dpi=300)

    csv_outfile = os.path.join(drr_outpath_, 'drr_impact_channel_KHM.csv')
    with open(csv_outfile, 'w') as f:
        f.write("values denote the percentage of total national capital stock destroyed through floods \n")
        f.write(" \n")
        res.to_csv(f)


        latex = res.to_latex(
            float_format="%.2f",
            index=True,
            header=True,
            na_rep="",
            caption="Annual average flood damage (\% national capital stock).",
            label="tab:drr_impact_channel_KHM",
            multicolumn=True,
            multicolumn_format='c'
        )
        latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
        with open(os.path.join(drr_outpath_, "drr_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)
        with open(os.path.join(paper_outpath_, "tables/drr_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)



def calc_agri_impact_channel(agri_outpath_, paper_outpath_, temperature_increases_path_, implementation_year_=2031, implementation_duration_=10):
    temperature_increases = pd.read_csv(temperature_increases_path_, index_col='year')
    temperature_increases = temperature_increases[temperature_increases.index <= 2050]

    # values obtained from Roson and Sartori (2016) - values are relative to the baseline with central year 1992
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
    res.index.name = 'Year'
    for scenario in ['Optimistic', 'Pessimistic']:
        temp_increase = temperature_increases.loc[res.index, scenario]
        productivity_loss = temp_increase.map(lambda x: (1 + get_productivity_loss(x + delta_t_since_1992, productivity_loss_lookup)) / (1 + get_productivity_loss(delta_t_since_1992, productivity_loss_lookup)) - 1)
        res[f'{scenario} - Control'] = productivity_loss
        implementation_level = pd.Series(np.clip((res.index - (implementation_year_ - 1)) / implementation_duration_, 0, 1), index=res.index, name='implementation_level')
        res[f'{scenario} - Status quo'] = (1 + res[f'{scenario} - Control']) * (1 + productivity_increase_current_forecasts * implementation_level) - 1
        res[f'{scenario} - Improvement'] = (1 + res[f'{scenario} - Control']) * (1 + productivity_increase_perfect_forecasts * implementation_level) - 1
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

    os.makedirs(agri_outpath_, exist_ok=True)

    fig.savefig(os.path.join(agri_outpath_, 'agri_impact_channel_KHM.pdf'), dpi=300)
    fig.savefig(os.path.join(paper_outpath_, 'figures/agri_impact_channel_KHM.pdf'), dpi=300)

    csv_outfile = os.path.join(agri_outpath_, 'agri_impact_channel_KHM.csv')
    with open(csv_outfile, 'w') as f:
        f.write("values are the agricultural productivity change w.r.t. the 2020 control level in percent\n")
        f.write(" \n")
        res.to_csv(f)

        latex = res.to_latex(float_format="%.2f", index=True, header=True,
                     na_rep="", caption="Agricultural productivity change (\%).", label="tab:agri_impact_channel_KHM", multicolumn=True,
                             multicolumn_format='c',
        )
        latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
        with open(os.path.join(agri_outpath_, "agri_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)
        with open(os.path.join(paper_outpath_, "tables/agri_impact_channel_KHM.tex"), 'w') as f:
            f.write(latex)


def prepare_hydropower_channel(hydropower_outpath_, paper_outpath_, hydropower_input_data_path_, temperature_increases_path_, implementation_year_, implementation_duration_, seasonally=True, weighted=False):
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
        'Status quo': ['No forecast', 'Ensemble Mean'],
        'Control': ['No forecast'],
        'Improvement': ['No forecast', 'Perfect', 'Ensemble Mean'],
    }
    costs = pd.concat([costs[cols].stack().groupby(['Year', 'Month']).min().squeeze().rename(scenario_name) for scenario_name, cols in scenario_col_mapping.items()], axis=1)
    costs = costs.groupby('Year').sum()
    forecast_benefit = (1 - costs[['Status quo', 'Improvement']].div(costs['Control'], axis=0)) * 100
    print(f"Average cost reduction: {forecast_benefit.mean().loc['Status quo']:.2}% (status quo) / {forecast_benefit.mean().loc['Improvement']:.2}% (improvement)")
    forecast_benefit.columns = [f"cost reduction - {c}" for c in forecast_benefit.columns]

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

    r2_scores = pd.DataFrame(columns=['Status quo', 'Improvement'], index=merged.columns[:-2])
    for climate_sc in ['Status quo', 'Improvement']:
        for season in merged.columns[:-2]:
            X = sm.add_constant(merged[season])
            model = sm.OLS(merged[f'cost reduction - {climate_sc}'], X).fit()
            r2_scores.loc[season, climate_sc] = model.rsquared
        # regression model
        X = merged.iloc[:, :-2]
        Y = merged[f'cost reduction - {climate_sc}']
        X = sm.add_constant(X)
        ols_model = sm.OLS(Y, X)
        ols_result = ols_model.fit()
        print(ols_result.summary())

    for climate_scenario, change_rates in target_change_rates.items():
        target = [(1 + change_rates[s]) * discharge[s].mean() for s in fit_on]
        weights = np.array([r2_scores[col] for col in fit_on]) if weighted else None
        subset, err = find_best_subset(discharge[fit_on], target, 1, weights=weights)
        years = list(discharge.index[list(subset)])
        selected_years_avg_cost_red = forecast_benefit.loc[years].mean()
        print(f"## {climate_scenario} ## selected years: {years}, RMSE: {err}, average forecast benefit: {selected_years_avg_cost_red}")
        print(f"Target mean: {target}, subset mean: {discharge[fit_on].loc[years].mean().values}")
        best_fit_result[climate_scenario] = {
            'subset': years,
            'RMSE': err,
            'cost_reduction': {sc: selected_years_avg_cost_red[f"cost reduction - {sc}"] for sc in ['Status quo', 'Improvement']},
            'mean_shift': (discharge.loc[years, fit_on].mean() / discharge[fit_on].mean() - 1).to_dict()
        }

    os.makedirs(hydropower_outpath_, exist_ok=True)

    with open(os.path.join(hydropower_outpath_, f'best_fit_result_{"+".join(fit_on)}.json'), 'w') as f:
        json.dump(best_fit_result, f, indent=2)

    plot_scenario = 'Improvement'
    fig, axs = plt.subplots(ncols=2, nrows=2, figsize=(6, 6), sharey=True)
    handles, labels = [], []
    for ax, season in zip(axs.flatten(), merged.columns[:-2]):
        ax.set_xlabel(season)
        sns.regplot(x=merged[season], y=merged[f'cost reduction - {plot_scenario}'], ax=ax, scatter_kws={'s': 20, 'alpha': .5, 'edgecolor': 'none'}, line_kws={'alpha': .5, 'linewidth': .8}, label='Full sample' if ax == axs[0, 0] else '__none__')
        ax.set_ylabel('')
        ax.xaxis.set_major_formatter(PercentFormatter(xmax=1))
        ax.text(.01, .99, f"R2={r2_scores.loc[season, plot_scenario]:.2f}", ha='left', va='top', transform=ax.transAxes)

        full_sample_mean_cost_reduction = (1 - costs.mean()['Improvement'] / costs.mean()['Control']) * 100
        ax.scatter(0, full_sample_mean_cost_reduction, color='blue', s=100, marker='x', zorder=10, label='__none__')
        if season in fit_on:
            ax.axvline(target_change_rates['Optimistic'][season], color='orange', linestyle='--', linewidth=0.8, label='__none__')
            ax.text(target_change_rates['Optimistic'][season], 0.01, f"{'  +' if target_change_rates['Optimistic'][season] > 0 else '  '}{target_change_rates['Optimistic'][season] * 100:.1f}%  ", ha='left' if target_change_rates['Optimistic'][season] > target_change_rates['Pessimistic'][season] else 'right', va='bottom', fontsize=7, color='orange', transform=blended_transform_factory(ax.transData, ax.transAxes))
            ax.scatter(merged[season].loc[best_fit_result['Optimistic']['subset']].values, merged[f'cost reduction - {plot_scenario}'].loc[best_fit_result['Optimistic']['subset']].values, color='orange', s=50, facecolors='none', label='__none__')
            ax.axvline(target_change_rates['Pessimistic'][season], color='red', linestyle='--', linewidth=0.8, label='__none__')
            ax.text(target_change_rates['Pessimistic'][season], 0.01, f"{'  +' if target_change_rates['Pessimistic'][season] > 0 else '  '}{target_change_rates['Pessimistic'][season] * 100:.1f}%  ", ha='right' if target_change_rates['Optimistic'][season] > target_change_rates['Pessimistic'][season] else 'left', va='bottom', fontsize=7, color='red', transform=blended_transform_factory(ax.transData, ax.transAxes))
            ax.scatter(merged[season].loc[best_fit_result['Pessimistic']['subset']].values, merged[f'cost reduction - {plot_scenario}'].loc[best_fit_result['Pessimistic']['subset']].values, color='red', s=100, facecolors='none', label='__none__')
            ax.axvline(target_change_rates['Pessimistic'][season], color='red', linestyle='--', linewidth=0.8, label='__none__')
            ax.scatter(best_fit_result['Optimistic']['mean_shift'][season], best_fit_result['Optimistic']['cost_reduction'][plot_scenario], color='orange', s=100, marker='x', zorder=10, label='__none__')
            ax.scatter(best_fit_result['Pessimistic']['mean_shift'][season], best_fit_result['Pessimistic']['cost_reduction'][plot_scenario], color='red', s=100, marker='x', zorder=10, label='__none__')
        ax_handles, ax_labels = ax.get_legend_handles_labels()
        handles.extend(ax_handles)
        labels.extend(ax_labels)
    handles.extend([
        Line2D([0], [0], marker='o', linestyle='None', markersize=8, markeredgecolor='orange', markerfacecolor='none'),
        Line2D([0], [0], marker='o', linestyle='None', markersize=10, markeredgecolor='red', markerfacecolor='none'),
        Line2D([0], [0], marker='x', color='black', linestyle='None', markersize=8),
        Line2D([0], [0], color='black', linestyle='--', linewidth=0.8),
    ])
    for ax in axs[:, 0]:
        ax.set_ylabel(f"Cost reduction - {plot_scenario} [%]")
    labels.extend(['Optimistic sample', 'Pessimistic sample', 'Sample means', 'Projected discharge change'])
    axs[-1, -1].legend(handles=handles, labels=labels, loc='upper left', bbox_to_anchor=(0, 1), frameon=False)
    axs[-1, -1].axis('off')
    fig.tight_layout()
    fig.savefig(os.path.join(hydropower_outpath_, f'hydropower_cc_year_selection.pdf'), dpi=300)
    fig.savefig(os.path.join(paper_outpath_, f'figures/hydropower_cc_year_selection.pdf'), dpi=300)

    temperature_increases = pd.read_csv(temperature_increases_path_, index_col='year')
    current_potential_benefit = forecast_benefit.mean()
    rel_temp_change = temperature_increases / temperature_increases.loc[2085]
    rel_temp_change = rel_temp_change[rel_temp_change.index <= 2050]

    res = pd.DataFrame(index=simulation_range)
    res.index.name = 'Year'
    res[f'Optimistic / Pessimistic - Control'] = 0
    for climate_sc in ['Optimistic', 'Pessimistic']:
        implementation_level = pd.Series(np.clip((res.index - (implementation_year_ - 1)) / implementation_duration_, 0, 1), index=res.index, name='implementation_level')
        for fc_sc in ['Status quo', 'Improvement']:
            res[f'{climate_sc} - {fc_sc}'] = ((current_potential_benefit[f'cost reduction - {fc_sc}'] + (best_fit_result[climate_sc]['cost_reduction'][fc_sc] - current_potential_benefit[f'cost reduction - {fc_sc}']) * rel_temp_change[climate_sc]) * implementation_level).loc[simulation_range]
    res = res[['Optimistic / Pessimistic - Control', 'Optimistic - Status quo', 'Optimistic - Improvement', 'Pessimistic - Status quo', 'Pessimistic - Improvement']]

    fig, ax = plt.subplots(figsize=(7, 3))
    for col in res.columns:
        ax.plot(res.index, res[col], label=col)
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel('Electricity generation\ncost reduction (%)')
    plt.tight_layout()

    res = res.rename(columns={'Control / Status quo': ' - Control / Status quo'})
    res.columns = pd.MultiIndex.from_tuples([tuple(col.split(' - ')) for col in res.columns], names=['Climate scenario', 'Forecast scenario'])
    fig.savefig(os.path.join(hydropower_outpath_, 'hydropower_impact_channel_KHM.pdf'), dpi=300)
    fig.savefig(os.path.join(paper_outpath_, 'figures/hydropower_impact_channel_KHM.pdf'), dpi=300)

    csv_outfile = os.path.join(hydropower_outpath_, 'hydropower_impact_channel_KHM.csv')
    with open(csv_outfile, 'w') as f:
        f.write("values are percent cost reductions of electricity generation cost in comparison to the control scenario\n")
        f.write(" \n")
        res.to_csv(f)

    latex = res.to_latex(
        float_format="%.2f",
        index=True,
        header=True,
        na_rep="",
        caption="Electricity generation\ncost reduction (\%).",
        label="tab:hydropower_impact_channel_KHM",
        multicolumn=True,
        multicolumn_format='c'
    )
    latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
    with open(os.path.join(hydropower_outpath_, "hydropower_impact_channel_KHM.tex"), 'w') as f:
        f.write(latex)
    with open(os.path.join(paper_outpath_, "tables/hydropower_impact_channel_KHM.tex"), 'w') as f:
        f.write(latex)


def generate_costs(costs_outpath_, paper_outpath_, opex_status_quo_=500_000., opex_improvement_=1_000_000., capex_improvement_=21_000_000., capex_improvement_duration_=5, capex_improvement_start_=2031):
    res = pd.DataFrame(
        data=0,
        index=simulation_range, columns=pd.MultiIndex.from_product(
            iterables=[['OPEX', 'CAPEX'], ['Optimistic', 'Pessimistic'], ['Control', 'Status quo', 'Improvement']],
            names=['Cost type', 'Climate scenario', 'Forecast scenario'],
        )
    )
    res.index.name = 'Year'

    res.loc[:, pd.IndexSlice['OPEX', :, 'Status quo']] = opex_status_quo_
    res.loc[:, pd.IndexSlice['OPEX', :, 'Improvement']] = opex_improvement_
    res.loc[np.arange(capex_improvement_start_, capex_improvement_start_ + capex_improvement_duration_), pd.IndexSlice['CAPEX', :, 'Improvement']] = capex_improvement_ / capex_improvement_duration_

    table_reduced = pd.DataFrame(
        data=0,
        columns=['OPEX', 'CAPEX'],
        index=pd.Index(['Control', 'Status quo', 'Improvement'], name='Forecast scenario'),
        dtype=str,
    )
    table_reduced.loc['Status quo', 'OPEX'] = f"{opex_status_quo_ / 1e6:.1f} p.a."
    table_reduced.loc['Improvement', 'OPEX'] = f"{opex_improvement_ / 1e6:.1f} p.a."
    table_reduced.loc['Improvement', 'CAPEX'] = f"{capex_improvement_ / capex_improvement_duration_ / 1e6:.1f} p.a. ({capex_improvement_start_}--{capex_improvement_start_ + capex_improvement_duration_ - 1})"

    os.makedirs(costs_outpath_, exist_ok=True)

    csv_outfile = os.path.join(costs_outpath_, 'scenario_costs_KHM.csv')
    with open(csv_outfile, 'w') as f:
        f.write("All values in 2025 USD\n")
        f.write(" \n")
        res.to_csv(f)
    latex_reduced = table_reduced.reset_index().to_latex(
        index=False,
        header=True,
        na_rep="",
        caption="Scenario costs (m~USD, 2025 net present value).",
        label="tab:scenario_costs_KHM",
        multicolumn=True,
        multicolumn_format='c'
    )
    latex_reduced = latex_reduced.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
    with open(os.path.join(costs_outpath_, "scenario_costs_KHM.tex"), 'w') as f:
        f.write(latex_reduced)
    with open(os.path.join(paper_outpath_, "tables/scenario_costs_KHM.tex"), 'w') as f:
        f.write(latex_reduced)


def combine_tables(table_paths, outpath_):
    with pd.ExcelWriter(outpath_, engine='openpyxl') as writer:
        for sheet_name, (file, num_header_rows) in table_paths.items():
            with open(file, "r") as f:
                meta_df = pd.DataFrame({'Info:': [f.readlines()[0].strip(), '']}).T
            df = pd.read_csv(file, header=list(np.arange(1, num_header_rows + 1)), index_col=0)
            meta_df.to_excel(writer, sheet_name=sheet_name, index=True, header=False, startrow=0)
            df.to_excel(writer, sheet_name=sheet_name, index=True, startrow=len(meta_df))


if __name__ == "__main__":
    simulation_range = np.arange(2020, 2051)
    paper_outpath = os.path.join(script_dir, "paper")
    os.makedirs(paper_outpath, exist_ok=True)

    raw_temperatures_data_path = os.path.join(script_dir, "data/Temperature/projected-average-mean-s.csv")
    temp_outpath = os.path.join(script_dir, "results/Temperature")
    process_temperature_data(
        raw_temperatures_data_path_=raw_temperatures_data_path,
        temperature_outpath_=temp_outpath,
        paper_outpath_=paper_outpath,
    )
    temperature_path = os.path.join(script_dir, temp_outpath, 'temperature_change_to_2020.csv')

    costs_outpath = os.path.join(script_dir, "results/Costs")
    generate_costs(
        costs_outpath_=costs_outpath,
        paper_outpath_=paper_outpath,
        opex_status_quo_=0.5e6,
        opex_improvement_=1e6,
        capex_improvement_=21e6,
        capex_improvement_duration_=5,
        capex_improvement_start_=2031
    )

    drr_outpath = os.path.join(script_dir, "results/DRR")
    calculate_drr_impact_channel(
        drr_outpath_=drr_outpath,
        paper_outpath_=paper_outpath,
        temperature_path_=temperature_path,
        implementation_year_=2021,
        implementation_duration_=30,
    )

    agri_outpath = os.path.join(script_dir, "results/Agriculture")
    calc_agri_impact_channel(
        agri_outpath_=agri_outpath,
        paper_outpath_=paper_outpath,
        temperature_increases_path_=temperature_path,
        implementation_year_=2021,
        implementation_duration_=30,
    )

    hydropower_input_data_path = os.path.join(script_dir, "data/Hydropower/Koh_Galelli")
    hydropower_outpath = os.path.join(script_dir, "results/Hydropower")
    prepare_hydropower_channel(
        hydropower_outpath_=hydropower_outpath,
        paper_outpath_=paper_outpath,
        hydropower_input_data_path_=hydropower_input_data_path,
        temperature_increases_path_=temperature_path,
        implementation_year_=2021,
        implementation_duration_=30,
    )

    combine_tables(
        table_paths={
            'drr_impact_channel_KHM': (os.path.join(drr_outpath, "drr_impact_channel_KHM.csv"), 2),
            'agri_impact_channel_KHM': (os.path.join(agri_outpath, "agri_impact_channel_KHM.csv"), 2),
            'hydropower_impact_channel_KHM': (os.path.join(hydropower_outpath, "hydropower_impact_channel_KHM.csv"), 2),
            'scenario_costs_KHM': (os.path.join(costs_outpath, "scenario_costs_KHM.csv"), 3),
        },
        outpath_=os.path.join(script_dir, "results/Cambodia_MFMod_inputs.xlsx"),
    )