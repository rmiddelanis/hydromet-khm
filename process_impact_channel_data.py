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

    fig, axs = plt.subplots(nrows=1, figsize=(5, 3), sharex=True)
    axs = [axs]
    for scenario, color in zip(['Historical', 'SSP1-2.6', 'SSP5-8.5'], ['k', 'tab:blue', 'tab:red']):
        axs[0].plot(df.index, df[scenario], label=scenario, color=color)
        axs[0].fill_between(df.index, df[scenario + ' 10-90th Percentile Range (low)'], df[scenario + ' 10-90th Percentile Range (high)'], color=color, alpha=0.2, lw=0)
    df.loc[np.arange(2020, 2051), 'Optimistic'].plot(ax=axs[0], label='Optimistic', color='tab:blue', linestyle='--')
    df.loc[np.arange(2020, 2051), 'Pessimistic'].plot(ax=axs[0], label='Pessimistic', color='tab:red', linestyle='--')
    axs[0].set_ylabel('Mean temperature (°C)')
    axs[0].legend(loc='upper left', frameon=False)#, bbox_to_anchor=(1, 1))
    plt.tight_layout()
    fig.savefig(os.path.join(output_path, 'temperature_projections_KHM.pdf'), dpi=300)

    temperature_change_to_base_year = (df - df.loc[2020])[['Historical', 'Optimistic', 'Pessimistic']]
    temperature_change_to_base_year.drop(columns='Historical').loc[np.arange(2020, 2051)].to_csv(os.path.join(output_path, 'temperature_change_to_2020.csv'))
    # for scenario, color in zip(['Historical', 'Optimistic', 'Pessimistic'], ['k', 'tab:blue', 'tab:red']):
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
    res['Optimistic - no FC'] = (temperature_increases / temperature_increases.loc[2050])['Optimistic'] * (optimistic_aal_2050 - current_aal) + current_aal
    res['Pessimistic - no FC'] = (temperature_increases / temperature_increases.loc[2050])['Pessimistic'] * (pessimistic_aal_2050 - current_aal) + current_aal

    res['Optimistic - current FC'] = res['Optimistic - no FC'] * (1 - current_ew_benefits)
    res['Pessimistic - current FC'] = res['Pessimistic - no FC'] * (1 - current_ew_benefits)

    implementation_level = pd.Series(np.clip((res.index - implementation_year) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
    res['Optimistic - perfect FC'] = res['Optimistic - no FC'] * (1 - (current_ew_benefits + implementation_level * (perfect_ew_benefits - current_ew_benefits)))
    res['Pessimistic - perfect FC'] = res['Pessimistic - no FC'] * (1 - (current_ew_benefits + implementation_level * (perfect_ew_benefits - current_ew_benefits)))

    fig, ax = plt.subplots(figsize=(7, 3))
    for col in res.columns:
        ax.plot(res.index, res[col], label=col)
    ax.set_ylim(0, ax.get_ylim()[1])
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel('Annual Average Capital Loss\n(% national capital stock)')
    plt.tight_layout()
    if outpath:
        fig.savefig(os.path.join(outpath, 'drr_impact_channel_KHM.pdf'), dpi=300)
        res.to_csv(os.path.join(outpath, 'drr_impact_channel_KHM.csv'))


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
    for scenario in ['Optimistic', 'Pessimistic']:
        temp_increase = temperature_increases[scenario]
        productivity_loss = temp_increase.map(lambda x: np.interp(x, list(productivity_loss_lookup.keys()), list(productivity_loss_lookup.values())))

        res[f'{scenario} - no FC'] = productivity_loss / 100
        res[f'{scenario} - current FC'] = (1 + res[f'{scenario} - no FC']) * (1 + productivity_increase_current_forecasts) - 1
        implementation_level = pd.Series(np.clip((res.index - implementation_year) / implementation_duration, 0, 1), index=res.index, name='implementation_level')
        res[f'{scenario} - perfect FC'] = (1 + res[f'{scenario} - no FC']) * (1 + productivity_increase_current_forecasts + implementation_level * (productivity_increase_perfect_forecasts - productivity_increase_current_forecasts)) - 1

    fig, ax = plt.subplots(figsize=(7, 3))
    for col in res.columns:
        ax.plot(res.index, res[col], label=col)
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel('Agricultural productivity\nincrease from forecasts (%)')
    plt.tight_layout()
    if outpath:
        fig.savefig(os.path.join(outpath, 'agri_impact_channel_KHM.pdf'), dpi=300)
        res.to_csv(os.path.join(outpath, 'agri_impact_channel_KHM.csv'))


if __name__ == "__main__":
    temperature_data_path = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/data/Temperature/projected-average-mean-s.csv"
    temperature_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Temperature/"
    process_temperature_data(temperature_data_path, temperature_outpath)
    temperature_change_path = os.path.join(temperature_outpath, 'temperature_change_to_2020.csv')

    drr_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/DRR/"
    calculate_drr_impact_channel(temperature_change_path, implementation_year=2031, implementation_duration=10, outpath=drr_outpath)

    agri_outpath = "/Users/robin/Documents/Karriere/Jobs/2023_The_World_Bank/03_projects/05_Hydromet-Cambodia/results/Agriculture/"
    calc_agri_impact_channel(temperature_change_path, implementation_year=2031, implementation_duration=10, outpath=agri_outpath)
