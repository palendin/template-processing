# analysis for each run
# make sure data table has correct label samples: standard, blank, sample, empty

import pandas as pd
import numpy as  np
from sklearn.linear_model import LinearRegression
import sklearn
from matplotlib import pyplot as plt
from sklearn.metrics import r2_score
import os

def hydroxyproline_assay_calc(df):

    # normalize reading
    blank_abs = df[df['sample_type'] == 'blank']['abs'].mean()
    df['normalized_abs'] = df['abs'] - blank_abs

    # tables of standards only (raw data)
    standard = df[df['sample_type'] == 'standard']

    model = LinearRegression()
    model.fit(standard[['normalized_abs']], standard[['ug/well']])
    r_squared = model.score(standard[['normalized_abs']], standard[['ug/well']])
    slope = np.asscalar(np.array(model.coef_))
    intercept = np.asscalar(np.array(model.intercept_))
    #print(slope, intercept, r_squared)

    # populate r_squared value in table of standards
    standard['r_squared'] = r_squared
    standard = standard.reset_index(level=0, drop=True)

    # plot scatter vs predicted
    #print(standard[['normalized_abs']], standard[['ug/well']])
    plt.scatter(standard[['normalized_abs']], standard[['ug/well']], color='g')
    plt.plot(standard[['normalized_abs']], model.predict(standard[['normalized_abs']]),color='k')
    plt.text(0.4, 0.2, f'r_squared= {round(r_squared,2)}', style='italic')
    plt.xlabel('normalized absorbance')
    plt.ylabel('ug/well')
    plt.savefig(os.path.join(os.path.dirname(__file__), 'standard_plot.png'))
    plt.close()
    #plt.show()


    # table of samples only (raw data)
    samples = df[df['sample_type'] == 'sample']

    # calculate 
    samples['ug/well']= samples['normalized_abs']*slope+intercept
    samples['mg/biopsy'] = samples['ug/well']/1000*(samples['homogenate volume ul']/samples['homogenate sample volume ul'])*(samples['digest volume ul']/samples['digest sample volume ul'])

    # average results per hide_ID replicates (each hide_ID has 4 rep)
    average_per_sample = samples.groupby(['experiment_ID','hide_ID', 'hide_replicate','scaffold_type'], squeeze=True).apply(lambda x: ((x['mg/biopsy'].sum()- x['mg/biopsy'].max()-x['mg/biopsy'].min())/2)).reset_index(name='mg/biopsy')
    #print(average_per_sample)

    # average mg/biopsy of the same sample_IDs, and standard dev
    biopsy_mean = average_per_sample.groupby(['experiment_ID','hide_ID','scaffold_type'], squeeze = True).apply(lambda x: x['mg/biopsy'].mean()).reset_index(name='mg/biopsy mean')
    biopsy_std = average_per_sample.groupby(['experiment_ID','hide_ID','scaffold_type'], squeeze = True).apply(lambda x: x['mg/biopsy'].std()).reset_index(name='mg/biopsy std')
    
    # convert to numeric before averaging. because sometimes it has type error
    x = pd.to_numeric(samples['net weight mg'])
    samples['x'] = x
    biopsy_weight = samples.groupby(['hide_ID','scaffold_type'], squeeze = True).apply(lambda x: x['x'].mean()).reset_index(name='net weight mg')
    
    # add to biopsy_mean dataframe
    biopsy_mean['mg/biopsy std'] = biopsy_std['mg/biopsy std']
    biopsy_mean['net weight mg'] = biopsy_weight['net weight mg']
    
    # define scaffold weight base on their type
    biopsy_mean.loc[biopsy_mean['scaffold_type'] == 'V2P1', 'scaffold weight mg'] = 5.75
    biopsy_mean.loc[biopsy_mean['scaffold_type'] == 'PLA', 'scaffold weight mg'] = 4.6
    
    # define average % hydroxyproline in collagens
    biopsy_mean['% hydroxyproline_in_collagen'] = 10.5
    biopsy_mean['% percent_collagen'] = (biopsy_mean['mg/biopsy mean']/(biopsy_mean['% hydroxyproline_in_collagen']/100))/(biopsy_mean['net weight mg']-biopsy_mean['scaffold weight mg'])*100
    #print(biopsy_mean)

    plt.bar(biopsy_mean['hide_ID'],biopsy_mean['mg/biopsy mean'])
    plt.errorbar(biopsy_mean['hide_ID'], biopsy_mean['mg/biopsy mean'], yerr=biopsy_mean['mg/biopsy std'], fmt='o', color ='r')
    plt.xlabel('hide_ID')
    plt.ylabel('avg mg/biopsy')
    plt.savefig(os.path.join(os.path.dirname(__file__), 'biopsy_results.png'))
    plt.close()
    # plt.show()
    #print(average_abs_per_sample)
    
    return standard, samples, biopsy_mean

if __name__ == "__main__":
    df = pd.read_csv('test_HP_calc.csv')
    standard, samples, biopsy_results = hydroxyproline_assay_calc(df)
#print(average_per_sample)

    # save CSV for standard, sample, and average result tables
    # standard.to_csv('standard'+f'{count}.csv')
    # samples.to_csv('samples'+f'{count}.csv')
    # average_abs_per_sample.to_csv('average_abs_reading'+f'{count}.csv')

    # upload to opvia and insert into DB (insert whole file or use API)

