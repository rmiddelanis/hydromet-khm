# Reproducibility Package README

## Economy-wide Benefits of Improved Hydrometeorological Forecasts and Services in Cambodia

**Authors:** R. Middelanis, U. Chewpreecha, B. A. Jafino, R. Koh, S. Galelli, M. Sidibe, P. Avner

**Publication:** World Bank Policy Research Working Paper

---

## 1. Overview

This reproducibility package contains all code and data required to replicate the results presented in the paper *"Economy-wide Benefits of Improved Hydrometeorological Forecasts and Services in Cambodia"*. The package uses the Cambodia macroeconomic model (KHM model), built on the World Bank MFMod framework, to simulate economy-wide impacts of improved hydrometeorological forecasts and services. Shocks are applied to the model baseline and results are extracted and compiled into charts for the paper.

---

## 2. Software Requirements
The MFMod model runs in EViews. Pre- and post-processing of the model input and 
output data are done in Python. No specific hardware requirements apply. The full package runs in less than five minutes on a standard computer.

### 2.1 EViews
The model runs in Eviews with version 9 or above. No additional packages or libraries are required beyond a standard EViews installation.

### 2.2 Python 

The generation of input data and post-processing of model outputs is done in Python. The necessary packages can be installed with 
```
conda env create --file environment.yml -n hydromet-khm
```

To activate the environment, execute 
```
conda activate hydromet-khm
```


---

## 3. Data Availability Statement

All data used in this package are publicly available and are included in this reproducibility package. The authors confirm that they had legitimate access to all data used in the manuscript and have the right to include this data in the reproducibility package. The following sections provide details on the raw data sets used:

### Raw data for construction of the KHM model workfile

The Cambodia Macroeconomic and Fiscal Model (MFMod) Dataset (included in the model workfile `Data/KHMSoln_clean.WF1`) was constructed by the authors using the World Bank MFMod standard setup. Documentation of the MFMod framework is publicly available at:

> World Bank. *Macro-Fiscal Model (MFMod) Documentation*. Available at: [https://openknowledge.worldbank.org/server/api/core/bitstreams/3ef71fcd-2146-5c61-88af-a2e8453f5486/content](https://openknowledge.worldbank.org/server/api/core/bitstreams/3ef71fcd-2146-5c61-88af-a2e8453f5486/content)

The following data was used to construct the Cambodia MFMod model workfile: 

1. Macroeconomic variables in Cambodia MFMod
   - Reference: KHMNY* (GDP), KHMNE* (expenditure side GDP), KHMNV* (production side GDP), KHMGG* (fiscal), KHMBN* (BOP): Note the last second from last letter: X = price deflator, K = real and N = nominal. The last letter: N = m national local currency and D = m of USD
   - file:  Data/KHMSoln_clean.WF1
   - URL: https://www.worldbank.org/en/publication/macro-poverty-outlook/mpo_eap
   - Accessed: October 2025
   - License: World Bank Group
   - Access policy: Users must obtain the data directly from the Data URL for the referenced variables.
   - Note: Data for Cambodia was manually compiled from the resources available under the data URL. Data was accessed in October 2025. The current data available in the data URL might not match the version of the accessed data.

### Raw data for model input generation

1. Monthly river discharge and simulated electricity generation cost for Cambodia
   - Reference: Koh, R. & Galelli, S. (2024). Evaluating streamflow forecasts in hydro‐dominated power systems—When and why they matter. _Water Resources Research_, _60_, e2023WR035825. https://doi.org/10.1029/2023WR035825
   - files: `Q_m_avg.csv` (discharge) and `syscost_m.csv` (generation cost) in `./Data/raw/Koh_Galelli`
   - URL: https://doi.org/10.1029/2023WR035825
   - Received on: 2025-11-24
   - Note: The data was received directly from the authors who granted permission for inclusion in this reproducibility package
2. Temperature projections for Cambodia 
   - Reference: World Bank (2025). Climate Change Knowledge Portal—Projected Timeseries Anomaly of Average Mean Surface Air Temperature for Cambodia [Dataset]. 
   - files: `./Data/raw/WB_CCKP/projected-average-mean-s.csv`
   - URL: https://climateknowledgeportal.worldbank.org/country/cambodia/climate-data-projections
   - Accessed on: 2025-10-29
   - License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)


---

## 4. Package Contents

```
  /
  ├── README.md                                  # This file
  ├── KHM_shocks_EWS.prg                         # EViews program: extend standard Cambodia MFMod model to include climate extension, runs baseline and 24 shock scenarios
  ├── prepare_impact_channel_data.py             # Script to generate MFMod inputs from raw data
  ├── process_model_results.py                   # Script to post-process MFMod outputs
  ├── environment.yml                            # Conda environment file
  ├── Data/           
  │   ├── raw/                                   # Raw input data files from Koh and Galelli (2024) and World Bank (2025c)
  │   │   ├──Koh_Galelli/         
  │   │   │   ├── Q_m_avg.csv                    # Monthyl discharge data 
  │   │   │   └── syscost_m.csv                  # Simulated electricity generation cost
  │   │   └──WB_CVCKP/
  │   │       └──projected-average-mean-s.csv    # Projected future temperatures for Cambodia
* │   ├── input_channels/...                     # Input data for individual impact channels (pre-computed)
* │   ├── Cambodia_MFMod_inputs.xlsx             # Combined MFMod inputs (pre-computed)
  │   └── KHMSoln_clean.WF1                      # Cambodia MFMod model solution workfile (baseline)
  └── results/                                   # Output folder 
*     ├── display_items/                         # Figures and tables as included in the manuscript (pre-computed) 
+     └── EWS_MFMod.xlsx                         # Excel file for MFMod outputs (pre-filled with simulation outputs)           

Files and directories marked with an asterisk * are generated or modified at runtime. 
Files marked with a plus sign + require manual editing during the replication process as indicated in the instructions below.
This reproducibility package contains the full pre-computed and pre-edited outputs.
```


---

## 5. Instructions for Replication

### Step 1 — Verify the package folder structure

Ensure the package is organised as described in Section 4. In particular, confirm that:
- The `Data/` folder contains both `KHMSoln_clean.WF1` and all necessary input files in `Data/raw`.

### Step 2 — Prepare the model input data
To create all model input data from raw inputs, execute 
```
python prepare_impact_channel_data.py
```

This will create a single file ```./Data/Cambodia_MFMod_inputs.xlsx``` containing all input data for the MFMod model. Individual impact channel data and corresponding display items (Figures 2—6 and Supplementary Tables 1—4) are written to subdirectories of ```./Data/input_channels```. Data is also additionally in machine-readable ```.csv``` files. Figures and tables are also copied to ```./results/display_items```.

### Step 3 — Run the shocks program

**No manual path changes are required.** The program automatically sets the working directory to the folder from which it is run, using the EViews built-in `@runpath` command.

Open EViews 13 and run `KHM_shocks_EWS.prg` 

Expected run time is **less than one minute**.

### What the program does

The program executes the following steps automatically:

1. Opens the Cambodia model solution workfile (`Data/KHMSoln_clean.WF1`) and imports the damage input data (`Data/Cambodia_MFMod_inputs.xlsx`).
2. Modifies model equations to incorporate climate damage channels: agricultural productivity, labour productivity, health impacts, roads and bridges disruption, and flood damage to capital stock (repairable and permanent).
3. Solves the **baseline** scenario with the updated model structure.
4. Runs **24 shock scenarios** across three dimensions:
   - **Climate scenarios (2):** Optimistic (`Opt`), Pessimistic (`Pes`)
   - **Policy scenarios (3):** Control (`CON`), Status Quo (`STQ`), Improvement (`IMP`)
   - **Impact channels (4):** Flood/Disaster Risk Reduction (`DRR`), Agriculture (`ARG`), Hydropower/Electricity (`HYD`), All channels combined (`ALL`)
5. Displays GDP results (`NYGDPMKTPKN`) for all 24 scenarios plus baseline over 2015–2050 in the EViews output window.


### Step 4 — Transfer results to Excel

Copy the GDP results displayed in the EViews output window (2015–2050, all scenarios) and paste them into the highlighted cells of sheet _MFModRaw_ in `./results/EWS_MFMod.xlsx` (25 columns for one baseline and 24 scenarios). 

---

### Step 5 — Post-process model output
To create Figures 7—11, Supplementary Figures 1—4, and Supplementary Tables 4—11, run 

```
python process_model_results.py
```
The script will place all of the above display items in ```./results/display_items```.

---

## 6. Mapping of Outputs to Exhibits

The table below maps each exhibit in the paper to the file responsible for generating it. All automatically generated display items are placed in ```./results/display_items```.

| Exhibit                | Description                                                                                | Files                                                                           | Generated by                                     |
|------------------------|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| Figure 1               | Conceptual setup of the study                                                              | n/a                                                                             | compiled manually                                |
| Figure 2               | Temperature projections for Cambodia                                                       | ```temperature_projections_KHM.pdf```                                           | ```prepare_impact_channel_data.py```             |
| Figure 3               | Disaster Risk Redution impact channel                                                      | ```drr_impact_channel_KHM.pdf```                                                | ```prepare_impact_channel_data.py```             |
| Figure 4               | Agricultural Productivity impact channel                                                   | ```agri_impact_channel_KHM.pdf```                                               | ```prepare_impact_channel_data.py```             |
| Figure 5               | Selection of year subset for hydropower climate change projections                         | ```hydropower_cc_year_selection.pdf```                                          | ```prepare_impact_channel_data.py```             |
| Figure 6               | Hydropower impact channel                                                                  | ```hydropower_impact_channel_KHM.pdf```                                         | ```prepare_impact_channel_data.py```             |
| Figure 7               | Isolated GDP impact of the Disaster Risk Reduction channel                                 | ```results_DRR_control_rel.pdf```                                               | ```process_model_results.py```                   |
| Figure 8               | Differences in GDP outcomes across hydromet services and climate change scenarios by 2050  | ```results_gdp_differences.pdf```; ```results_gdp_differences.csv```            | ```process_model_results.py```                   |
| Figure 9               | Isolated GDP impact of the Agricultural Productivity channel                               | ```results_AGR_control_rel.pdf```                                               | ```process_model_results.py```                   |
| Figure 10              | Isolated GDP impact of the Hydropower channel                                              | ```results_HYD_control_rel.pdf```                                               | ```process_model_results.py```                   |
| Figure 11              | Combined GDP impact with all channels active simultaneously                                | ```results_All_control_rel.pdf```                                               | ```process_model_results.py```                   |
| Supplementary Figure 1 | Isolated DRR channel – GDP deviation from baseline                                         | ```results_DRR_baseline_rel.pdf```                                              | ```process_model_results.py```                   |
| Supplementary Figure 2 | Isolated Agricultural Productivity channel – GDP deviation from baseline                   | ```results_AGR_baseline_rel.pdf```                                              | ```process_model_results.py```                   |
| Supplementary Figure 3 | Isolated Hydropower channel – GDP deviation from baseline                                  | ```results_HYD_baseline_rel.pdf```                                              | ```process_model_results.py```                   |
| Supplementary Figure 4 | mbined GDP impact – deviation from baseline                                                | ```results_All_baseline_rel.pdf```                                              | ```process_model_results.py```                   |
| Table 1                | Scenario costs                                                                             | n/a                                                                             | compiled manually                                |   
| Supplementary Table 1  | Annual average flood damage                                                                | ```drr_impact_channel_KHM.csv```; ```drr_impact_channel_KHM.tex```              | ```prepare_impact_channel_data.py```             |   
| Supplementary Table 2  | Agricultural productivity change                                                           | ```agri_impact_channel_KHM.csv```; ```agri_impact_channel_KHM.tex```            | ```prepare_impact_channel_data.py```             |   
| Supplementary Table 3  | Electricity generation cost reduction                                                      | ```hydropower_impact_channel_KHM.csv```; ```hydropower_impact_channel_KHM.tex``` | ```prepare_impact_channel_data.py```             |   
| Supplementary Table 4  | GDP deviation from control – Disaster Risk Reduction                                       | ```results_DRR_control_rel.csv```; ```results_DRR_control_rel.tex```            | ```process_model_results.py```                   |   
| Supplementary Table 5  | GDP deviation from control – Agricultural Productivity                                     | ```results_AGR_control_rel.csv```; ```results_AGR_control_rel.tex```            | ```process_model_results.py```                   |   
| Supplementary Table 6  | GDP deviation from control – Hydropower                                                    | ```results_HYD_control_rel.csv```; ```results_HYD_control_rel.tex```            | ```process_model_results.py```                   |   
| Supplementary Table 7  | GDP deviation from control – all channels combined                                         | ```results_All_control_rel.csv```; ```results_All_control_rel.tex```            | ```process_model_results.py```                   |   
| Supplementary Table 8  | GDP deviation from baseline – Disaster Risk Reduction                                      | ```results_DRR_baseline_rel.csv```; ```results_DRR_baseline_rel.tex```                                                          | ```process_model_results.py```                   |   
| Supplementary Table 9  | GDP deviation from baseline – Agricultural Productivity                                    | ```results_AGR_baseline_rel.csv```; ```results_AGR_baseline_rel.tex```                                                          | ```process_model_results.py```                   |   
| Supplementary Table 10 | GDP deviation from baseline – Hydropower                                                   | ```results_HYD_baseline_rel.csv```; ```results_HYD_baseline_rel.tex```                                                          | ```process_model_results.py```                   |   
| Supplementary Table 11 | GDP deviation from baseline – all channels combined                                        | ```results_All_baseline_rel.csv```; ```results_All_baseline_rel.tex```                                                          | ```process_model_results.py```                   |




