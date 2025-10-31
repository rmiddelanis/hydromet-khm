import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def process_temperature_data(raw_data_path, output_path):
    # Load raw temperature data
    df = pd.read_csv(raw_data_path).rename(columns={'Category': 'year'}).set_index('year')

    df = df.rename(columns={'Hist. Ref. Period, 1950-2014': 'Historical'})

    df['SSP1-2.6-rolling'] = df['SSP1-2.6'].rolling(window=10, center=True).mean()
    df['SSP5-8.5-rolling'] = df['SSP5-8.5'].rolling(window=10, center=True).mean()

    plot_range = (df.index >= 1970) & (df.index <= 2085)
    simulation_range = (df.index >= 2020) & (df.index <= 2050)

    fig, axs = plt.subplots(nrows=1, figsize=(5.5, 3.5), sharex=True)
    axs = [axs]
    for scenario, color in zip(['Historical', 'SSP1-2.6', 'SSP5-8.5'], ['k', 'tab:blue', 'tab:red']):
        axs[0].plot(df.loc[plot_range].index, df.loc[plot_range, scenario], label=scenario, color=color, alpha=.25)
        axs[0].fill_between(df.loc[plot_range].index, df.loc[plot_range, scenario + ' 10-90th Percentile Range (low)'], df.loc[plot_range, scenario + ' 10-90th Percentile Range (high)'], color=color, alpha=0.1, lw=0)
    df.loc[simulation_range, 'SSP1-2.6-rolling'].plot(ax=axs[0], label='__none__', color='tab:blue', linestyle='--')
    df.loc[simulation_range, 'SSP5-8.5-rolling'].plot(ax=axs[0], label='__none__', color='tab:red', linestyle='--')
    axs[0].plot([], [], color='k', linestyle='--', label='10-y rolling mean')
    axs[0].set_ylabel('Mean temperature (°C)')
    axs[0].legend(loc='upper left', frameon=False)
    axs[0].set_ylim((27, 31))

    offset = (df.loc[2020, 'SSP1-2.6-rolling'] + df.loc[2020, 'SSP5-8.5-rolling']) / 2
    ax2 = axs[0].twinx()
    ylim_left = axs[0].get_ylim()
    ax2.set_ylim([ylim_left[0] - offset, ylim_left[1] - offset])
    ax2.set_ylabel("Temperature increase (°C)")
    ax2.axhline(0, color='gray', linestyle='--', linewidth=0.8)

    x_pos = df.index[plot_range][-1] + 10
    for i, (scenario, color) in enumerate(zip(['SSP1-2.6', 'SSP5-8.5'], ['tab:blue', 'tab:red'])):
        smooth = df.loc[simulation_range, scenario + '-rolling']
        increase = smooth.iloc[-1] - smooth.iloc[0]
        ax2.vlines(x=x_pos + i * 5, ymin=0, ymax=increase, color=color, linewidth=3)
        ax2.text(x_pos - 2 + i * 5, increase + .01, f"+{increase:.1f}", color=color, va='bottom', ha='center', fontsize=8)

    # drop x labels above the plot_range
    axs[0].set_xticks(axs[0].get_xticks()[(axs[0].get_xticks() <= df.index[plot_range][-1]) & (axs[0].get_xticks() >= df.index[plot_range][0])])

    axs[0].set_ylabel('Mean temperature (°C)')
    axs[0].set_xlabel('Year')
    axs[0].legend(loc='upper left', frameon=False)
    axs[0].set_ylim((27, 31))

    plt.tight_layout()
    fig.savefig(os.path.join(output_path, 'temperature_projections_KHM.pdf'), dpi=300)

    temperature_change_to_base_year = (df - df.loc[2020])[['Historical', 'SSP1-2.6-rolling', 'SSP5-8.5-rolling']].rename(columns={'SSP1-2.6-rolling': 'SSP1-2.6', 'SSP5-8.5-rolling': 'SSP5-8.5'})
    temperature_change_to_base_year.drop(columns='Historical').loc[np.arange(2020, 2051)].to_csv(os.path.join(output_path, 'temperature_change_to_2020.csv'))
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

    temperature_increases = pd.read_csv(temperature_increases_path, index_col='year')

    res = pd.DataFrame(index=temperature_increases.index)
    res['SSP1-2.6 - Control'] = (temperature_increases / temperature_increases.loc[2050])['SSP1-2.6'] * (optimistic_aal_2050 - current_aal) + current_aal
    res['SSP5-8.5 - Control'] = (temperature_increases / temperature_increases.loc[2050])['SSP5-8.5'] * (pessimistic_aal_2050 - current_aal) + current_aal

    res['SSP1-2.6 - Status quo'] = res['SSP1-2.6 - Control'] * (1 - current_ew_benefits)
    res['SSP5-8.5 - Status quo'] = res['SSP5-8.5 - Control'] * (1 - current_ew_benefits)

    implementation_level = pd.Series(np.clip((res.index - (implementation_year - 1)) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
    res['SSP1-2.6 - Improvement'] = res['SSP1-2.6 - Control'] * (1 - (current_ew_benefits + implementation_level * (perfect_ew_benefits - current_ew_benefits)))
    res['SSP5-8.5 - Improvement'] = res['SSP5-8.5 - Control'] * (1 - (current_ew_benefits + implementation_level * (perfect_ew_benefits - current_ew_benefits)))

    res = res[['SSP1-2.6 - Control', 'SSP1-2.6 - Status quo', 'SSP1-2.6 - Improvement', 'SSP5-8.5 - Control', 'SSP5-8.5 - Status quo', 'SSP5-8.5 - Improvement']]
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

    # values obtained from Roson and Sartori (2016)
    productivity_loss_lookup = {
        0: 0.0,
        1: -2.51,
        2: -5.27,
        3: -8.2,
        4: -11.33,
        5: -14.66,
    }

    productivity_increase_no_forecasts = 0
    productivity_increase_current_forecasts = 0.1034
    productivity_increase_perfect_forecasts = 0.1686

    res = pd.DataFrame(index=temperature_increases.index)
    for scenario in ['SSP1-2.6', 'SSP5-8.5']:
        temp_increase = temperature_increases[scenario]
        productivity_loss = temp_increase.map(lambda x: np.interp(x, list(productivity_loss_lookup.keys()), list(productivity_loss_lookup.values())))

        res[f'{scenario} - Control'] = productivity_loss / 100
        res[f'{scenario} - Status quo'] = (1 + res[f'{scenario} - Control']) * (1 + productivity_increase_current_forecasts) - 1
        implementation_level = pd.Series(np.clip((res.index - (implementation_year - 1)) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
        res[f'{scenario} - Improvement'] = (1 + res[f'{scenario} - Control']) * (1 + productivity_increase_current_forecasts + implementation_level * (productivity_increase_perfect_forecasts - productivity_increase_current_forecasts)) - 1
    res *= 100  # convert to percentage
    res = res[['SSP1-2.6 - Control', 'SSP1-2.6 - Status quo', 'SSP1-2.6 - Improvement', 'SSP5-8.5 - Control', 'SSP5-8.5 - Status quo', 'SSP5-8.5 - Improvement']]

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
    temperature_data_path = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/data/Temperature/projected-average-mean-s.csv"
    temperature_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Temperature/"
    process_temperature_data(temperature_data_path, temperature_outpath)
    temperature_change_path = os.path.join(temperature_outpath, 'temperature_change_to_2020.csv')

    drr_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/DRR/"
    calculate_drr_impact_channel(temperature_change_path, implementation_year=2020, implementation_duration=30, outpath=drr_outpath)

    agri_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Agriculture/"
    calc_agri_impact_channel(temperature_change_path, implementation_year=2020, implementation_duration=30, outpath=agri_outpath)
