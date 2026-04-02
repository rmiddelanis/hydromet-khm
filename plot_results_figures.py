import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shutil

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


def export_table(df, caption, label, outpath, filename, suptable=False):
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
    if suptable:
        latex = latex.replace("\\label{tab", "\\label[suptable]{tab")
    with open(os.path.join(outpath, filename + '.tex'), 'w') as f:
        f.write(latex)
    df.to_csv(os.path.join(outpath, filename + '.csv'))


def generate_gdp_differences_table(impact_channel_data_, outpath_):
    """Generate paper/tables/results_gdp_differences.tex and .csv from control-relative DataFrames."""
    channels = ['DRR', 'AGR', 'HYD', 'All']
    col_names = ['DRR', 'Agriculture', 'Hydropower', 'All']

    def fmt(v):
        return f"{v:.2f}\\%"

    lines = [
        "\\begin{table}[htb]",
        "\\caption{Differences in GDP outcomes across hydromet services and climate change scenarios by 2050.}",
        "\\label{tab:gdp_differences}",
        "\\centering",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        " & DRR & Agriculture & Hydropower & All \\\\",
    ]

    csv_rows = []
    for climate in ['Optimistic', 'Pessimistic']:
        sq_vals = [impact_channel_data_[ch].loc[2050, f'{climate} - Status quo'] for ch in channels]
        imp_vals = [impact_channel_data_[ch].loc[2050, f'{climate} - Improvement'] for ch in channels]
        diff_vals = [i - s for i, s in zip(imp_vals, sq_vals)]

        lines += [
            "\\midrule",
            f"\\multicolumn{{5}}{{l}}{{\\textit{{{climate} climate scenarios}}}} \\\\",
            "\\midrule",
            f"{'Status quo -- control':<27}& {' & '.join(fmt(v) for v in sq_vals)} \\\\",
            f"{'Improvement -- control':<27}& {' & '.join(fmt(v) for v in imp_vals)} \\\\",
            f"{'Improvement -- status quo':<27}& {' & '.join(fmt(v) for v in diff_vals)} \\\\",
        ]

        for label, vals in [('Status quo -- control', sq_vals),
                             ('Improvement -- control', imp_vals),
                             ('Improvement -- status quo', diff_vals)]:
            csv_rows.append({'Climate': climate, 'Comparison': label,
                             **dict(zip(col_names, vals))})

    lines += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]

    with open(os.path.join(outpath_, 'results_gdp_differences.tex'), 'w') as f:
        f.write("\n".join(lines))

    pd.DataFrame(csv_rows).set_index(['Climate', 'Comparison']).to_csv(
        os.path.join(outpath_, 'results_gdp_differences.csv')
    )


def plot_gdp_differences(data_by_channel, outpath, filename='results_gdp_differences.pdf'):
    """Horizontal paired bar chart of 2050 GDP differences by channel and climate scenario."""
    channels = ['DRR', 'AGR', 'HYD', 'All']
    channel_titles = {'DRR': 'DRR', 'AGR': 'Agriculture', 'HYD': 'Hydropower', 'All': 'All channels'}
    y_labels = ['Status quo\nvs. control', 'Improvement\nvs. control', 'Improvement\nvs. status quo']
    y_pos = np.arange(3)
    bar_h = 0.35
    colors = {'Optimistic': '#4C72B0', 'Pessimistic': '#DD8452'}

    fig, axes = plt.subplots(1, 4, figsize=(12, 3), sharey=True)

    for ax, ch in zip(axes, channels):
        df = data_by_channel[ch]
        opt_sq  = df.loc[2050, 'Optimistic - Status quo']
        opt_imp = df.loc[2050, 'Optimistic - Improvement']
        pes_sq  = df.loc[2050, 'Pessimistic - Status quo']
        pes_imp = df.loc[2050, 'Pessimistic - Improvement']

        opt_vals = [opt_sq, opt_imp, opt_imp - opt_sq]
        pes_vals = [pes_sq, pes_imp, pes_imp - pes_sq]

        ax.barh(y_pos - bar_h / 2, opt_vals, height=bar_h,
                color=colors['Optimistic'], label='Optimistic')
        ax.barh(y_pos + bar_h / 2, pes_vals, height=bar_h,
                color=colors['Pessimistic'], label='Pessimistic')
        ax.axvline(0, color='black', linewidth=0.5, zorder=0)
        ax.set_title(channel_titles[ch])

    axes[0].set_yticks(y_pos)
    axes[0].set_yticklabels(y_labels)
    fig.supxlabel('GDP deviation (%)')

    handles, labels = axes[0].get_legend_handles_labels()
    axes[-1].legend(handles, labels, loc='upper left', frameon=False, bbox_to_anchor=(1, 1))

    plt.tight_layout()
    fig.savefig(os.path.join(outpath, filename), dpi=300, bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    excel_path = os.path.join(script_dir, '../../results/EWS_MFMod_full.xlsx')
    outpath = os.path.join(script_dir, 'results')
    paper_outpath = os.path.join(script_dir, 'paper')
    os.makedirs(outpath, exist_ok=True)
    os.makedirs(os.path.join(paper_outpath, 'figures'), exist_ok=True)
    os.makedirs(os.path.join(paper_outpath, 'tables'), exist_ok=True)

    channel_labels = {
        'DRR': 'Disaster Risk Reduction',
        'AGR': 'Agricultural Productivity',
        'HYD': 'Hydropower',
        'All': 'all channels combined',
    }

    data_by_channel = {}
    for name, sheet in {'DRR': 'DRR', 'AGR': 'AGR', 'HYD': 'HYD', 'All': 'All'}.items():
        df_pct, df_abs = read_results_sheet(excel_path, sheet)

        # Baseline-relative
        df_baseline = rename_columns(df_pct)
        plot_channel(
            df=df_baseline,
            ylabel='GDP deviation from baseline (%)',
            outpath=outpath,
            filename=f'results_{name}_baseline_rel.pdf'
        )
        export_table(
            to_multiindex(df_baseline),
            caption=f"GDP deviation from baseline (\\%) -- {channel_labels[name]}.",
            label=f"tab:results_{name}_baseline_rel",
            outpath=outpath,
            filename=f'results_{name}_baseline_rel',
            suptable=True,
        )

        # Control-relative
        df_control = rename_columns(compute_control_relative(df_abs))
        plot_channel(
            df=df_control,
            ylabel='GDP deviation from control (%)',
            outpath=outpath,
            filename=f'results_{name}_control_rel.pdf'
        )
        export_table(
            to_multiindex(df_control),
            caption=f"GDP deviation from control (\\%) -- {channel_labels[name]}.",
            label=f"tab:results_{name}_control_rel",
            outpath=outpath,
            filename=f'results_{name}_control_rel',
            suptable=True,
        )

        data_by_channel[name] = df_control

    # Generate GDP differences summary table and figure
    generate_gdp_differences_table(data_by_channel, outpath)
    plot_gdp_differences(data_by_channel, outpath)

    # Copy .tex and .pdf files to paper directory
    for f in os.listdir(outpath):
        if f.endswith('.tex') or f.endswith('.pdf'):
            shutil.copy2(os.path.join(outpath, f), os.path.join(paper_outpath, 'tables' if f.endswith('.tex') else 'figures', f))

    print(f"Generated all figures and tables")
