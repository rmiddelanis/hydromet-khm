' ==============================
' KHM shocks EWS - hydro, crops and flood damage
' Author: Unnada Chewpreecha
' Date: 29 Oct 2025
' ==============================
' Description:
' This program modifies the Cambodia (KHM) MFMod macroeconomic model to
' incorporate climate damage channels (floods, agriculture, hydropower/electricity),
' solves a baseline, and runs 24 shock scenarios across:
'   - 2 climate scenarios:  Optimistic (Opt), Pessimistic (Pes)
'   - 3 policy scenarios:   Control (CON), Status Quo (STQ), Improvement (IMP)
'   - 4 impact channels:    DRR (flood), ARG (agriculture), HYD (hydropower), ALL (combined)
' Output: GDP at market prices (NYGDPMKTPKN) for 2015-2050 across all scenarios.
' ==============================

close @all
logmode l

' Set working directory automatically to the folder where this program is run
%path = @runpath
cd %path

'------------------------------------------------------------------------
' SECTION 1: SETTINGS
'------------------------------------------------------------------------

' Sample period definitions
%solve_start = "2018"   ' Start of model solution period
%solve_end   = "2050"   ' End of model solution period
%fcst_end    = "2050"   ' End of forecast period
%dat_end     = "2024"   ' End of historical data
%fcst_start  = "2025"   ' Start of forecast period
%solve       = "g"      ' Solver method: Gauss-Seidel

' Country code
%cty = "KHM"

'------------------------------------------------------------------------
' SECTION 2: LOAD DATA
'------------------------------------------------------------------------

' Open Cambodia MFMod model solution workfile
wfopen .\Data\KHMSoln_clean.WF1

' Import damage input data from Excel (sheet: ForEViews)
' Series01 is used as the date identifier; #N/A treated as missing values
import .\Data\Cambodia_MFMod_inputs.xlsx range=ForEViews colhead=1 na="#N/A" @id @date(series01) @smpl @all

' Electricity shares used to convert hydropower savings into macro impacts
' Source: GTAP database
!elecshareIND = 0.01  ' Electricity share in intermediate consumption (industry)
!elecshareHH  = 0.019 ' Electricity share in household consumption

'------------------------------------------------------------------------
' SECTION 3: MODIFY SECTOR GVA EQUATIONS
'------------------------------------------------------------------------
' Replace sector GVA (Gross Value Added) level identities with share-based identities.
' This allows sector shares to be held constant in the forecast period,
' with GVA determined as: sector GVA = sector share x total GDP (factor cost).
' Sectors: Agriculture (AGR), Industry (IND), Services (SRV)

%sectors = "AGR IND SRV"

' Step 1: Calculate historical sector shares and replace model GVA identities
smpl @first %dat_end
for %s {%sectors}
    ' Calculate sector share of GDP at factor cost over the historical period
    series {%cty}NV{%s}TOT = {%cty}NV{%s}TOTLKN / {%cty}NYGDPFCSTKN

    ' Drop the existing level GVA identity from the model
    {%cty}.drop {%cty}NV{%s}TOTLKN

    ' Append new identity: sector GVA = share x total GDP at factor cost
    {%cty}.append @identity {%cty}NV{%s}TOTLKN = {%cty}NYGDPFCSTKN * {%cty}NV{%s}TOT
next

' Step 2: Set sector shares — hold constant at last historical value in the forecast period
for %s {%sectors}
    ' Fill share series over the full sample using actual data
    smpl @all
    series {%cty}NV{%s}TOT = ({%cty}NV{%s}TOTLKN / {%cty}NYGDPFCSTKN)

    ' In the forecast period, hold the share constant at the previous year's value
    smpl %fcst_start %fcst_end
    series {%cty}NV{%s}TOT = {%cty}NV{%s}TOT(-1)
next

smpl @all

'------------------------------------------------------------------------
' SECTION 4: INITIALISE CLIMATE DAMAGE VARIABLES
'------------------------------------------------------------------------
' All damage variables are initialised to zero (baseline = no damage).
' These will be overridden in the shock scenarios below.

series {%cty}AGDAMAGE      = 0 ' Agricultural TFP damage (share): land productivity loss due to climate change
series {%cty}YLDAMAGE      = 0 ' Labour productivity loss due to heat stress: Y = A*[(u*N)^a]*[K^(1-a)]
series {%cty}HLDAMAGE      = 0 ' Labour productivity loss due to health impacts
series {%cty}RBHOURS       = 0 ' Reduction in effective labour hours due to roads and bridges disruption
series {%cty}RBLOSTK       = 0 ' Capital stock loss from roads and bridges damage

' Repairable flood damage variables
series {%cty}NEFLOAVERKN_  = 0 ' Repairable flood damage to capital stock (% of existing capital stock)
series {%cty}FLODAMKN      = 0 ' Repairable flood damage to capital stock (real LCU, annual flow)
series {%cty}FLODSTKN      = 0 ' Repairable flood damage to capital stock (real LCU, cumulative stock net of repairs)
series {%cty}RECOVINVESTKN = 0 ' Investment diverted to repair damaged capital stock

' Permanent flood damage variables
series {%cty}PERMDAMKN     = 0 ' Permanent flood damage to capital stock (real LCU, annual flow)
series {%cty}PERMSTKN      = 0 ' Permanent flood damage to capital stock (real LCU, cumulative stock)
series {%cty}NEPERMAVERKN_ = 0 ' Permanent flood damage to capital stock (% of existing capital stock)

'------------------------------------------------------------------------
' SECTION 5: REPLACE MODEL IDENTITIES FOR CLIMATE DAMAGES
'------------------------------------------------------------------------

' Drop original potential GDP and capital stock identities (to be replaced below)
' NOTE: The PSTAR identity replacement is commented out below — retained for reference.
' {%cty}.DROP {%cty}PSTAR
{%cty}.DROP {%cty}NYGDPPOTLKN
{%cty}.DROP {%cty}NEGDIKSTKKN

' New potential GDP identity incorporating all damage channels:
'   - Agricultural damage (AGDAMAGE): reduces TFP
'   - Health damage (HLDAMAGE): reduces effective labour
'   - Heat/labour productivity damage (YLDAMAGE): reduces effective labour
'   - Roads & bridges disruption (RBHOURS): reduces effective labour hours
'   - Capital stock (lagged): standard Cobb-Douglas input
{%cty}.APPEND @IDENTITY {%cty}NYGDPPOTLKN = ((1+{%cty}AGDAMAGE)*(1+{%cty}HLDAMAGE)*(1+{%cty}YLDAMAGE)^({%cty}NYYWBTOTLCN_)) * {%cty}NYGDPTFP * (((1+{%cty}RBHOURS)*{%cty}SPPOP1564TO)^{%cty}NYYWBTOTLCN_) * ({%cty}NEGDIKSTKKN(-1)^(1 - {%cty}NYYWBTOTLCN_))

'------------------------------------------------------------------------
' SECTION 6: CAPITAL STOCK WITH FLOOD AND ROAD/BRIDGE DAMAGES
'------------------------------------------------------------------------
' Create NEGDIKSTKKN2: capital stock BEFORE damage, used as the base for damage calculations.
' NEGDIKSTKKN (the model's capital stock) will then be adjusted downward for actual damages.

' Find the first year of capital stock data and initialise NEGDIKSTKKN2
series myear = @year
!stDate1 = @ifirst({%cty}NEGDIKSTKKN)
%stDate  = @str(myear(!stDate1))

smpl %stDate %stDate
series {%cty}NEGDIKSTKKN2 = {%cty}NEGDIKSTKKN

' Build NEGDIKSTKKN2 forward using the standard perpetual inventory method
smpl %stDate+1 %dat_end
{%cty}NEGDIKSTKKN2 = {%cty}NEGDIKSTKKN2(-1) * (1 - {%cty}DEPR) + {%cty}NEGDIFTOTKN - {%cty}RECOVINVESTKN

' NOTE: Over the historical period, set NEGDIKSTKKN2 = NEGDIKSTKKN (actual data).
'       This handles missing early-year investment data (as in the original KHM model setup).
smpl %stDate %dat_end
{%cty}NEGDIKSTKKN2 = {%cty}NEGDIKSTKKN

smpl @all

' --- Repairable flood damage identities ---
' Annual repairable damage flow (convert % of capital stock to real LCU)
' Note: NEFLOAVERKN_ should be positive to represent damage
{%cty}.APPEND @IDENTITY {%cty}FLODAMKN = {%cty}NEFLOAVERKN_ * {%cty}NEGDIKSTKKN2

' Cumulative stock of repairable damage net of repairs
' Capped at 90% of capital stock to avoid unrealistic solutions
{%cty}.APPEND @IDENTITY {%cty}FLODSTKN = @recode( {%cty}FLODSTKN(-1) + {%cty}FLODAMKN - {%cty}RECOVINVESTKN > 0.9 * {%cty}NEGDIKSTKKN2, 0.9 * {%cty}NEGDIKSTKKN2, {%cty}FLODSTKN(-1) + {%cty}FLODAMKN - {%cty}RECOVINVESTKN)

' Recovery investment: amount of total investment diverted to repair damaged stock
' Assumption: up to 50% of total investment can be channelled into reconstruction
{%cty}.APPEND @IDENTITY {%cty}RECOVINVESTKN = @recode({%cty}FLODSTKN(-1) > 0.5 * {%cty}NEGDIFTOTKN, 0.5 * {%cty}NEGDIFTOTKN, {%cty}FLODSTKN(-1))

' --- Permanent flood damage identities ---
' Annual permanent damage flow (convert % of capital stock to real LCU)
' Note: NEPERMAVERKN_ should be positive to represent damage
{%cty}.APPEND @IDENTITY {%cty}PERMDAMKN = {%cty}NEPERMAVERKN_ * {%cty}NEGDIKSTKKN2

' Cumulative permanent damage stock (depreciates but is never repaired)
{%cty}.APPEND @IDENTITY {%cty}PERMSTKN = (1 - {%cty}DEPR) * {%cty}PERMSTKN(-1) + {%cty}PERMDAMKN

' --- EWS adaptation costs ---
' Initialise CAPEX (one-off investment cost) and OPEX (recurring operational cost) to zero.
' These will be overridden in shock scenarios to reflect EWS implementation costs.
series {%cty}CAPEX = 0.0
series {%cty}OPEX  = 0.0

' --- Updated capital stock identities ---
' NEGDIKSTKKN2: pre-damage capital stock
' Reconstruction spending (RECOVINVESTKN) and EWS capital cost (CAPEX) are excluded
' from productive capital formation (they divert investment away from new capital)
{%cty}.append @IDENTITY {%cty}NEGDIKSTKKN2 = {%cty}NEGDIKSTKKN2(-1) * (1 - {%cty}DEPR) + {%cty}NEGDIFTOTKN - {%cty}RECOVINVESTKN - {%cty}CAPEX

' NEGDIKSTKKN: effective (post-damage) capital stock
' Repairable flood damage reduces effective capital proportionally (power function of share lost)
' Roads/bridges damage (RBLOSTK) and permanent damage (PERMSTKN) are subtracted directly
{%cty}.append @IDENTITY {%cty}NEGDIKSTKKN = (1 - ({%cty}FLODSTKN / {%cty}NEGDIKSTKKN2))^(1 / (1 - (1 - {%cty}NYYWBTOTLCN_))) * {%cty}NEGDIKSTKKN2 + {%cty}RBLOSTK - {%cty}PERMSTKN

' Update the model object with all new identities
{%cty}.update

'------------------------------------------------------------------------
' SECTION 7: SOLVE BASELINE
'------------------------------------------------------------------------

smpl @all

' Clean up any previous scenario add-factor or override series
delete *_a *_0

smpl %solve_start %fcst_end

' Add stochastic add-factors and initialise for baseline solve
{%cty}.addassign(i,c) @stochastic
{%cty}.addinit(v=n) @stochastic

{%cty}.scenario "Baseline"
{%cty}.solve(s=d, d=d, o={%solve}, i=a, c=1e-6, f=t, v=t, g=n)
logmsg "Solved baseline with damage equations for: " + %cty 

' Extract baseline endogenous variable list and store baseline values
%endos = {%cty}.@endoglist

smpl %solve_start %fcst_end
for %var {%endos}
    series {%var} = {%var}_0
next

smpl @all

'------------------------------------------------------------------------
' SECTION 8: RUN SHOCK SCENARIOS
'------------------------------------------------------------------------
' Scenario naming convention:
'   Scenario number = !k (climate) + !i (policy) + !j (channel)
'   Optimistic (!k=100), Pessimistic (!k=200)
'   Control (!i=10), Status Quo (!i=20), Improvement (!i=30)
'   DRR (!j=1), ARG (!j=2), HYD (!j=3), ALL (!j=4)
' Example: Opt + STQ + HYD = 100 + 20 + 3 = scenario 123

' Initialise output string with baseline GDP series
%toprint = "KHMNYGDPMKTPKN_0 "

!k = 100 ' Climate scenario counter: 100 = Optimistic, 200 = Pessimistic
for %a Opt Pes

    !i = 10 ' Policy scenario counter: 10 = CON, 20 = STQ, 30 = IMP
    for %b CON STQ IMP

        !j = 1 ' Impact channel counter: 1=DRR, 2=ARG, 3=HYD, 4=ALL
        for %c DRR ARG HYD ALL

            !scen = !k + !i + !j ' Unique scenario identifier

            ' --- Initialise all shock override series to baseline values ---
            smpl @all
            series {%cty}NEFLOAVERKN__!scen  = {%cty}NEFLOAVERKN_  ' Repairable flood damage (% capital stock)
            series {%cty}AGDAMAGE_!scen       = {%cty}AGDAMAGE       ' Agricultural TFP damage
            series {%cty}NVAGRTOT_!scen       = {%cty}NVAGRTOT       ' Total agricultural GVA
            series {%cty}CAPEX_!scen          = {%cty}CAPEX          ' EWS capital investment cost
            series {%cty}GGEXPCAPTCN_!scen    = {%cty}GGEXPCAPTCN    ' Government capital expenditure
            series {%cty}OPEX_!scen           = {%cty}OPEX           ' EWS operational cost
            series {%cty}NECONPRVTXN_A_!scen  = {%cty}NECONPRVTXN_A  ' Consumer price add-factor
            series {%cty}NYGDPCPSHXN_A_!scen  = {%cty}NYGDPCPSHXN_A  ' GDP deflator/production cost add-factor

            ' === DRR: Disaster Risk Reduction (flood damage only) ===
            if %c == "DRR" then
                smpl 2020 2050
                ' Apply flood damage reduction (input as % ? divide by 100)
                {%cty}NEFLOAVERKN__!scen = DRR{%b}_{%a} / 100
                ' Convert EWS capital cost from 2025 USD to millions of real LCU
                {%cty}CAPEX_!scen = (CAPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                ' Add EWS CAPEX to government investment (CAPEX already in LCU, convert using private consumption deflator)
                {%cty}GGEXPCAPTCN_!scen = {%cty}GGEXPCAPTCN + ({%cty}CAPEX_!scen) * {%cty}NECONPRVTXN
                ' Convert EWS operational cost from 2025 USD to millions of real LCU
                {%cty}OPEX_!scen = (OPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                ' Pass OPEX through to consumer prices (change in real per-capita OPEX cost)
                {%cty}NECONPRVTXN_A_!scen = {%cty}NECONPRVTXN_A + D(({%cty}OPEX_!scen * {%cty}NECONPRVTXN) / {%cty}NECONPRVTKN(-1))
            endif

            ' === ARG: Agriculture (crop damage only) ===
            if %c == "ARG" then
                smpl 2020 2050
                ' Agricultural damage as a share of total agricultural GVA
                {%cty}AGDAMAGE_!scen = ARG{%b}_{%a} / 100 * {%cty}NVAGRTOT
                ' Adjust total agricultural GVA for the damage
                {%cty}NVAGRTOT_!scen = {%cty}NVAGRTOT + {%cty}AGDAMAGE_!scen
                ' EWS costs (same conversion as DRR)
                {%cty}CAPEX_!scen = (CAPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                {%cty}GGEXPCAPTCN_!scen = {%cty}GGEXPCAPTCN + ({%cty}CAPEX_!scen) * {%cty}NECONPRVTXN
                {%cty}OPEX_!scen = (OPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                {%cty}NECONPRVTXN_A_!scen = {%cty}NECONPRVTXN_A + D(({%cty}OPEX_!scen * {%cty}NECONPRVTXN) / {%cty}NECONPRVTKN(-1))
            endif

            ' === HYD: Hydropower/electricity (production cost and consumer price effects) ===
            if %c == "HYD" then
                smpl 2020 2050
                ' Reduction in electricity costs to intermediate production (scaled by industry electricity share)
                {%cty}NYGDPCPSHXN_A_!scen = {%cty}NYGDPCPSHXN_A - (HYD{%b}_{%a} / 100 * !elecshareIND)
                ' EWS costs (same conversion as DRR)
                {%cty}CAPEX_!scen = (CAPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                {%cty}GGEXPCAPTCN_!scen = {%cty}GGEXPCAPTCN + ({%cty}CAPEX_!scen) * {%cty}NECONPRVTXN
                {%cty}OPEX_!scen = (OPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                ' Consumer price: OPEX cost plus reduction in household electricity prices
                {%cty}NECONPRVTXN_A_!scen = {%cty}NECONPRVTXN_A + D(({%cty}OPEX_!scen * {%cty}NECONPRVTXN) / {%cty}NECONPRVTKN(-1)) - (HYD{%b}_{%a} / 100 * !elecshareHH)
            endif

            ' === ALL: Combined (DRR + ARG + HYD) ===
            if %c == "ALL" then
                smpl 2020 2050
                ' Flood damage reduction
                {%cty}NEFLOAVERKN__!scen = DRR{%b}_{%a} / 100
                ' Agricultural damage
                {%cty}AGDAMAGE_!scen = ARG{%b}_{%a} / 100 * {%cty}NVAGRTOT
                {%cty}NVAGRTOT_!scen = {%cty}NVAGRTOT + {%cty}AGDAMAGE_!scen
                ' EWS costs (same conversion as above)
                {%cty}CAPEX_!scen = (CAPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                {%cty}GGEXPCAPTCN_!scen = {%cty}GGEXPCAPTCN + ({%cty}CAPEX_!scen) * {%cty}NECONPRVTXN
                {%cty}OPEX_!scen = (OPEX{%b}_{%a} * @elem(KHMPANUSATLS,"2025")) / 1000000
                ' Consumer price: OPEX plus household electricity savings
                {%cty}NECONPRVTXN_A_!scen = {%cty}NECONPRVTXN_A + D(({%cty}OPEX_!scen * {%cty}NECONPRVTXN) / {%cty}NECONPRVTKN(-1)) - (HYD{%b}_{%a} / 100 * !elecshareHH)
                ' Reduction in electricity costs to intermediate production
                {%cty}NYGDPCPSHXN_A_!scen = {%cty}NYGDPCPSHXN_A - (HYD{%b}_{%a} / 100 * !elecshareIND)
            endif

            ' --- Define and solve scenario ---
            ' Create a new named scenario with alias suffix = !scen
            {%cty}.scenario(n, a=!scen) EWS{%b}_{%a}_{%c}

            smpl %solve_start %fcst_end

            ' Override and exclude the shocked variables so the solver uses scenario values
            {%cty}.OVERRIDE {%cty}NEFLOAVERKN_ {%cty}AGDAMAGE {%cty}NVAGRTOT {%cty}CAPEX {%cty}GGEXPCAPTCN {%cty}NECONPRVTXN_A {%cty}NYGDPCPSHXN_A
            {%cty}.EXCLUDE  {%cty}NEFLOAVERKN_ {%cty}AGDAMAGE {%cty}NVAGRTOT {%cty}CAPEX {%cty}GGEXPCAPTCN {%cty}NECONPRVTXN_A {%cty}NYGDPCPSHXN_A

            ' Solve relative to Baseline
            {%cty}.SCENARIO(C) "BASELINE"
            {%cty}.solve(s=d, d=d, o={%solve}, i=a, g=n)

            logmsg Solved scenario EWS{%b}_{%a}_{%c} !scen

            ' Append this scenario's GDP series to the display list
            ' Note: comment corrected from "disply" to "display"
            %toprint = %toprint + %cty + "NYGDPMKTPKN_" + @str(!scen) + " "

            !j = !j + 1  ' Increment impact channel counter
        next ' %c: impact channel

        !i = !i + 10 ' Increment policy scenario counter
    next ' %b: policy scenario

    !k = !k + 100 ' Increment climate scenario counter
next ' %a: climate scenario

'------------------------------------------------------------------------
' SECTION 9: DISPLAY RESULTS
'------------------------------------------------------------------------
' Show GDP at market prices (constant LCU) for baseline and all 24 scenarios, 2015-2050

smpl 2015 2050
show {%toprint} 'Copy this table to Excel results template in \output folder

