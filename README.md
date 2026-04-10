# Reproducibility Package README

## Economy-wide Benefits of Improved Hydrometeorological Forecasts and Services in Cambodia

**Authors:** R. Middelanis, U. Chewpreecha, B. A. Jafino, R. Koh, S. Galelli, M. Sidibe, P. Avner

**Publication:** World Bank Policy Research Working Paper

---

## 1. Overview

This reproducibility package contains all code and data required to replicate the results presented in the paper *"Economy-wide Benefits of Improved Hydrometeorological Forecasts and Services in Cambodia"*. The package uses the Cambodia macroeconomic model (KHM model), built on the World Bank MFMod framework, to simulate economy-wide impacts of improved hydrometeorological forecasts and services. Shocks are applied to the model baseline and results are extracted and compiled into charts for the paper.

---

## 2. Software Requirements

### 2.1 EViews
The model runs in Eviews with the following requirements: 

| Software | Version |
|----------|---------|
| EViews   | 9 or above      |
| Microsoft Excel | Any recent version (for chart production) |

No additional packages or libraries are required beyond a standard EViews installation.

The package was developed and tested on Windows. No specific hardware requirements apply — the full package runs in less than one minute on a standard laptop.

### 2.2 Python 

The generation of input data and post-processing of model outputs is done in Python. The necessary packages can be installed with 
```
conda env create --file environment.yml -n hydromet-khm
```

To activate, run 
```
conda activate hydromet-khm
```


---

## 3. Data Availability Statement

**Summary:** All data used in this package are publicly available and are included in the EViews workfile provided.

The KHM model workfile was constructed by the author using the World Bank MFMod standard setup. Documentation of the MFMod framework is publicly available at:

> World Bank. *Macro-Fiscal Model (MFMod) Documentation*. Available at: [https://openknowledge.worldbank.org/server/api/core/bitstreams/3ef71fcd-2146-5c61-88af-a2e8453f5486/content](https://openknowledge.worldbank.org/server/api/core/bitstreams/3ef71fcd-2146-5c61-88af-a2e8453f5486/content)

| File                                 | Description                                                     | Source                                                          | Access              |
|--------------------------------------|-----------------------------------------------------------------|-----------------------------------------------------------------|---------------------|
| `Data/KHMSoln_clean.WF1`             | Cambodia MFMod macroeconomic model solution workfile (baseline) | Constructed by the authors using the World Bank MFMod framework | Included in package |
| `Data/raw/Koh_Galelli/Q_m_avg.csv`   | Monthly discharge                                               | Koh and Galelli (2024)                                          | Included in package |
| `Data/raw/Koh_Galelli/syscost_m.csv` | Simulated electricity generation cost                           | Koh and Galelli (2024)                                          | Included in package                    |
| `Data/raw/data/raw/WB_CCKP/projected-average-mean-s.csv`     | Projected future temperatures for Cambodia                              | World Bank (2025c)                                              | Included in package                    |




**Rights statement:** The authors confirm that they had legitimate access to all data used in the manuscript and have the right to include this data in the reproducibility package.

**Restrictions:** There are no restrictions on data access, publication, or storage.

---

## 4. Package Contents

```
/
├── README.md                                  # This file
├── KHM_shocks_EWS.prg                         # EViews program: extend standard Cambodia MFMod model to include climate extension, runs baseline and 24 shock scenarios
├── results_template.xlsx                      # Excel file used to compile results and produce paper charts
├── Data/           
│   ├── raw/                                   # Raw input data files from Koh and Galelli (2024) and World Bank (2025c)
│   │   ├──Koh_Galelli/         
│   │   │   ├── Q_m_avg.csv                    # Monthyl discharge data 
│   │   │   └── syscost_m.csv                  # Simulated electricity generation cost
│   │   └──WB_CVCKP/
│   │   │   └──projected-average-mean-s.csv    # Projected future temperatures for Cambodia
│   └── KHMSoln_clean.WF1                      # Cambodia MFMod model solution workfile (baseline)
└── outputs/                                   # Output folder — contains Excel Charts and Table template 
    └── EWS_MFMod_Template.xlsx                # Charts and Table Excel Template           
    
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

This will create a single model input file in ```./Data/Cambodia_MFMod_inputs.xlsx```. Individual impact channel data and corresponding display items (Figures 2—6 and Supplementary Tables 1—4) are written to subdirectories of ```./Data/input_channels```. Figures and tables are also copied to ```./results/display_items```.

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

Copy the GDP results displayed in the EViews output window (2015–2050, all scenarios) and paste them into the corresponding sheets in `./results/EWS_MFMod.xlsx`. 

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




