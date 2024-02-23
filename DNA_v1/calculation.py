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

def DNA_assay_calc(df,save_img_path):

    # --------------tables of standards only (raw data)---------------
    if len(df[df['sample_type'] == 'standard']) > 0:
        standard = df[df['sample_type'] == 'standard']

        model = LinearRegression()
        model.fit(standard[['abs']], standard[['std_conc_ng_per_well']])
        r_squared = model.score(standard[['abs']], standard[['std_conc_ng_per_well']])
        slope = np.ndarray.item(np.array(model.coef_))
        intercept = np.ndarray.item(np.array(model.intercept_))
        print(slope, intercept, r_squared)

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
        plt.savefig(os.path.join(save_img_path,'standard plot'))
        plt.close()

    # -------------table of samples only (raw data)-------------
    if len(df[df['sample_type'] == 'sample']) > 0:
        samples = df[(df['sample_type'] == 'sample')]

        # calculate ng/well for each sample using standard plot
        samples['ng_per_well'] = samples['abs']*slope+intercept

        # calculate ug/ml for all samples
        samples['ug_per_ml'] = (samples['ng_per_well']/(pd.to_numeric(samples['assay_volume_ul'])/1000)*pd.to_numeric(samples['dilution_factor']))/1000 # convert from ng/ml to ug/ml
        
        # calclate ug/biopsy for all samples
        samples['ug_per_biopsy'] = samples['ug_per_ml']*(pd.to_numeric(samples['digestion_volume_ul'])/1000)
        
        # calculate ug/cm2 for all samples
        samples['ug_per_cm2'] = samples['ug_per_biopsy']/(np.pi*((pd.to_numeric(samples['sample_diameter_mm'])/10)/2)**2)

    else:
        print('no samples')
        samples = None  

    return standard, samples


# once all samples are calculated, then calculate averages
def calculate_sample_averages(combined_raw_data):
    if len(combined_raw_data[combined_raw_data['sample_type'] == 'sample']) > 0:
        samples = combined_raw_data[combined_raw_data['sample_type'] == 'sample']

        # -- average result of each sample (trimming) --
        average_per_sample = samples.groupby(['dna_sid','sample_id','sample_replicate'], squeeze=True).apply(lambda x: x['ug_per_cm2'].mean()).reset_index(name='avg_ug_per_cm2')
        average_per_sample_std = samples.groupby(['dna_sid','sample_id','sample_replicate'], squeeze = True).apply(lambda x: x['ug_per_cm2'].std()).reset_index(name='avg_ug_per_cm2_std')
        
        average_per_sample['avg_ug_per_cm2_std'] = average_per_sample_std['avg_ug_per_cm2_std']
    else:
        print('no samples to calculate results')
        biopsy_mean = None

    return average_per_sample

def recalculate(combined_raw_data, save_img_path, plate):

    if len(combined_raw_data[combined_raw_data['data check'] == 'o']) == 0:
        print(f'{plate} does not need for recalculation')
    
    # keep omitted samples for tracking purposes
    omitted_data = combined_raw_data[(combined_raw_data['sheet_name'] == plate) & (combined_raw_data['data check'] == 'o')]

    # keep retained data for recalculation
    retained_data = combined_raw_data[(combined_raw_data['sheet_name'] == plate) & (combined_raw_data['data check'].isnull())]

    # output only raw data columns 1 - 27 before recalculating
    retained_data = retained_data.iloc[:,0:28]

    plate_number = plate[-1] + ' reprocessed'
    standard, samples, control = DNA_assay_calc(retained_data, save_img_path, plate_number)

    return omitted_data, standard, samples, control 
