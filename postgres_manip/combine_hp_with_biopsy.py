import pandas as pd


# combine hp with biopsy to get sample id column and remove duplicates to get overall combined file of biopsy

path = 'biopsy_result.csv'
df1 = pd.read_csv(path)
df2 = df1.drop_duplicates(subset=['experiment_id','biopsy_id','mg_per_biopsy_mean','mg_per_ml_mean'])

#df2.to_csv('unique_biopsy_result.csv')

# merge with raw result to get sample id
hp_raw_path = 'hydroxyproline_raw.csv'
hp_raw = pd.read_csv(hp_raw_path).iloc[:,0:33]
combined = pd.merge(hp_raw,df2, on =['biopsy_id','experiment_id'], how='left')
combined = combined.drop_duplicates(subset=['experiment_id','sample_id_x','biopsy_id','mg_per_ml_mean'])
combined = combined[combined['sample_type'] == 'sample']

print(len(df2))
print(len(combined))

# output only certain columns for biopsy_result
combined = combined[['hp_sid','experiment_id','biomaterial_id_x','sample_id_x','biopsy_id','mg_per_biopsy_mean','mg_per_biopsy_std','mg_per_ml_mean','mg_per_ml_std','mg_per_cm2_mean','mg_per_cm2_std','net_weight_mg_x','tissue_areal_density_mg_per_cm2']]
combined_renamed = combined.rename(columns = {'sample_id_x':'sample_id','biomaterial_id_x':'biomaterial_id'})

combined_renamed.to_csv('combined.csv')

# recombine to add hp sid to raw data
combined_renamed1 = combined_renamed[['hp_sid','experiment_id','sample_id','biopsy_id']]
final_raw = pd.merge(combined_renamed1,hp_raw, on = ['experiment_id','sample_id','biopsy_id'],how = 'outer')

final_raw.to_csv('final_raw.csv') # biopsy result with hp_sid and sample_id
# print(len(hp_raw))
# print(len(final_raw))

# print(len(final_raw['experiment_id'].unique()))

# merge back to see if the output will be the same length as combined.csv
final_combined = pd.read_csv('combined_with_hpsid.csv')
test = pd.merge(final_raw,final_combined,on =['biopsy_id','experiment_id','sample_id'], how='inner')
test=test.drop_duplicates(subset=['experiment_id','sample_id','biopsy_id','mg_per_ml_mean'])
print(len(test))

final_raw_combined = pd.merge(final_combined,hp_raw, on = ['experiment_id','sample_id','biopsy_id'],how = 'outer')

final_raw_columns = ['hp_sid','experiment_id','sample_id','biopsy_id','sample_type','sample_state',
                     	'sample_lot','culture_date','biopsy_replicate','biopsy_diameter_mm','digestion_volume_ul','dilution_factor',
                        'assay_volume_ul','loaded_weight1_mg','loaded_weight2_mg','tube_weight1_mg','tube_weight2_mg','operator',
                        'std_conc_ug_per_well','media_type','biomaterial_id_y','reaction_date','abs','sheet_name','location',
                        'data_check','normalized_abs','r_squared','net_weight_mg_y','ug_per_well','mg_per_ml','mg_per_biopsy',
                        'mg_per_cm2']

final_hp_raw_data = final_raw_combined[final_raw_columns]
final_hp_raw_data.to_csv('final_hp_raw_combined.csv')

# m = df1.merge(df2, on='id', how='outer', suffixes=['', '_'], indicator=True)

# experiment = combined['experiment_id'].unique()
# any(s.startswith('HP15') for s in experiment)
# # m.to_csv('dup.csv')