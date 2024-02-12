# convert matrix (96 well plate format) into dataframe
import pandas as pd
import os
from calculation import *
import os, sys
import warnings
warnings.filterwarnings("ignore")
import traceback
#from read_all_tabs_gsheet import read_gsheet_by_name

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
    #read_gsheet_by_name(folder_name)
    root_directory = resource_path('HP_assay')

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
        
        # ------------------- format sample layout ----------------------------
        print('input from user is',folder_name)
        #print(sample_layout['Well layout1']) 
        
        # ------------------- format sample layout ----------------------------      update the format sample layout code from wayne's PC
        layout_df_list = []
        
        column_names = ['HP_sid', 'experiment_ID', 'sample_ID','sample_type', 'sample_state', 'sample_lot','biopsy_id','culture_date', 
                        'biopsy_replicate', 'biopsy_diameter_mm', 'digestion_volume_ul', 'dilution_factor',	'assay_volume_ul', 'loaded_weight1_mg', 'loaded_weight2_mg', 
                        'tube_weight1_mg', 'tube_weight2_mg','operator', 'std_conc_ug_per_well', 'media_type', 'biomaterial_id', 'reaction_date']
        
        # to process each plate individually with own standard curve,
        # loop through excel sheet find 'i-th' layout -> loop through sample sheet find the 'i-th' layout -> combine -> calculate
        # combine the calculated results
        
        # process digestion samples layout
        for i, sheet_name in enumerate(sample_layout):
    
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

                    # replace header with renamed column names
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

        # ----------------------- calculating each sheet and combine them after -------------------
        # zip the two list of dataframes: layout_df_list, abs_df_list
        zipped_df_list = []

        for layout, abs in zip(layout_df_list, abs_df_list):
            zipped_df_list.append(pd.concat([layout, abs], axis=1))

        # process each dataframe in combined_layout_abs list
        combined_raw_data_list = []

        for i, layout_abs_df in enumerate(zipped_df_list):
            # add data check column for omission
            layout_abs_df['data check'] = ''

            # run calculation. i = dataframe number in the zipped list of dataframes, also is the plate number
            standard, samples, control = hydroxyproline_assay_calc(layout_abs_df,folder_path,i+1)

            # stack outputs
            raw_data_combined = pd.concat([standard, samples, control], axis=0)
            
            # append outputs
            combined_raw_data_list.append(raw_data_combined)
            #biopsy_results.append(result_list)
        
        # combine the appended list of dataframes containing multiple headers with single row of header
        combined_raw_data_df = pd.concat(combined_raw_data_list, ignore_index=True)[raw_data_combined.columns]

        # fix culture date column to a date format, subtract 2 days due to excel start date reference. Then convert into mm-dd-yyyy
        start_date = pd.to_datetime('01-01-1900')
        culture_date = pd.to_numeric(combined_raw_data_df['culture_date'])
        combined_raw_data_df['culture_date'] = ((start_date + pd.to_timedelta(culture_date, unit='D')) - pd.to_timedelta(2, unit='D')).dt.strftime('%m-%d-%Y')
        
  
        # calculate average results for hides
        average_results, biopsy_results = calculate_sample_averages(combined_raw_data_df)
        #combined_raw_data_df.iloc[:,0:33].to_csv(folder_path + '/' + 'combined_raw_data.csv')
        biopsy_results.to_csv(folder_path + '/' + 'biopsy_result.csv')
        
        # average_results.to_csv('test.csv')
        # drop duplicate columns before merging
        average_results = average_results.drop(['experiment_ID', 'sample_ID','biopsy_id','biopsy_replicate','biomaterial_id'],axis=1)

        # merge with raw data
        combined_avg_results = pd.merge(average_results,combined_raw_data_df, on = 'HP_sid', how='outer')

        # reorganize columns
        combined_avg_results_column = ['HP_sid', 'experiment_ID', 'sample_ID',
                                        'sample_type', 'sample_state', 'sample_lot', 'biopsy_id',
                                        'culture_date', 'biopsy_replicate', 'biopsy_diameter_mm',
                                        'digestion_volume_ul', 'dilution_factor', 'assay_volume_ul',
                                        'loaded_weight1_mg', 'loaded_weight2_mg', 'tube_weight1_mg',
                                        'tube_weight2_mg', 'operator', 'std_conc_ug_per_well', 'media_type',
                                        'biomaterial_id', 'reaction_date', 'abs', 'sheet_name', 'location',
                                        'data check', 'normalized_abs', 'r_squared', 'net weight mg', 'ug/well',
                                        'mg/ml', 'mg/biopsy', 'mg/cm2','avg mg/biopsy', 'mg/biopsy std', 'avg mg/cm2',
                                        'mg/cm2 std', 'avg mg/ml', 'mg/ml std']
    

        # rearrange columns and save combined raw data with averages
        combined_avg_results = combined_avg_results[combined_avg_results_column]
        combined_avg_results.to_csv(folder_path + '/' + 'combined_raw_data.csv')

        # # merge average results with sample layout to only get the averages of individual samples
        # sample_layout = sample_layout['Samples'].iloc[:,0:22].dropna(subset=['ID'])
        # for i, col_name in enumerate(sample_layout.columns):
        #         sample_layout.rename(columns = {col_name: column_names[i]}, inplace = True)
        
        # unique_avg_results = pd.merge(average_results,sample_layout, on = 'HP_sid', how='inner')
    
        # # reorganize columns
        # unique_avg_results_column = ['HP_sid','experiment_ID', 'sample_ID',
        #                                 'sample_type', 'sample_state', 'sample_lot', 'biopsy_id',
        #                                 'culture_date', 'biopsy_replicate', 'biopsy_diameter_mm',
        #                                 'digestion_volume_ul', 'dilution_factor', 'assay_volume_ul',
        #                                 'loaded_weight1_mg', 'loaded_weight2_mg', 'tube_weight1_mg',
        #                                 'tube_weight2_mg', 'operator', 'std_conc_ug_per_well', 'media_type',
        #                                 'biomaterial_id', 'reaction_date','avg mg/biopsy', 'mg/biopsy std', 'avg mg/cm2',
        #                                 'mg/cm2 std', 'avg mg/ml', 'mg/ml std']
        
        # unique_avg_results = unique_avg_results[unique_avg_results_column]
        # unique_avg_results.to_csv(folder_path + '/' + 'sample_avg_results.csv')

    else:
        raise Exception(f'folder name {folder_name} does not exist')
                    
def reprocessing(folder_name):

    root_directory = resource_path('HP_assay')
    
    folder_path = os.path.join(root_directory, folder_name)
        # check if subfolder
    if os.path.isdir(folder_path):
        print(f"Folder: {folder_path}")

        try:
        # # Print the file names in the current subfolder
        # for file_name in os.listdir(folder_path):
        #     print(f" - {file_name}")
            raw_data_combined = pd.read_csv(folder_path + '/' + 'combined_raw_data.csv')
            sample_layout = pd.read_excel(folder_path+'/' + 'sample_layout.xlsx',engine='openpyxl',sheet_name=None, skiprows=0)

            # remove the index column name and the averaged value columns
            columns = raw_data_combined.iloc[:,1:34].columns

        except:
           print(traceback.format_exc())        

        combined_raw_data_list_rp = []
        plate_list = raw_data_combined['sheet_name'].unique()

        # reprocess each plate in the file
        for i, plate in enumerate(plate_list):
            filtered_data = raw_data_combined[raw_data_combined['sheet_name'] == plate]

            omitted, standard, samples, control = recalculate(filtered_data,folder_path, plate)

            # stack outputs
            stacked_data = pd.concat([omitted, standard, samples, control], axis=0)
            stacked_data.reset_index()
            
            # append outputs to list
            combined_raw_data_list_rp.append(stacked_data)
        
        
        if combined_raw_data_list_rp is not None:
            # combine the appended dataframe with multiple header columns into 1 single header column
            combined_raw_data_df = pd.concat(combined_raw_data_list_rp, ignore_index=True, join='outer')[columns]
         
            
            # combined_raw_data retains omitted samples even though it wasnt part of calc, so need to omit the samples again and calculate biopsy results
            combined_raw_data_df_filtered = combined_raw_data_df[combined_raw_data_df['data check'].isnull()]
            
            average_results, biopsy_results = calculate_sample_averages(combined_raw_data_df_filtered)
            
            biopsy_results.to_csv(folder_path + '/' + 'biopsy_result.csv')
            
            # drop duplicate columns before merging
            average_results = average_results.drop(['experiment_ID', 'sample_ID','biopsy_id','biopsy_replicate','biomaterial_id'],axis=1)

            combined_avg_results = pd.merge(average_results,combined_raw_data_df, on = 'HP_sid', how='outer')

            # reorganize columns
            combined_avg_results_column = ['HP_sid', 'experiment_ID', 'sample_ID',
                                            'sample_type', 'sample_state', 'sample_lot', 'biopsy_id',
                                            'culture_date', 'biopsy_replicate', 'biopsy_diameter_mm',
                                            'digestion_volume_ul', 'dilution_factor', 'assay_volume_ul',
                                            'loaded_weight1_mg', 'loaded_weight2_mg', 'tube_weight1_mg',
                                            'tube_weight2_mg', 'operator', 'std_conc_ug_per_well', 'media_type',
                                            'biomaterial_id', 'reaction_date', 'abs', 'sheet_name', 'location',
                                            'data check', 'normalized_abs', 'r_squared', 'net weight mg', 'ug/well',
                                            'mg/ml', 'mg/biopsy', 'mg/cm2','avg mg/biopsy', 'mg/biopsy std', 'avg mg/cm2',
                                            'mg/cm2 std', 'avg mg/ml', 'mg/ml std']
            
            # rearrange columns
            combined_avg_results = combined_avg_results[combined_avg_results_column]
           
            combined_avg_results.to_csv(folder_path + '/' + 'combined_raw_data.csv')


            # # merge average results with sample layout to only get the averages of individual samples
            # sample_layout = sample_layout['Samples'].iloc[:,0:22].dropna(subset=['ID'])
            # for i, col_name in enumerate(sample_layout.columns):
            #         if i < 23:
            #             sample_layout.rename(columns = {col_name: combined_avg_results_column[i]}, inplace = True)
            
            # unique_avg_results = pd.merge(average_results,sample_layout, on = 'HP_sid', how='inner')

            # # reorganize columns
            # unique_avg_results_column = ['HP_sid','experiment_ID', 'sample_ID',
            #                                 'sample_type', 'sample_state', 'sample_lot', 'biopsy_id',
            #                                 'culture_date', 'biopsy_replicate', 'biopsy_diameter_mm',
            #                                 'digestion_volume_ul', 'dilution_factor', 'assay_volume_ul',
            #                                 'loaded_weight1_mg', 'loaded_weight2_mg', 'tube_weight1_mg',
            #                                 'tube_weight2_mg', 'operator', 'std_conc_ug_per_well', 'media_type',
            #                                 'biomaterial_id', 'reaction_date','avg mg/biopsy', 'mg/biopsy std', 'avg mg/cm2',
            #                                 'mg/cm2 std', 'avg mg/ml', 'mg/ml std']
            
            # unique_avg_results = unique_avg_results[unique_avg_results_column]
            # unique_avg_results.to_csv(folder_path + '/' + 'sample_avg_results.csv')
    

if __name__ == "__main__":
    # user_input = input('enter experiment name for calculating')
    # if user_input is not None:
    #     processing(user_input)

    processing('HP83-20240207')


# when use new version, uncomment the column names in the hp_data_pg.py


