# convert matrix (96 well plate format) into dataframe
import pandas as pd
import os
from calculation import *
import os, sys
import warnings
warnings.filterwarnings("ignore")
import traceback

# for executable purposes, defining a dynamic base path is needed for executing at different locations
# relative path is a folder path created in the same directory as the executable for storing HP_assay experiments
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)

    return path
    
def processing(folder_name):

    root_directory = resource_path('DNA_assay')

    folder_path = os.path.join(root_directory, folder_name)
        # check if subfolder
    if os.path.isdir(folder_path):
        try:
        # # Print the file names in the current subfolder
        # for file_name in os.listdir(folder_path):
        #     print(f" - {file_name}")
            sample_layout = pd.read_excel(folder_path+'/' + 'sample_layout.xlsx',engine='openpyxl',sheet_name=None, skiprows=0) #skip the first row which is the indexes of the well
            measurements = pd.read_excel(folder_path+'/' + 'abs_reading.xlsx',engine='openpyxl',sheet_name=None, skiprows=0) #skip the first row which is the indexes of the well
         
        except:
            print(traceback.format_exc())
        
        print('input from user is',folder_name)

        column_names = ['dna_sid', 'experiment_id','sample_id','sample_type','description','sample_replicate','sample_diameter_mm','digestion_volume_ul','digested_sample_volume_ul',
                        'buffer_volume_ul','dilution_factor','assay_volume_ul','std_conc_ng_per_well','biopsy_region','culture_duration_days','master_well_plate_location']


        # process all the data using 1 standard curve.
        # loop through sample sheet find 'i-th' layout -> loop through abs sheet find the 'i-th' layout -> combine data -> calculate
        # combine the calculated results
        
        # ------------------- format sample layout ----------------------------
        
        layout_df_list = []
        
        # process sample_layouts
        well_layout_count = 1
        for sheet in sample_layout:
            if sheet == 'Well layout' + str(well_layout_count):
                well_layout_count += 1
                # drop the rows/columns and expand into appropriate dataframe
                df = sample_layout[sheet].iloc[0:,1:].reset_index(level=0,drop=True)
                try:
                    df = df.melt()['value'].str.split(',',expand=True)
                except:
                    continue

                # rename header
                for i, col_name in enumerate(df.columns):
                    df.rename(columns = {col_name: column_names[i]}, inplace = True)

                # put dataframes into a list
                layout_df_list.append(df)

        #  # ------------------- format absorbance measurement layout ----------------------------
        # empty list for combining multiple sheets together    
        abs_df_list = []

        # loop through each sheet in excel file
        for i, sheet_name in enumerate(measurements):
            if sheet_name == 'Plate' + str(i):

                # ignore 1st row and 1st column (recall first row is skipped already)
                df = measurements[sheet_name].iloc[0:,1:]
                df = df.values

                row = ['A', 'B', 'C', 'D','E','F','G','H']
                column = ['1','2','3','4','5','6','7','8','9','10','11','12']
                
                # Convert matrices into DataFrames with row and column names
                df_converted = pd.DataFrame(df, index=row, columns=column)

                # stack or melt dataframe
                #df_converted = pd.DataFrame(df, index=row, columns=column).stack().reset_index(name='abs').rename(columns={'level_0':'row','level_1':'column'})
                df_converted = df_converted.reset_index().melt(id_vars='index', var_name='column_name', value_name='abs')

                # Add sheet_name column to each DataFrame
                df_converted['sheet_name'] = sheet_name

                # add location column
                df_converted['location'] = df_converted['index'] + df_converted['column_name']
                df_converted = df_converted.iloc[:,2:]

                # put dataframes into a list
                abs_df_list.append(df_converted)
        
        # ----------------------- combine sample layout and absorbance by zipping -------------------
        zipped_df_list = []

        for layout, abs in zip(layout_df_list, abs_df_list):
            zipped_df_list.append(pd.concat([layout, abs], axis=1))

        # process each dataframe in in the zipped dataframe list
        combined_raw_data_list = []

        for i, layout_abs_df in enumerate(zipped_df_list):
            # add data check column for omission
            layout_abs_df['data_check'] = ''

            # run calculation. i = dataframe number in the zipped list of dataframes, also is the plate number
            standard, samples = DNA_assay_calc(layout_abs_df, folder_path,i+1)

             # stack outputs
            raw_data_combined = pd.concat([standard, samples], axis=0)
            
            # append outputs
            combined_raw_data_list.append(raw_data_combined)
            #biopsy_results.append(result_list)


        # combine the appended list of dataframes containing multiple headers with single row of header
        combined_raw_data_df = pd.concat(combined_raw_data_list, ignore_index=True)[raw_data_combined.columns]
        

        # calculate average results
        averaged_results = calculate_sample_averages(combined_raw_data_df)

        # ----------------------- output individual + average results together -----------------------------------
        
        # drop columns before merging
        averaged_results = averaged_results.drop(['sample_id', 'sample_replicate'], axis=1)
        
        all_results = pd.merge(averaged_results, combined_raw_data_df, on='dna_sid', how='outer')
        #all_results = pd.concat([merged_averaged_results,standard],axis=0, join='outer').reset_index(drop=True)
    
        all_results_columns = ['dna_sid', 'experiment_id',
                                'sample_id', 'sample_type', 'description', 'sample_replicate',
                                'sample_diameter_mm', 'digestion_volume_ul',
                                'digested_sample_volume_ul', 'buffer_volume_ul', 'dilution_factor',
                                'assay_volume_ul', 'std_conc_ng_per_well', 'biopsy_region',
                                'culture_duration_days', 'master_well_plate_location', 'abs',
                                'sheet_name', 'location', 'ng_per_well', 'ug_per_ml', 'ug_per_biopsy',
                                'ug_per_cm2', 'r_squared','data_check','avg_ug_per_cm2', 'avg_ug_per_cm2_std']
        
        all_results = all_results[all_results_columns]
        all_results.to_csv(folder_path + '/' + 'combined_raw_data.csv')
   
        
        # ----------------------- output only unique id average results -----------------------------------
        display_columns = ['dna_sid','experiment_id','sample_id','sample_type','description','sample_diameter_mm','digestion_volume_ul','digested_sample_volume_ul',
                        'buffer_volume_ul','dilution_factor','assay_volume_ul','std_conc_ng_per_well','biopsy_region','culture_duration_days','master_well_plate_location']
        
        sample_layout = sample_layout['Samples'].iloc[:,0:16][display_columns]

        unique_sample_avg_results = pd.merge(averaged_results, sample_layout, on='dna_sid', how='inner')
        
        avg_results_column = ['dna_sid', 'experiment_id',
                            'sample_id', 'sample_type', 'description', 'sample_diameter_mm',
                            'digestion_volume_ul', 'digested_sample_volume_ul', 'buffer_volume_ul',
                            'dilution_factor', 'assay_volume_ul','biopsy_region', 'culture_duration_days', 'master_well_plate_location','avg_ug_per_cm2', 'avg_ug_per_cm2_std']
        
        unique_sample_avg_results = unique_sample_avg_results[avg_results_column]
        unique_sample_avg_results.to_csv(folder_path + '/' + 'averaged_data.csv')
        
    else:
        raise Exception(f'folder name {folder_name} does not exist')
                    
def reprocessing(folder_name):

    root_directory = resource_path('DNA_assay')

    folder_path = os.path.join(root_directory, folder_name)
        # check if subfolder
    if os.path.isdir(folder_path):
        print(f"Folder: {folder_path}")

        try:
        # # Print the file names in the current subfolder
        # for file_name in os.listdir(folder_path):
        #     print(f" - {file_name}")
            raw_data_combined = pd.read_csv(folder_path + '/' + 'combined_raw_data.csv').iloc[:,0:26] # remove unnamed index and averaged results first
            columns = raw_data_combined.iloc[:,1:26].columns
            
        except:
           print(traceback.format_exc())        

        combined_raw_data_list_rp = []
        plate_list = raw_data_combined['sheet_name'].unique()
        
        # reprocess each plate in the file
        for i, plate in enumerate(plate_list):
            filtered_data = raw_data_combined[raw_data_combined['sheet_name'] == plate]

            omitted, standard, samples = recalculate(filtered_data,folder_path, plate)

            # stack outputs
            stacked_data = pd.concat([omitted, standard, samples], axis=0)
            stacked_data.reset_index()
            
            # append outputs to list
            combined_raw_data_list_rp.append(stacked_data)
    
        if combined_raw_data_list_rp is not None:
            # combine the appended dataframe with multiple header columns into 1 single header column
            combined_raw_data_df = pd.concat(combined_raw_data_list_rp, ignore_index=True, join='outer')[columns]

            # combined_raw_data retains omitted samples even though it wasnt part of calc, so need to omit the samples before calculate averages
            combined_raw_data_df_filtered = combined_raw_data_df[combined_raw_data_df['data_check'].isnull()]

            averaged_results = calculate_sample_averages(combined_raw_data_df_filtered)


            # save averaged results first
            # averaged_results.to_csv(folder_path + '/' + 'averaged_data.csv')

            
            # ----------------------merge individual + average results together -----------------------------------
            
            # drop duplicated column on raw data first
            averaged_results = averaged_results.drop(['sample_id', 'sample_replicate'],axis=1)

            all_results = pd.merge(averaged_results,combined_raw_data_df, on = 'dna_sid', how='outer')

            all_results_columns = ['dna_sid', 'experiment_id',
                                    'sample_id', 'sample_type', 'description', 'sample_replicate',
                                    'sample_diameter_mm', 'digestion_volume_ul',
                                    'digested_sample_volume_ul', 'buffer_volume_ul', 'dilution_factor',
                                    'assay_volume_ul', 'std_conc_ng_per_well', 'biopsy_region',
                                    'culture_duration_days', 'master_well_plate_location', 'abs',
                                    'sheet_name', 'location', 'ng_per_well', 'ug_per_ml', 'ug_per_biopsy',
                                    'ug_per_cm2', 'r_squared','data_check','avg_ug_per_cm2', 'avg_ug_per_cm2_std']

            all_results = all_results[all_results_columns]
            all_results.to_csv(folder_path + '/' + 'combined_raw_data.csv')
            
            # --------------------------- extract only averaged results from combined_raw_data __________________________
            avg_results_column = ['dna_sid', 'experiment_id',
                                'sample_id', 'sample_type', 'description', 'sample_diameter_mm',
                                'digestion_volume_ul', 'digested_sample_volume_ul', 'buffer_volume_ul',
                                'dilution_factor', 'assay_volume_ul','biopsy_region', 'culture_duration_days', 'master_well_plate_location','avg_ug_per_cm2', 'avg_ug_per_cm2_std']
            
            unique_sample_avg_results = all_results.drop_duplicates(subset=['dna_sid'])
            unique_sample_avg_results = unique_sample_avg_results[unique_sample_avg_results['sample_type'] == 'sample']
            unique_sample_avg_results = unique_sample_avg_results[avg_results_column]
            unique_sample_avg_results.to_csv(folder_path + '/' + 'averaged_data.csv')
       


if __name__ == "__main__":
    # user_input = input('enter experiment name for calculating')
    # if user_input is not None:
    #     processing(user_input)
    reprocessing('DNA74')