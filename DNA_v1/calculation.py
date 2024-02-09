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

def DNA_assay_calc(df,save_img_path, plate_number):

    # --------------tables of standards only (raw data)---------------
    if len(df[df['sample_type'] == 'standard']) > 0:
        standard = df[df['sample_type'] == 'standard']

        model = LinearRegression()
        model.fit(standard[['abs']], standard[['std_conc_ng_per_well']])
        r_squared = model.score(standard[['abs']], standard[['std_conc_ng_per_well']])
        slope = np.ndarray.item(np.array(model.coef_))
        intercept = np.ndarray.item(np.array(model.intercept_))
        #print(slope, intercept, r_squared)

        # populate r_squared value in table of standards
        standard['r_squared'] = r_squared
        standard = standard.reset_index(level=0, drop=True)

        # plot scatter vs predicted
        standard_ug_well = pd.to_numeric(standard['std_conc_ng_per_well'])
        plt.scatter(standard[['abs']], standard_ug_well, color='g')
        plt.plot(standard[['abs']], model.predict(standard[['abs']]),color='k')
        plt.text(0.4, 0.2, f'r_squared= {round(r_squared,5)}', style='italic')
        plt.xlabel('absorbance')
        plt.ylabel('std_conc_ng_per_well')
        plt.savefig(os.path.join(save_img_path, f'Plate{plate_number} standard plot'))
        plt.close()

    # -------------table of samples only (raw data)-------------
    if len(df[df['sample_type'] == 'sample']) > 0:
        samples = df[(df['sample_type'] == 'sample')]

        # calculate ng/well for each sample using standard plot
        samples['ng/well'] = samples['abs']*slope+intercept

        # calculate ug/ml for all samples
        samples['ug/ml'] = (samples['ng/well']/pd.to_numeric(samples['assay_volume_ul'])*pd.to_numeric(samples['dilution_factor']))/1000 # convert from ng/ml to ug/ml
        
        # calclate ug/biopsy for all samples
        samples['ug/biopsy'] = samples['ug/ml']*(pd.to_numeric(samples['digestion_volume_ul'])/1000)
        
        # calculate ug/cm2 for all samples
        samples['ug/cm2'] = samples['ug/biopsy']/(np.pi*((pd.to_numeric(samples['sample_diameter_mm'])/10)/2)**2)

    else:
        print('no samples')
        samples = None  

    return standard, samples


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
    standard, samples, control = DNA_assay_calc(retained_data, save_img_path, plate_number)

    return omitted_data, standard, samples, control 
