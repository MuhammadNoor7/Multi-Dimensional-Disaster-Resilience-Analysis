import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

EMDAT_FILE='public_emdat_incl_hist_2025-11-24 (1).xlsx'
WORLDBANK_FILE='World_Bank_Indicators.csv'
HDI_FILE='hdr-data.xlsx'
WGI_FILE='wgi.csv'
URBAN_FILE='urban.csv'
OWID_FILE='decadal-average-annual-number-of-deaths-from-disasters.csv'

OUTPUT_FILE='resilience_under_pressure.csv'

# Severity weights by disaster type (for Disaster Impact Index)
SEVERITY_WEIGHTS = {
    'Earthquake': 1.5,
    'Tsunami': 1.6,
    'Volcanic activity': 1.4,
    'Mass movement (dry)': 1.3,
    'Mass movement (wet)': 1.2,
    'Flood': 1.0,
    'Storm': 1.1,
    'Extreme temperature': 1.0,
    'Drought': 1.2,
    'Wildfire': 1.1,
    'Epidemic': 1.4,
    'Insect infestation': 0.7,
    'Animal incident': 0.6,
    'Industrial accident': 0.9,
    'Transport accident': 0.8,
    'Miscellaneous accident': 0.7,
    'Complex disasters': 1.3,
    'Famine': 1.5,
}


#Step 1: LOADING AND PREPROCESSING INDIVIDUAL DATASETS
COUNTRY_MAPPING={
    'United States of America':'United States','USA':'United States',
    'US':'United States','Korea, Rep.':'South Korea',
    'Korea, Democratic People\'s Republic of':'North Korea',
    'Russian Federation':'Russia',
    'Iran, Islamic Rep.':'Iran',
    'Egypt, Arab Rep.':'Egypt',
    'Venezuela, RB':'Venezuela',
    'Syrian Arab Republic':'Syria',
    'Lao PDR':'Laos',
    'Congo, Dem. Rep.':'Democratic Republic of Congo',
    'Congo, Rep.':'Republic of Congo',
    'Yemen, Rep.':'Yemen',
    'Türkiye':'Turkey',
    'Czechia':'Czech Republic',
    'Slovak Republic':'Slovakia',
    'Viet Nam':'Vietnam',
    'Myanmar (Burma)':'Myanmar',
}

#standardizing country names
def standardize_country_name(country):
    if pd.isna(country):
        return None
    country=str(country).strip()
    return COUNTRY_MAPPING.get(country,country)

#funcs for loading individual datasets
def load_emdat():
    print("\nLoading EM-DAT.....")
    em_df= pd.read_excel(EMDAT_FILE)
    
    #merging start year and end year into single 'Year' column
    em_df['Year']=em_df['Start Year'].fillna(em_df['End Year'])

    # Rename columns to standard format
    final_em_df=em_df.rename(columns={
        'Country':'country',
        'Year':'year',
        'Disaster Type':'disaster_type',
        'Total Deaths':'fatalities',
        'Total Affected':'affected',
        'Total Damage (\'000 US$)':'economic_loss'
    })
    
    final_em_df['country']=final_em_df['country'].apply(standardize_country_name)
    final_em_df['year']=pd.to_numeric(final_em_df['year'],errors='coerce').astype(int)
    final_em_df['fatalities']=pd.to_numeric(final_em_df['fatalities'],errors='coerce')
    final_em_df['affected']=pd.to_numeric(final_em_df['affected'],errors='coerce')
    final_em_df['economic_loss']=pd.to_numeric(final_em_df['economic_loss'],errors='coerce')
    
    print(f"Loaded {len(final_em_df)} disaster events into Merged Dataset.")
    return final_em_df

def load_worldbank():

    print("\nLoading World Bank.....")
    wb_df=pd.read_csv(WORLDBANK_FILE)
    
    #country is  named as 'Country Name' in WB dataset and year is named as Time Code
    wb_df=wb_df.rename(columns={'Country Name':'Country','Time':'Year'})
    wb_df=wb_df.rename(columns={
        'Country':'country',
        'Year':'year',
        'GDP (current US$) [NY.GDP.MKTP.CD]':'gdp',
        'Population, total [SP.POP.TOTL]':'population',
        'GDP per capita (current US$) [NY.GDP.PCAP.CD]':'gdp_per_capita'
    })
    
    wb_df['country']=wb_df['country'].apply(standardize_country_name)
    wb_df['year']=pd.to_numeric(wb_df['year'],errors='coerce')
    wb_df['gdp']=pd.to_numeric(wb_df['gdp'],errors='coerce')
    wb_df['population']=pd.to_numeric(wb_df['population'],errors='coerce')
    wb_df['gdp_per_capita']=pd.to_numeric(wb_df['gdp_per_capita'],errors='coerce')
    
    print(f"Loaded {len(wb_df)} economic records into Merged Dataset.")
    return wb_df

def load_owid():
    print("\nLoading OWID.....")
    
    owid_df=pd.read_csv(OWID_FILE)
    
    owid_df=owid_df.rename(columns={'Country name':'Country'})
    owid_df=owid_df.rename(columns={
        'Country':'country',
        'Year':'year',
        'Number of deaths from disasters':'owid_deaths'
    })
    
    owid_df['country']=owid_df['country'].apply(standardize_country_name)
    owid_df['year']=pd.to_numeric(owid_df['year'],errors='coerce').fillna(0)
    owid_df['owid_deaths']=pd.to_numeric(owid_df['owid_deaths'],errors='coerce').fillna(0)
    
    print(f"Loaded {len(owid_df)} OWID records into Merged Dataset.")
    return owid_df

def load_hdi():
    """Load Human Development Index data (historical, 1990-2023)"""
    print("\nLoading HDI Data.....")
    
    try:
        hdi_df = pd.read_excel(HDI_FILE)
        
        # Filter for HDI values only (Human Development Index)
        hdi_values = hdi_df[hdi_df['indicator'] == 'Human Development Index (value)'].copy()
        
        # Rename and select relevant columns
        hdi_values = hdi_values[['country', 'year', 'value']].copy()
        hdi_values.columns = ['country', 'year', 'hdi']
        
        hdi_values['country'] = hdi_values['country'].apply(standardize_country_name)
        hdi_values['year'] = pd.to_numeric(hdi_values['year'], errors='coerce')
        hdi_values['hdi'] = pd.to_numeric(hdi_values['hdi'], errors='coerce')
        
        # Drop any rows with missing country/year
        hdi_values = hdi_values.dropna(subset=['country', 'year'])
        
        print(f"Loaded {len(hdi_values)} HDI records.")
        print(f"  Countries: {hdi_values['country'].nunique()}, Years: {int(hdi_values['year'].min())}-{int(hdi_values['year'].max())}")
        return hdi_values
        
    except Exception as e:
        print(f"  Warning: Could not load HDI data: {e}")
        return pd.DataFrame(columns=['country', 'year', 'hdi'])

def load_wgi():
    """Load World Governance Indicators data"""
    print("\nLoading WGI Data.....")
    
    wgi_df = pd.read_csv(WGI_FILE)
    
    # Filter for the 6 main governance estimate indicators
    governance_indicators = [
        'Control of Corruption: Estimate',
        'Government Effectiveness: Estimate',
        'Political Stability and Absence of Violence/Terrorism: Estimate',
        'Regulatory Quality: Estimate',
        'Rule of Law: Estimate',
        'Voice and Accountability: Estimate'
    ]
    
    wgi_filtered = wgi_df[wgi_df['Series Name'].isin(governance_indicators)].copy()
    
    # Melt the year columns into rows
    year_cols = [col for col in wgi_filtered.columns if '[YR' in col]
    
    wgi_melted = pd.melt(
        wgi_filtered,
        id_vars=['Country Name', 'Country Code', 'Series Name'],
        value_vars=year_cols,
        var_name='year_raw',
        value_name='value'
    )
    
    # Extract year from column name (e.g., '2010 [YR2010]' -> 2010)
    wgi_melted['year'] = wgi_melted['year_raw'].str.extract(r'(\d{4})').astype(float)
    wgi_melted['value'] = pd.to_numeric(wgi_melted['value'], errors='coerce')
    
    # Pivot to get one column per indicator
    wgi_pivot = wgi_melted.pivot_table(
        index=['Country Name', 'year'],
        columns='Series Name',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Rename columns
    wgi_pivot = wgi_pivot.rename(columns={
        'Country Name': 'country',
        'Control of Corruption: Estimate': 'wgi_corruption',
        'Government Effectiveness: Estimate': 'wgi_gov_effectiveness',
        'Political Stability and Absence of Violence/Terrorism: Estimate': 'wgi_pol_stability',
        'Regulatory Quality: Estimate': 'wgi_reg_quality',
        'Rule of Law: Estimate': 'wgi_rule_of_law',
        'Voice and Accountability: Estimate': 'wgi_voice_accountability'
    })
    
    wgi_pivot['country'] = wgi_pivot['country'].apply(standardize_country_name)
    
    # Calculate composite governance index (average of all 6 indicators, normalized to 0-1)
    gov_cols = ['wgi_corruption', 'wgi_gov_effectiveness', 'wgi_pol_stability', 
                'wgi_reg_quality', 'wgi_rule_of_law', 'wgi_voice_accountability']
    # WGI scores range from -2.5 to 2.5, normalize to 0-1
    wgi_pivot['governance_index'] = (wgi_pivot[gov_cols].mean(axis=1) + 2.5) / 5.0
    
    print(f"Loaded {len(wgi_pivot)} WGI records.")
    return wgi_pivot

def load_urban():
    """Load Urban Population percentage data"""
    print("\nLoading Urban Population Data.....")
    
    # Skip the first 4 rows (metadata)
    urban_df = pd.read_csv(URBAN_FILE, skiprows=4)
    
    # Keep only relevant columns (Country Name, Country Code, and year columns)
    id_cols = ['Country Name', 'Country Code']
    year_cols = [col for col in urban_df.columns if col.isdigit() or (col.replace('.', '').isdigit())]
    
    # Melt to long format
    urban_melted = pd.melt(
        urban_df,
        id_vars=id_cols,
        value_vars=[col for col in urban_df.columns if col not in id_cols and col not in ['Indicator Name', 'Indicator Code', 'Unnamed: 69']],
        var_name='year',
        value_name='urban_pop_pct'
    )
    
    urban_melted['year'] = pd.to_numeric(urban_melted['year'], errors='coerce')
    urban_melted['urban_pop_pct'] = pd.to_numeric(urban_melted['urban_pop_pct'], errors='coerce')
    
    urban_melted = urban_melted.rename(columns={'Country Name': 'country'})
    urban_melted['country'] = urban_melted['country'].apply(standardize_country_name)
    
    urban_final = urban_melted[['country', 'year', 'urban_pop_pct']].dropna(subset=['year'])
    
    print(f"Loaded {len(urban_final)} Urban Population records.")
    return urban_final

# STEP 2: DOING DATA FUSION ON COUNTRY-YEAR PAIRS
def fuse_datasets(): 
    #loading all individual datasets
    emd_df=load_emdat()
    wb_df=load_worldbank()
    owid_df=load_owid()
    hdi_df=load_hdi()
    wgi_df=load_wgi()
    urban_df=load_urban()
    
    print("\n"+"="*60)
    print("MERGING ON COUNTRY-YEAR PAIRS")
    print("="*60)
    
    fused_df=emd_df.copy()
    print(f"\nBase (EM-DAT) Before Merging: {len(fused_df)} Rows.")
    
    #now merging datasets one by one on country-year pairs
    fused_df=pd.merge(fused_df,wb_df,on=['country','year'],how='left')
    print(f"After World Bank Merging: {len(fused_df)} Rows.")
    
    fused_df=pd.merge(fused_df,owid_df,on=['country','year'],how='left')
    print(f"After OWID Merging: {len(fused_df)} Rows.")
    
    fused_df=pd.merge(fused_df,hdi_df,on=['country','year'],how='left')
    print(f"After HDI Merging: {len(fused_df)} Rows.")
    
    fused_df=pd.merge(fused_df,wgi_df,on=['country','year'],how='left')
    print(f"After WGI Merging: {len(fused_df)} Rows.")
    
    fused_df=pd.merge(fused_df,urban_df,on=['country','year'],how='left')
    print(f"After Urban Pop Merging: {len(fused_df)} Rows.")
    
    fused_df = fused_df.dropna(subset=['country','year'])
    print(f"\nFinal fused dataset: {len(fused_df)} Rows After Dropping Missing Country-Year Pairs.")
    print(f"\nCountries: {fused_df['country'].nunique()}")
    print(f"\nYear range: {fused_df['year'].min()} - {fused_df['year'].max()}")
    
    return fused_df

# STEP 3: FEATURE ENGINEERING
def engineer_features(df):
    """
    Create derived features for disaster resilience analysis:
    1. Annualized disaster frequency (per country)
    2. Average economic loss per event (normalized by GDP)
    3. Recovery rate (GDP growth rate change)
    4. Infrastructure exposure (urbanization × hazard intensity proxy)
    5. Human cost ratio (fatalities per 100k population)
    6. Severity weight based on disaster type
    7. Disaster Impact Index (DII)
    8. Resilience Recovery Score (RRS) - simplified
    9. Composite Resilience Index (CRI)
    """
    print("\n"+"="*60)
    print("FEATURE ENGINEERING")
    print("="*60)
    
    fe_df = df.copy()
    
    # ------------------------------------------------------------------
    # 1. SEVERITY WEIGHT (S) - based on disaster type
    # ------------------------------------------------------------------
    fe_df['severity_weight'] = fe_df['disaster_type'].map(SEVERITY_WEIGHTS).fillna(1.0)
    print("✓ Added: severity_weight")
    
    # ------------------------------------------------------------------
    # 2. HUMAN COST RATIO - Fatalities per 100k population
    # ------------------------------------------------------------------
    fe_df['human_cost_ratio'] = np.where(
        fe_df['population'] > 0,
        (fe_df['fatalities'] / fe_df['population']) * 100000,
        np.nan
    )
    print("✓ Added: human_cost_ratio (fatalities per 100k population)")
    
    # ------------------------------------------------------------------
    # 3. AFFECTED POPULATION PERCENTAGE
    # ------------------------------------------------------------------
    fe_df['affected_pop_pct'] = np.where(
        fe_df['population'] > 0,
        (fe_df['affected'] / fe_df['population']) * 100,
        np.nan
    )
    print("✓ Added: affected_pop_pct (% of population affected)")
    
    # ------------------------------------------------------------------
    # 4. ECONOMIC LOSS NORMALIZED BY GDP
    # ------------------------------------------------------------------
    # economic_loss is in '000 US$, gdp is in US$
    fe_df['economic_loss_gdp_pct'] = np.where(
        fe_df['gdp'] > 0,
        (fe_df['economic_loss'] * 1000 / fe_df['gdp']) * 100,
        np.nan
    )
    print("✓ Added: economic_loss_gdp_pct (economic loss as % of GDP)")
    
    # ------------------------------------------------------------------
    # 5. ANNUALIZED DISASTER FREQUENCY (per country per year)
    # ------------------------------------------------------------------
    disaster_freq = fe_df.groupby(['country', 'year']).size().reset_index(name='disaster_frequency')
    fe_df = pd.merge(fe_df, disaster_freq, on=['country', 'year'], how='left')
    print("✓ Added: disaster_frequency (number of disasters per country-year)")
    
    # ------------------------------------------------------------------
    # 6. GDP GROWTH RATE CHANGE (Recovery Rate Proxy)
    # Calculate YoY GDP growth change as a proxy for recovery
    # ------------------------------------------------------------------
    fe_df['gdp_growth'] = pd.to_numeric(fe_df.get('GDP growth (annual %) [NY.GDP.MKTP.KD.ZG]', np.nan), errors='coerce')
    
    # Calculate lagged GDP growth (previous year)
    fe_df = fe_df.sort_values(['country', 'year'])
    fe_df['gdp_growth_prev'] = fe_df.groupby('country')['gdp_growth'].shift(1)
    fe_df['gdp_growth_change'] = fe_df['gdp_growth'] - fe_df['gdp_growth_prev']
    print("✓ Added: gdp_growth_change (recovery rate proxy: post - pre growth)")
    
    # ------------------------------------------------------------------
    # 7. INFRASTRUCTURE EXPOSURE (Urbanization × Disaster Frequency)
    # Higher urbanization + more disasters = higher infrastructure exposure
    # ------------------------------------------------------------------
    fe_df['infrastructure_exposure'] = (fe_df['urban_pop_pct'] / 100) * fe_df['disaster_frequency']
    print("✓ Added: infrastructure_exposure (urbanization × disaster frequency)")
    
    # ------------------------------------------------------------------
    # 8. DISASTER IMPACT INDEX (DII)
    # DII = ((F + Apop) / GDPpc) × S
    # Where F = fatalities per million, Apop = affected %, GDPpc = GDP per capita
    # ------------------------------------------------------------------
    fe_df['fatalities_per_million'] = np.where(
        fe_df['population'] > 0,
        (fe_df['fatalities'] / fe_df['population']) * 1_000_000,
        np.nan
    )
    
    fe_df['disaster_impact_index'] = np.where(
        fe_df['gdp_per_capita'] > 0,
        ((fe_df['fatalities_per_million'].fillna(0) + fe_df['affected_pop_pct'].fillna(0)) / fe_df['gdp_per_capita']) * fe_df['severity_weight'],
        np.nan
    )
    print("✓ Added: disaster_impact_index (DII)")
    
    # ------------------------------------------------------------------
    # 9. RESILIENCE RECOVERY SCORE (RRS) - Simplified
    # RRS = gdp_growth_change + (HDI + governance_index) / 2
    # ------------------------------------------------------------------
    fe_df['rrs_institutional'] = (fe_df['hdi'].fillna(0) + fe_df['governance_index'].fillna(0)) / 2
    fe_df['resilience_recovery_score'] = fe_df['gdp_growth_change'].fillna(0) + fe_df['rrs_institutional']
    print("✓ Added: resilience_recovery_score (RRS)")
    
    # ------------------------------------------------------------------
    # 10. ADAPTIVE CAPACITY (A)
    # Composite of HDI, governance, and urban infrastructure
    # ------------------------------------------------------------------
    fe_df['adaptive_capacity'] = (
        fe_df['hdi'].fillna(0) * 0.4 +
        fe_df['governance_index'].fillna(0) * 0.4 +
        (fe_df['urban_pop_pct'].fillna(0) / 100) * 0.2
    )
    print("✓ Added: adaptive_capacity (A)")
    
    # ------------------------------------------------------------------
    # 11. EXPOSURE (E) - Disaster frequency × average severity
    # ------------------------------------------------------------------
    fe_df['exposure'] = fe_df['disaster_frequency'] * fe_df['severity_weight']
    print("✓ Added: exposure (E = frequency × severity)")
    
    # ------------------------------------------------------------------
    # 12. VULNERABILITY (V) - Impact per capita or GDP
    # Normalized DII (min-max scaling within dataset)
    # ------------------------------------------------------------------
    dii_min = fe_df['disaster_impact_index'].min()
    dii_max = fe_df['disaster_impact_index'].max()
    fe_df['vulnerability'] = np.where(
        dii_max > dii_min,
        (fe_df['disaster_impact_index'] - dii_min) / (dii_max - dii_min),
        0
    )
    # Ensure minimum vulnerability of 0.01 to avoid division by zero
    fe_df['vulnerability'] = fe_df['vulnerability'].clip(lower=0.01)
    print("✓ Added: vulnerability (V = normalized DII)")
    
    # ------------------------------------------------------------------
    # 13. COMPOSITE RESILIENCE INDEX (CRI)
    # CRI = A / (E × V)
    # Higher CRI = greater resilience
    # ------------------------------------------------------------------
    fe_df['composite_resilience_index'] = np.where(
        (fe_df['exposure'] > 0) & (fe_df['vulnerability'] > 0),
        fe_df['adaptive_capacity'] / (fe_df['exposure'] * fe_df['vulnerability']),
        np.nan
    )
    print("✓ Added: composite_resilience_index (CRI = A / (E × V))")
    
    # ------------------------------------------------------------------
    # 14. DATA QUALITY FLAGS
    # ------------------------------------------------------------------
    fe_df['flag_missing_gdp'] = fe_df['gdp'].isna().astype(int)
    fe_df['flag_missing_population'] = fe_df['population'].isna().astype(int)
    fe_df['flag_missing_hdi'] = fe_df['hdi'].isna().astype(int)
    fe_df['flag_missing_governance'] = fe_df['governance_index'].isna().astype(int)
    fe_df['flag_missing_urban'] = fe_df['urban_pop_pct'].isna().astype(int)
    fe_df['data_quality_score'] = 1 - (fe_df[['flag_missing_gdp', 'flag_missing_population', 
                                               'flag_missing_hdi', 'flag_missing_governance', 
                                               'flag_missing_urban']].mean(axis=1))
    print("✓ Added: data quality flags and score")
    
    print(f"\nFeature engineering complete. Total columns: {len(fe_df.columns)}")
    
    return fe_df

#STEP 4: SAVING FUSED DATASET TO CSV
def save_to_csv(df):
    print("\n"+"="*60)
    print("SAVING TO CSV")
    print("="*60)
    
    try:
        df.to_csv(OUTPUT_FILE,index=False)
        print(f"Saving {len(df)} Rows to '{OUTPUT_FILE}'")
        
    except Exception as e:
        print(f"Error saving file:{e}")

def print_feature_summary(df):
    """Print summary of engineered features"""
    print("\n"+"="*60)
    print("ENGINEERED FEATURES SUMMARY")
    print("="*60)
    
    feature_cols = [
        'severity_weight', 'human_cost_ratio', 'affected_pop_pct',
        'economic_loss_gdp_pct', 'disaster_frequency', 'gdp_growth_change',
        'infrastructure_exposure', 'fatalities_per_million', 'disaster_impact_index',
        'resilience_recovery_score', 'adaptive_capacity', 'exposure',
        'vulnerability', 'composite_resilience_index', 'data_quality_score'
    ]
    
    print(f"\n{'Feature':<35} {'Non-Null':<12} {'Mean':<15} {'Min':<15} {'Max':<15}")
    print("-" * 92)
    
    for col in feature_cols:
        if col in df.columns:
            non_null = df[col].notna().sum()
            mean_val = df[col].mean() if df[col].notna().any() else np.nan
            min_val = df[col].min() if df[col].notna().any() else np.nan
            max_val = df[col].max() if df[col].notna().any() else np.nan
            print(f"{col:<35} {non_null:<12} {mean_val:<15.4f} {min_val:<15.4f} {max_val:<15.4f}")

# main func
if __name__ == "__main__":
    print("="*60)
    print("RESILIENCE UNDER PRESSURE DATA FUSION PROCESSING")
    print("="*60)
    
    # Step 1-2: Load and fuse datasets
    fused_df = fuse_datasets()
    
    # Step 3: Feature engineering
    final_df = engineer_features(fused_df)
    
    # Step 4: Save to CSV
    save_to_csv(final_df)
    
    # Print summaries
    print_feature_summary(final_df)

    print("\n"+"="*60)
    print("SAMPLE DATA (First 5 rows):")
    print("="*60)
    print(final_df.head())
    
    print("\n"+"="*60)
    print("ALL COLUMNS IN FINAL DATASET:")
    print("="*60)
    print(final_df.columns.tolist())
    
    print("\n"+"="*60)
    print("NEW ENGINEERED FEATURES:")
    print("="*60)
    new_features = [
        'severity_weight', 'human_cost_ratio', 'affected_pop_pct',
        'economic_loss_gdp_pct', 'disaster_frequency', 'gdp_growth_change',
        'infrastructure_exposure', 'fatalities_per_million', 'disaster_impact_index',
        'resilience_recovery_score', 'adaptive_capacity', 'exposure',
        'vulnerability', 'composite_resilience_index', 'data_quality_score'
    ]
    for f in new_features:
        print(f"  • {f}")
    
    print("\n"+"="*60)
    print("FUSION PROCESS COMPLETE!")
    print("="*60)
    print(f"\nFinal dataset saved to: {OUTPUT_FILE}")
    print(f"Total rows: {len(final_df)}")
    print(f"Total columns: {len(final_df.columns)}")