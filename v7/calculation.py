# problem with v7 - after standard curve changes, sample calculation became incorrect. 
# the standard curve was normalized to ug/ml with 20 uL. So it also assumes that samples has 20 uL, but this value can be different. if its different, it gives wrong value in calculation

import pandas as pd
import numpy as  np
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot as plt
import sys, os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)

    return path

def hydroxyproline_assay_calc(df,save_img_path, plate_number):

    # normalize abs reading if there is any
    if len(df[df['sample_type'] == 'blank_control']) > 0:
        blank_abs = df[df['sample_type'] == 'blank_control']['abs'].mean()
    else:
        blank_abs = 0
    
    df['normalized_abs'] = df['abs'] - blank_abs

    # --------------tables of standards only (raw data)---------------
    standard = df[df['sample_type'] == 'standard']
    standard_volume_ml = pd.to_numeric(standard['assay_volume_ul'])/1000
    standard_ug_per_ml = pd.to_numeric(standard['std_conc_ug_per_well'])/standard_volume_ml
  
    model = LinearRegression()
    model.fit(standard[['normalized_abs']], standard_ug_per_ml)
    r_squared = model.score(standard[['normalized_abs']], standard_ug_per_ml)
    slope = np.ndarray.item(np.array(model.coef_))
    intercept = np.ndarray.item(np.array(model.intercept_))
    #print(slope, intercept, r_squared)

    # populate r_squared value in table of standards
    standard['r_squared'] = r_squared
    standard = standard.reset_index(level=0, drop=True)

    # plot scatter vs predicted
    #print(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
    plt.scatter(standard[['normalized_abs']], standard_ug_per_ml , color='g')
    plt.plot(standard[['normalized_abs']], model.predict(standard[['normalized_abs']]),color='k')
    plt.text(0.4, 0.2, f'r_squared= {round(r_squared,5)}', style='italic')
    plt.xlabel('normalized absorbance')
    plt.ylabel('std_conc_ug_per_ml')
    plt.savefig(os.path.join(save_img_path, f'Plate{plate_number} standard plot'))
    plt.close()
    #plt.show()

    # --------------table of gelatin control only----------------
    if len(df[df['sample_type'] == 'control']) > 0:
        control = df[df['sample_type'] == 'control']

        control['ug/ml'] = control['normalized_abs']*slope+intercept # y value of the standard curve is in ug/ml
        control['ug/well'] = control['ug/ml'] * pd.to_numeric(control['assay_volume_ul'])/1000

        # change to ug/ml by multiplying by the dilution factor and dividing the assay volume
        # how to implement the change without creating additional columns? maybe just need to add 1 extra column for std conc ug per ml for groupby.
        #control_std_ug_per_ml = pd.to_numeric(control['std_conc_ug_per_well'])/control['assay_volume_ul']*control['dilution_factor']


        control_std = pd.to_numeric(control['std_conc_ug_per_well'])
        control['std_conc_ug_per_well'] = control_std

        # average the standard conc for each gelatin control
        std_conc_per_control = control.groupby(['experiment_ID','sample_ID'])['std_conc_ug_per_well'].mean().reset_index()
        
        avg_conc_per_control = control.groupby(['experiment_ID','sample_ID'], squeeze=True).apply(lambda x: ((x['ug/ml'].sum()- x['ug/ml'].max()-x['ug/ml'].min())/(len(x)-2))).reset_index(name='ug/ml')
        avg_conc_per_control['std_conc_ug_per_ml'] = std_conc_per_control['std_conc_ug_per_well']/(pd.to_numeric(control['assay_volume_ul'])/1000)

        gelatin_model = LinearRegression()
        gelatin_model.fit(avg_conc_per_control[['std_conc_ug_per_ml']], avg_conc_per_control[['ug/ml']])
        gelatin_r_squared = gelatin_model.score(avg_conc_per_control[['std_conc_ug_per_ml']], avg_conc_per_control[['ug/ml']])
        # slope = np.ndarray.item(np.array(gelatin_model.coef_))
        # intercept = np.ndarray.item(np.array(gelatin_model.intercept_))

        control['r_squared'] = gelatin_r_squared
        control = control.reset_index(level=0, drop=True)

        # plotting fitted line
        plt.scatter(avg_conc_per_control[['std_conc_ug_per_ml']], avg_conc_per_control[['ug/ml']], color='g')
        plt.plot(avg_conc_per_control[['std_conc_ug_per_ml']],gelatin_model.predict(avg_conc_per_control[['std_conc_ug_per_ml']]),color='k')
        plt.text(0.4, 0.4, f'r_squared= {round(gelatin_r_squared,5)}', style='italic')
        plt.xlabel('thereotical hydroxyproline ug/ml')
        plt.ylabel('hydroxyproline in gelatin ug/ml')
        plt.savefig(os.path.join(save_img_path, f'Plate{plate_number} control_plot.png'))
        plt.close()
    else:
        control = None

    # -------------table of samples only (raw data)-------------
    if len(df[df['sample_type'] == 'sample']) > 0:
        samples = df[(df['sample_type'] == 'sample')]

        # net weight calculation
        loaded_weight1 = pd.to_numeric(samples['loaded_weight1_mg'])
        loaded_weight2 = pd.to_numeric(samples['loaded_weight2_mg'])
        avg_loaded_weight = (loaded_weight1 + loaded_weight2)/2

        tube_weight1 = pd.to_numeric(samples['tube_weight1_mg'])
        tube_weight2 = pd.to_numeric(samples['tube_weight2_mg'])
        avg_empty_weight = (tube_weight1 + tube_weight2)/2
        # avg_loaded_weight = (samples['loaded_weight1_mg']+samples['loaded_weight2_mg'])/2
        # avg_empty_weight = (samples['tube_weight1_mg']+samples['tube_weight2_mg'])/2
        samples['net weight mg'] = avg_loaded_weight - avg_empty_weight

        # calculate ug/well for each sample using standard plot
        samples['ug/well'] = samples['normalized_abs']*slope+intercept

        # calculate mg/ml for all samples
        samples['mg/ml'] = samples['ug/well']/pd.to_numeric(samples['assay_volume_ul'])*pd.to_numeric(samples['dilution_factor']) # ug/ul = mg/ml
        
        # if sample is aggregrate, calculate mg/biopsy
        samples['mg/biopsy'] = samples[(samples['sample_state'] == 'aggregrate') | (samples['sample_state'] == 'hide')]['mg/ml']*(pd.to_numeric(samples['digestion_volume_ul'])/1000)
        
        # if sample is hide, calculate weight/area
        samples['mg/cm2'] = samples[(samples['sample_state'] == 'hide')]['mg/biopsy']/(np.pi*((pd.to_numeric(samples['biopsy_diameter_mm'])/10)/2)**2)

    else:
        print('no samples')
        samples = None  

    return standard, samples, control


# once all samples are calculated, then calculate averages
def calculate_sample_averages(combined_raw_data):
    if len(combined_raw_data[combined_raw_data['sample_type'] == 'sample']) > 0:
        samples = combined_raw_data[combined_raw_data['sample_type'] == 'sample']

        # -- average result of each sample (trimming) --
        average_per_sample = samples.groupby(['experiment_ID','sample_ID', 'biopsy_id','biopsy_replicate','biomaterial_id'], squeeze=True).apply(lambda x: ((x['mg/biopsy'].sum()- x['mg/biopsy'].max()-x['mg/biopsy'].min())/(len(x)-2)) if len(x) > 2 else x['mg/biopsy'].mean()).reset_index(name='mg/biopsy')
        average_mg_per_ml = samples.groupby(['experiment_ID','sample_ID', 'biopsy_id','biopsy_replicate','biomaterial_id'], squeeze=True).apply(lambda x: ((x['mg/ml'].sum()- x['mg/ml'].max()-x['mg/ml'].min())/(len(x)-2)) if len(x) > 2 else x['mg/ml'].mean()).reset_index(name='mg/ml')
        average_mg_cm2_per_sample = samples.groupby(['experiment_ID','sample_ID','biopsy_id','biopsy_replicate','biomaterial_id'], squeeze=True).apply(lambda x: ((x['mg/cm2'].sum()- x['mg/cm2'].max()-x['mg/cm2'].min())/(len(x)-2)) if len(x) > 2 else x['mg/cm2'].mean()).reset_index(name='mg/cm2')
        
        average_per_sample['mg/cm2'] = average_mg_cm2_per_sample['mg/cm2']
        average_per_sample['mg/ml'] = average_mg_per_ml['mg/ml']

        # --average results of each hide --
        biopsy_mean = average_per_sample.groupby(['experiment_ID','biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['mg/biopsy'].mean()).reset_index(name='mg/biopsy mean')
        biopsy_std = average_per_sample.groupby(['experiment_ID','biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['mg/biopsy'].std()).reset_index(name='mg/biopsy std')
    
        conc_mean = average_per_sample.groupby(['experiment_ID','biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['mg/ml'].mean()).reset_index(name='mg/ml mean')
        conc_mean_std = average_per_sample.groupby(['experiment_ID','biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['mg/ml'].std()).reset_index(name='mg/ml std')
        
        weight_per_area_mean = average_per_sample.groupby(['experiment_ID','biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['mg/cm2'].mean()).reset_index(name='mg/cm2 mean')
        weight_per_area_std = average_per_sample.groupby(['experiment_ID','biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['mg/cm2'].std()).reset_index(name='mg/cm2 std')
    
        # average weight of each biopsy_id categorized by biomaterial_id
        biopsy_weight = samples.groupby(['biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: x['net weight mg'].mean()).reset_index(name='net weight mg')

        # get average diameter for each hide (just for grouping for calculation purpose)
        biopsy_area = samples.groupby(['biopsy_id','biomaterial_id'], squeeze = True).apply(lambda x: (np.pi*(pd.to_numeric(x['biopsy_diameter_mm'])/10/2)**2).mean()).reset_index(name='biopsy_area')

        # add to biopsy_mean dataframe
        biopsy_mean['mg/biopsy std'] = biopsy_std['mg/biopsy std']
        biopsy_mean['mg/ml mean'] = conc_mean['mg/ml mean']
        biopsy_mean['mg/ml std'] = conc_mean_std['mg/ml std']

        # hydroxyproline on biopsy
        biopsy_mean['mg/cm2 mean'] = weight_per_area_mean['mg/cm2 mean']
        biopsy_mean['mg/cm2 std'] = weight_per_area_std['mg/cm2 std'] 
        
        biopsy_mean['net weight mg'] = biopsy_weight['net weight mg']
        biopsy_mean['tissue areal density mg/cm2'] = biopsy_mean['net weight mg']/biopsy_area['biopsy_area']

        # convert mg/cm2 to collagen mg/cm2, divide by 0.105
        # to get % collagen = collagen/(tissue density - biomaterial density)
    else:
        print('no samples to calculate results')
        biopsy_mean = None

    return biopsy_mean

def recalculate(combined_raw_data, save_img_path, plate):

    if len(combined_raw_data[combined_raw_data['data check'] == 'o']) == 0:
        print(f'{plate} does not need for recalculation')
    
    # keep omitted samples for tracking purposes
    omitted_data = combined_raw_data[(combined_raw_data['sheet_name'] == plate) & (combined_raw_data['data check'] == 'o')]

    # keep retained data for recalculation
    retained_data = combined_raw_data[(combined_raw_data['sheet_name'] == plate) & (combined_raw_data['data check'].isnull())]

    # output only raw data columns 1 - 27 before recalculating
    retained_data = retained_data.iloc[:,1:28]

    plate_number = plate[-1] + ' reprocessed'
    standard, samples, control = hydroxyproline_assay_calc(retained_data, save_img_path, plate_number)

    return omitted_data, standard, samples, control 
