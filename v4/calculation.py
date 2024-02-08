# analysis for each run
# make sure data table has correct label samples: standard, blank, sample, control

import pandas as pd
import numpy as  np
from sklearn.linear_model import LinearRegression
from matplotlib import pyplot as plt
import sys, os
import datetime

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)

    return path

def hydroxyproline_assay_calc(df,save_img_path):

    # convert culture date due to bad csv format
    # Define a starting date as a reference
    start_date = pd.to_datetime('01-01-1900')
    culture_date = pd.to_numeric(df['culture_date'])

    # Convert the 'time' column to a date format, subtract 2 days due to excel start date reference. Then convert into mm-dd-yyyy
    df['culture_date'] = ((start_date + pd.to_timedelta(culture_date, unit='D')) - pd.to_timedelta(2, unit='D')).dt.strftime('%m-%d-%Y')

    #print(df['culture_date'])

    # normalize abs reading
    blank_abs = df[df['sample_type'] == 'blank_control']['abs'].mean()
    df['normalized_abs'] = df['abs'] - blank_abs

    # --------------tables of standards only (raw data)---------------
    standard = df[df['sample_type'] == 'standard']
    model = LinearRegression()
    model.fit(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
    r_squared = model.score(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
    slope = np.ndarray.item(np.array(model.coef_))
    intercept = np.ndarray.item(np.array(model.intercept_))
    #print(slope, intercept, r_squared)

    # populate r_squared value in table of standards
    standard['r_squared'] = r_squared
    standard = standard.reset_index(level=0, drop=True)

    # plot scatter vs predicted
    #print(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
    standard_ug_well = pd.to_numeric(standard['std_conc_ug_per_well'])
    plt.scatter(standard[['normalized_abs']], standard_ug_well, color='g')
    plt.plot(standard[['normalized_abs']], model.predict(standard[['normalized_abs']]),color='k')
    plt.text(0.4, 0.2, f'r_squared= {round(r_squared,5)}', style='italic')
    plt.xlabel('normalized absorbance')
    plt.ylabel('std_conc_ug_per_well')
    plt.savefig(os.path.join(save_img_path, 'standard_plot.png'))
    plt.close()
    #plt.show() 

    # --------------table of gelatin control only----------------
    control = df[df['sample_type'] == 'control']
    control['ug/well']= control['normalized_abs']*slope+intercept

    control_std = pd.to_numeric(control['std_conc_ug_per_well'])
    control['std_conc_ug_per_well'] = control_std

    # average the standard conc for each gelatin control
    std_conc_per_control = control.groupby(['experiment_ID','sample_ID'])['std_conc_ug_per_well'].mean().reset_index()
    
    avg_conc_per_control = control.groupby(['experiment_ID','sample_ID'], squeeze=True).apply(lambda x: ((x['ug/well'].sum()- x['ug/well'].max()-x['ug/well'].min())/6)).reset_index(name='ug/well')
    avg_conc_per_control['std_conc_ug_per_well'] = std_conc_per_control['std_conc_ug_per_well']
    #print(avg_conc_per_control['ug/well'])

    gelatin_model = LinearRegression()
    gelatin_model.fit(avg_conc_per_control['std_conc_ug_per_well'].to_np(), avg_conc_per_control[['ug/well']])
    gelatin_r_squared = gelatin_model.score(avg_conc_per_control[['std_conc_ug_per_well']], avg_conc_per_control[['ug/well']])
    # slope = np.ndarray.item(np.array(gelatin_model.coef_))
    # intercept = np.ndarray.item(np.array(gelatin_model.intercept_))

    control['r_squared'] = gelatin_r_squared
    control = control.reset_index(level=0, drop=True)

    #control_ug_well = pd.to_numeric(control['std_conc_ug_per_well'])
    plt.scatter(avg_conc_per_control[['std_conc_ug_per_well']], avg_conc_per_control[['ug/well']], color='g')
    plt.plot(avg_conc_per_control[['std_conc_ug_per_well']],gelatin_model.predict(avg_conc_per_control[['std_conc_ug_per_well']]),color='k')
    plt.text(0.4, 0.4, f'r_squared= {round(gelatin_r_squared,5)}', style='italic')
    plt.xlabel('thereotical hydroxyproline ug/well')
    plt.ylabel('hydroxyproline in gelatin ug/well')
    plt.savefig(os.path.join(save_img_path, 'control_plot.png'))
    plt.close()



    # -------------table of samples only (raw data)-------------
    samples = df[df['sample_type'] == 'sample']

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

    # calculate mg/biopsy and ug/area of each sample
    samples['ug/well']= samples['normalized_abs']*slope+intercept
    samples['mg/biopsy'] = samples['ug/well']/1000*(samples['homogenate volume ul']/samples['homogenate sample volume ul'])*(samples['digest volume ul']/samples['digest sample volume ul'])
    samples['mg/cm2'] = samples['mg/biopsy']/(np.pi*((pd.to_numeric(samples['biopsy_diameter_mm'])/10)/2)**2)

    # average mg/biopsy and ug/area per sample. each sample has 4 replicates. the avg exclude min and max value
    average_per_sample = samples.groupby(['experiment_ID','sample_ID', 'hide_ID','biopsy_replicate','biomaterial_ID'], squeeze=True).apply(lambda x: ((x['mg/biopsy'].sum()- x['mg/biopsy'].max()-x['mg/biopsy'].min())/2)).reset_index(name='mg/biopsy')
    average_mg_cm2_per_sample = samples.groupby(['experiment_ID','sample_ID','hide_ID','biopsy_replicate','biomaterial_ID'], squeeze=True).apply(lambda x: ((x['mg/cm2'].sum()- x['mg/cm2'].max()-x['mg/cm2'].min())/2)).reset_index(name='mg/cm2')
    average_per_sample['mg/cm2'] = average_mg_cm2_per_sample['mg/cm2']

    # -----------average results of each
    # average mg/biopsy and ug/cm2 of each hide_ID, and standard dev
    biopsy_mean = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/biopsy'].mean()).reset_index(name='mg/biopsy mean')
    biopsy_std = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/biopsy'].std()).reset_index(name='mg/biopsy std')
    
    weight_per_area_mean = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/cm2'].mean()).reset_index(name='mg/cm2 mean')
    weight_per_area_std = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/cm2'].std()).reset_index(name='mg/cm2 std')
 
    # average weight of each hide_ID categorized by biomaterial_ID
    biopsy_weight = samples.groupby(['hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['net weight mg'].mean()).reset_index(name='net weight mg')

    # get average diameter for each hide (just for grouping)
    biopsy_area = samples.groupby(['hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: (np.pi*(pd.to_numeric(x['biopsy_diameter_mm'])/10/2)**2).mean()).reset_index(name='biopsy_area')

    # add to biopsy_mean dataframe
    biopsy_mean['mg/biopsy std'] = biopsy_std['mg/biopsy std']
    biopsy_mean['net weight mg'] = biopsy_weight['net weight mg']
    biopsy_mean['tissue areal density mg/cm2'] = biopsy_mean['net weight mg']/biopsy_area['biopsy_area']
    biopsy_mean['mg/cm2 mean'] = weight_per_area_mean['mg/cm2 mean']
    biopsy_mean['mg/cm2 std'] = weight_per_area_std['mg/cm2 std']
    
    # define scaffold weight base on their type
    # base_path = resource_path('')
    # biomaterial_ID = pd.read_csv(base_path + '/' + 'biomaterial_ID.csv')
    # biopsy_mean = biopsy_mean.merge(biomaterial_ID, on = 'biomaterial_ID', how = 'left')
    
    # define average % hydroxyproline in collagens
    # biopsy_mean['% hydroxyproline_in_collagen'] = 10.5
    # biopsy_mean['% percent_collagen'] = (biopsy_mean['mg/biopsy mean']/(biopsy_mean['% hydroxyproline_in_collagen']/100))/(biopsy_mean['net weight mg']-biopsy_mean['scaffold_weight_mg'])*100
    # biopsy_mean['% percent_collagen_std'] = (biopsy_mean['mg/biopsy std']/(biopsy_mean['% hydroxyproline_in_collagen']/100))/(biopsy_mean['net weight mg']-biopsy_mean['scaffold_weight_mg'])*100
    #print(biopsy_mean)

    # plt.bar(biopsy_mean['hide_ID'],biopsy_mean['% percent_collagen'])
    # plt.errorbar(biopsy_mean['hide_ID'], biopsy_mean['% percent_collagen'], yerr=biopsy_mean['% percent_collagen_std'], fmt='o', color ='r')
    # plt.xlabel('hide_ID')
    # plt.ylabel('percent collagen')
    # plt.savefig(os.path.join(save_img_path, 'biopsy_results.png'))
    # plt.close()
    # plt.show()
    #print(average_abs_per_sample)

    return standard, samples, biopsy_mean, control

def recalculate(combined_raw_data, save_img_path):

    # output only raw data columns 1 - 27 before recalculating
    standard = combined_raw_data[combined_raw_data['sample_type'] == 'standard'].iloc[:,1:28]
    control = combined_raw_data[combined_raw_data['sample_type'] == 'control'].iloc[:,1:28]
    samples = combined_raw_data[combined_raw_data['sample_type'] == 'sample'].iloc[:,1:28]

    # --------------table of standard only----------------
    model = LinearRegression()
    if len(standard[standard['data check'] == 'o']) > 0:
        standard = standard[standard['data check'].isnull()]
        model.fit(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
        r_squared = model.score(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
        slope = np.ndarray.item(np.array(model.coef_))
        intercept = np.ndarray.item(np.array(model.intercept_))

        # populate r_squared value in table of standards
        standard['r_squared'] = r_squared
        standard = standard.reset_index(level=0, drop=True)

        # plot scatter vs predicted
        standard_ug_well = pd.to_numeric(standard['std_conc_ug_per_well'])
        plt.scatter(standard[['normalized_abs']], standard_ug_well, color='g')
        plt.plot(standard[['normalized_abs']], model.predict(standard[['normalized_abs']]),color='k')
        plt.text(0.4, 0.2, f'r_squared= {round(r_squared,5)}', style='italic')
        plt.xlabel('normalized absorbance')
        plt.ylabel('std_conc_ug_per_well')
        plt.savefig(os.path.join(save_img_path, 'standard_plot_reprocessed.png'))
        plt.close()

    else:
        model.fit(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
        r_squared = model.score(standard[['normalized_abs']], standard[['std_conc_ug_per_well']])
        slope = np.ndarray.item(np.array(model.coef_))
        intercept = np.ndarray.item(np.array(model.intercept_))


    # --------------table of gelatin control only----------------
    gelatin_model = LinearRegression()
    if len(control[control['data check'] == 'o']) > 0:
        control = control[control['data check'].isnull()]
        control['ug/well']= control['normalized_abs']*slope+intercept

        control_std = pd.to_numeric(control['std_conc_ug_per_well'])
        control['std_conc_ug_per_well'] = control_std

        # average the standard conc for each gelatin control
        std_conc_per_control = control.groupby(['experiment_ID','sample_ID'])['std_conc_ug_per_well'].mean().reset_index()
        
        avg_conc_per_control = control.groupby(['experiment_ID','sample_ID'], squeeze=True).apply(lambda x: ((x['ug/well'].sum() - x['ug/well'].max()-x['ug/well'].min())/(len(x)-2)) if len(x) > 2 else x['ug/well'].mean()).reset_index(name='ug/well')
        avg_conc_per_control['std_conc_ug_per_well'] = std_conc_per_control['std_conc_ug_per_well']
        #print(avg_conc_per_control['ug/well'])

        # fit the model
        gelatin_model.fit(avg_conc_per_control[['std_conc_ug_per_well']], avg_conc_per_control[['ug/well']])
        gelatin_r_squared = gelatin_model.score(avg_conc_per_control[['std_conc_ug_per_well']], avg_conc_per_control[['ug/well']])
        # slope = np.ndarray.item(np.array(gelatin_model.coef_))
        # intercept = np.ndarray.item(np.array(gelatin_model.intercept_))

        control['r_squared'] = gelatin_r_squared
        control = control.reset_index(level=0, drop=True)

        #control_ug_well = pd.to_numeric(control['std_conc_ug_per_well'])
        plt.scatter(avg_conc_per_control[['std_conc_ug_per_well']], avg_conc_per_control[['ug/well']], color='g')
        plt.plot(avg_conc_per_control[['std_conc_ug_per_well']],gelatin_model.predict(avg_conc_per_control[['std_conc_ug_per_well']]),color='k')
        plt.text(0.4, 0.4, f'r_squared= {round(gelatin_r_squared,5)}', style='italic')
        plt.xlabel('thereotical hydroxyproline ug/well')
        plt.ylabel('hydroxyproline in gelatin ug/well')
        plt.savefig(os.path.join(save_img_path, 'control_plot_reprocessed.png'))
        plt.close()

     # -------------table of samples only (raw data)-------------
    if len(samples[samples['data check'] == 'o']) > 0:
        samples = samples[samples['data check'].isnull()]

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

        # calculate mg/biopsy and ug/area of each sample
        samples['ug/well']= samples['normalized_abs']*slope+intercept
        samples['mg/biopsy'] = samples['ug/well']/1000*(samples['homogenate volume ul']/samples['homogenate sample volume ul'])*(samples['digest volume ul']/samples['digest sample volume ul'])
        samples['mg/cm2'] = samples['mg/biopsy']/(np.pi*((pd.to_numeric(samples['biopsy_diameter_mm'])/10)/2)**2)

        # average mg/biopsy and ug/area per sample. each digestion sample has 4 replicates. the avg exclude min and max value
        average_per_sample = samples.groupby(['experiment_ID','sample_ID', 'hide_ID','biopsy_replicate','biomaterial_ID'], squeeze=True).apply(lambda x: ((x['mg/biopsy'].sum()- x['mg/biopsy'].max()-x['mg/biopsy'].min())/(len(x)-2)) if len(x) > 2 else x['mg/biopsy'].mean()).reset_index(name='mg/biopsy')
        average_mg_cm2_per_sample = samples.groupby(['experiment_ID','sample_ID','hide_ID','biopsy_replicate','biomaterial_ID'], squeeze=True).apply(lambda x: ((x['mg/cm2'].sum()- x['mg/cm2'].max()-x['mg/cm2'].min())/(len(x)-2)) if len(x) > 2 else x['mg/cm2'].mean()).reset_index(name='mg/cm2')
        average_per_sample['mg/cm2'] = average_mg_cm2_per_sample['mg/cm2']

        # -----------average results of each
        # average mg/biopsy and ug/cm2 of each hide_ID, and standard dev
        biopsy_mean = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/biopsy'].mean()).reset_index(name='mg/biopsy mean')
        biopsy_std = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/biopsy'].std()).reset_index(name='mg/biopsy std')
        
        weight_per_area_mean = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/cm2'].mean()).reset_index(name='mg/cm2 mean')
        weight_per_area_std = average_per_sample.groupby(['experiment_ID','hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['mg/cm2'].std()).reset_index(name='mg/cm2 std')
    
       # average weight of each hide_ID categorized by biomaterial_ID
        biopsy_weight = samples.groupby(['hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: x['net weight mg'].mean()).reset_index(name='net weight mg')

        # get average diameter for each hide (just for grouping)
        biopsy_area = samples.groupby(['hide_ID','biomaterial_ID'], squeeze = True).apply(lambda x: (np.pi*(pd.to_numeric(x['biopsy_diameter_mm'])/10/2)**2).mean()).reset_index(name='biopsy_area')

        # add to biopsy_mean dataframe
        biopsy_mean['mg/biopsy std'] = biopsy_std['mg/biopsy std']
        biopsy_mean['net weight mg'] = biopsy_weight['net weight mg']
        biopsy_mean['tissue areal density mg/cm2'] = biopsy_mean['net weight mg']/biopsy_area['biopsy_area']
        biopsy_mean['mg/cm2 mean'] = weight_per_area_mean['mg/cm2 mean']
        biopsy_mean['mg/cm2 std'] = weight_per_area_std['mg/cm2 std']
    else:
        print('no change in results')
        biopsy_mean = None

    # can apply len(x) if there are more than 2 samples because it will take out min and max. if there is <=2, cannot take out min and max.
    #df.groupby(['ID_0', 'ID_1']).apply(lambda x: x['ID_2'].sum()/len(x))
    
    return biopsy_mean

# if __name__ == "__main__":
#     # df = pd.read_csv('test_HP_calc.csv')
#     # standard, samples, biopsy_results = hydroxyproline_assay_calc(df,None)

#     # save CSV for standard, sample, and average result tables
#     # standard.to_csv('standard'+f'{count}.csv')
#     # samples.to_csv('samples'+f'{count}.csv')
#     # average_abs_per_sample.to_csv('average_abs_reading'+f'{count}.csv')
