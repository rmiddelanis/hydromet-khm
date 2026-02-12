import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

script_dir = os.path.dirname(os.path.realpath(__file__))


def read_results_sheet(excel_path, sheet_name, start_year=2020):
    """Read the absolute GDP columns (B-H) and percentage deviation columns (K-Q) from a results sheet."""
    df_raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    # Percentage deviation from baseline: columns K-Q (indices 10-16)
    labels = df_raw.iloc[1, 11:17].values
    years = df_raw.iloc[2:, 10].values.astype(int)
    pct_data = df_raw.iloc[2:, 11:17].values.astype(float)
    df_pct = pd.DataFrame(pct_data, index=years, columns=labels)
    df_pct.index.name = 'Year'
    df_pct *= 100

    # Absolute GDP values: columns B-H (indices 1-7)
    abs_labels = df_raw.iloc[0, 1:8].values
    abs_years = df_raw.iloc[2:, 0].values.astype(int)
    abs_data = df_raw.iloc[2:, 1:8].values.astype(float)
    df_abs = pd.DataFrame(abs_data, index=abs_years, columns=abs_labels)
    df_abs.index.name = 'Year'

    # Filter to start_year onwards
    df_pct = df_pct.loc[df_pct.index >= start_year]
    df_abs = df_abs.loc[df_abs.index >= start_year]

    return df_pct, df_abs


SCENARIO_RENAME = {
    'Control_Optimistic': 'Optimistic - Control',
    'StatusQuo_Optimistic': 'Optimistic - Status quo',
    'Improvement_Optimistic': 'Optimistic - Improvement',
    'Control_Pessimistic': 'Pessimistic - Control',
    'StatusQuo_Pessimistic': 'Pessimistic - Status quo',
    'Improvement_Pessimistic': 'Pessimistic - Improvement',
}

SCENARIO_ORDER = [
    'Optimistic - Control', 'Optimistic - Status quo', 'Optimistic - Improvement',
    'Pessimistic - Control', 'Pessimistic - Status quo', 'Pessimistic - Improvement',
]


def rename_columns(df):
    """Rename columns from 'Control_Optimistic' to 'Optimistic - Control' style."""
    df_renamed = df.rename(columns=SCENARIO_RENAME)
    return df_renamed[[c for c in SCENARIO_ORDER if c in df_renamed.columns]]


def compute_control_relative(df_abs):
    """Compute percentage deviation of each scenario from its respective control scenario."""
    df_rel = pd.DataFrame(index=df_abs.index)
    for climate in ['Optimistic', 'Pessimistic']:
        control_col = f'Control_{climate}'
        for forecast_key in ['StatusQuo', 'Improvement']:
            src_col = f'{forecast_key}_{climate}'
            if src_col in df_abs.columns and control_col in df_abs.columns:
                df_rel[src_col] = (df_abs[src_col] / df_abs[control_col] - 1) * 100
    return df_rel


def plot_channel(df, ylabel, outpath, filename):
    fig, ax = plt.subplots(figsize=(7, 3))
    for col in df.columns:
        ax.plot(df.index, df[col], label=col)
    ax.legend(loc='upper left', frameon=False, bbox_to_anchor=(1, 1))
    ax.set_xlabel('Year')
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    fig.savefig(os.path.join(outpath, filename), dpi=300)
    plt.close(fig)


def to_multiindex(df):
    """Convert 'Optimistic - Control' style columns to a MultiIndex."""
    tuples = [tuple(col.split(' - ')) for col in df.columns]
    df = df.copy()
    df.columns = pd.MultiIndex.from_tuples(tuples, names=['Climate scenario', 'Forecast scenario'])
    return df.sort_index(axis=1, level='Climate scenario', sort_remaining=False)


def export_table(df, caption, label, outpath, filename):
    """Export a DataFrame with MultiIndex columns to .tex and .csv files."""
    latex = df.to_latex(
        float_format="%.2f",
        index=True,
        header=True,
        na_rep="",
        caption=caption,
        label=label,
        multicolumn=True,
        multicolumn_format='c',
    )
    latex = latex.replace("\\begin{tabular}", "\\centering\n\\begin{tabular}")
    with open(os.path.join(outpath, filename + '.tex'), 'w') as f:
        f.write(latex)
    df.to_csv(os.path.join(outpath, filename + '.csv'))


if __name__ == "__main__":
    excel_path = os.path.join(script_dir, '../../results/EWS_MFMod_full.xlsx')
    outpath = os.path.join(script_dir, 'results')
    paper_outpath = os.path.join(script_dir, 'paper')
    os.makedirs(outpath, exist_ok=True)

    channel_labels = {
        'DRR': 'Disaster Risk Reduction',
        'AGR': 'Agricultural Productivity',
        'HYD': 'Hydropower',
        'All': 'all channels combined',
    }

    for name, sheet in {'DRR': 'DRR', 'AGR': 'AGR', 'HYD': 'HYD', 'All': 'All'}.items():
        df_pct, df_abs = read_results_sheet(excel_path, sheet)

        # Baseline-relative
        df_baseline = rename_columns(df_pct)
        plot_channel(df_baseline, 'GDP deviation from baseline (%)', outpath, f'results_{name}_baseline_rel.pdf')
        export_table(
            to_multiindex(df_baseline),
            caption=f"GDP deviation from baseline (\\%) -- {channel_labels[name]}.",
            label=f"tab:results_{name}_baseline_rel",
            outpath=outpath,
            filename=f'results_{name}_baseline_rel',
        )

        # Control-relative
        df_control = rename_columns(compute_control_relative(df_abs))
        plot_channel(df_control, 'GDP deviation from control (%)', outpath, f'results_{name}_control_rel.pdf')
        export_table(
            to_multiindex(df_control),
            caption=f"GDP deviation from control (\\%) -- {channel_labels[name]}.",
            label=f"tab:results_{name}_control_rel",
            outpath=outpath,
            filename=f'results_{name}_control_rel',
        )

    # Copy .tex and .pdf files to paper directory
    import shutil
    for f in os.listdir(outpath):
        if f.startswith('results_') and (f.endswith('.tex') or f.endswith('.pdf')):
            shutil.copy2(os.path.join(outpath, f), os.path.join(paper_outpath, 'tables' if f.endswith('.tex') else 'figures', f))

    print(f"Figures and tables saved to {outpath}")
