import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
