# convert matrix (96 well plate format) into dataframe
import pandas as pd
import os
from calculation import *
import os, sys
import warnings
warnings.filterwarnings("ignore")

# for executable purposes, defining a dynamic base path is needed for executing at different locations
# for relative path, this is a folder created in the same directory as the executable for storing HP_assay experiments
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    path = os.path.join(base_path, relative_path)

    return path
    
def processing(root_directory):
    print(root_directory)
    # Loop through file in directory 
    for folder_name in os.listdir(root_directory):
        folder_path = os.path.join(root_directory, folder_name)
        # check if subfolder
        if os.path.isdir(folder_path):
            print(f"Folder: {folder_path}")

            # # Print the file names in the current subfolder
            # for file_name in os.listdir(folder_path):
            #     print(f" - {file_name}")

            # have a text file to indicate which folder has been processed
            remembered_folders_file = 'processed_files.txt'
            # with open(remembered_folders_file, 'r+') as f:
            #     if folder_path not in f.read():
            #         f.write(folder_path + ',')     
            #         pass
            #     else:
            #         continue

            try:
            # # Print the file names in the current subfolder
            # for file_name in os.listdir(folder_path):
            #     print(f" - {file_name}")
                sample_layout = pd.read_excel(folder_path+'/' + 'sample_layout.xlsx',engine='openpyxl',sheet_name=None, skiprows=0) #skip the first row which is the indexes of the well
                measurements = pd.read_excel(folder_path+'/' + 'abs_reading.xlsx',engine='openpyxl',sheet_name=None, skiprows=0) #skip the first row which is the indexes of the well
            except:
                raise Exception('cannot read files in folder ')
            
            # ------------------- format sample layout ----------------------------      update the format sample layout code from wayne's PC
            digestion_layout_df_list = []
            layout_df_list = []

            column_names = ['ID', 'experiment_ID', 'sample_ID','sample_type', 'sample_state', 'sample_lot','hide_ID','culture_date', 
                            'biopsy_replicate', 'biopsy_diameter_mm', 'digestion_volume_ul', 'dilution_factor',	'assay_volume_ul', 'loaded_weight1_mg', 'loaded_weight2_mg', 
                            'tube_weight1_mg', 'tube_weight2_mg','operator', 'std_conc_ug_per_well', 'media_type', 'biomaterial_ID', 'reaction_date']
            
            # to process each plate individually with own standard curve,
            # loop through excel sheet find 'i-th' layout -> loop through sample sheet find the 'i-th' layout -> combine -> calculate
            # combine the calculated results
            
            # process digestion samples layout
            for i, sheet_name in enumerate(sample_layout):

                if sheet_name == 'Digestion' + str(i):
                    #print(sheet_name)

                    # we need digestion layout to skip first and last row, first and last column
                    digestion_layout = sample_layout[sheet_name].iloc[1:7,2:12] # start at 1 because first row is already skipped.

                    # extract the values in cells (concatenated well info string)
                    digestion_layout = digestion_layout.values

                    # add row and column name for 6x10 matrix
                    row = ['B', 'C', 'D','E','F','G']
                    column = ['2','3','4','5','6','7','8','9','10','11']

                    # add index and column name
                    digestion_loc_df = pd.DataFrame(digestion_layout, index=row, columns=column)

                    # Convert matrices into DataFrames with row and column names
                    digestion_loc_df = digestion_loc_df.reset_index().melt(id_vars='index', var_name='column_name', value_name='well_info')
                    
                    digestion_info = digestion_loc_df.iloc[0:,2:].reset_index(level=0,drop=True)

                    # expand strings with ',' into individual cells
                    digestion_info = digestion_info.melt()['value'].str.split(',',expand=True)
                    
                    # rename column
                    for i, col_name in enumerate(digestion_info.columns):
                        digestion_info.rename(columns = {col_name: column_names[i]}, inplace = True)
                    
                    # add location to the digestion dataframe
                    digestion_location = digestion_loc_df['index'] + digestion_loc_df['column_name']
                    digestion_info.insert(loc = 2, column = 'location', value = digestion_location)
                    digestion_info = digestion_info[digestion_info['ID'].str.len() > 0 ]

                    digestion_info['sheet_name'] = sheet_name
                    
                    # put dataframes into a list
                    digestion_layout_df_list.append(digestion_info)

                    # combine dataframes with single row of header
                    digestion_layout_df = pd.concat(digestion_layout_df_list, ignore_index=True)[digestion_info.columns]

                    digestion_layout_df = digestion_layout_df[digestion_layout_df['experiment_ID'] != '']
            
            # process sample_layouts
            well_layout_count = 1
            for sheet in sample_layout:
                if sheet == 'Well_layout' + str(well_layout_count):
                    well_layout_count += 1
                    # drop the rows/columns and expand into appropriate dataframe
                    df = sample_layout[sheet].iloc[0:,1:].reset_index(level=0,drop=True)
                    df = df.melt()['value'].str.split(',',expand=True)
                   
                    # replace header
                    for i, col_name in enumerate(df.columns):
                        df.rename(columns = {col_name: column_names[i]}, inplace = True)

                    # put dataframes into a list
                    layout_df_list.append(df)

                    # # combine dataframes with single row of header
                    # layout_df = pd.concat(layout_df_list, ignore_index=True)[df.columns]


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
            biopsy_results = calculate_sample_averages(combined_raw_data_df)

            combined_raw_data_df.to_csv(folder_path + '/' + 'combined_raw_data.csv')
            biopsy_results.to_csv(folder_path + '/' + 'biopsy_result.csv')

def reprocessing(root_directory):
    print(root_directory)
    # Loop through file in directory 
    for folder_name in os.listdir(root_directory):
        folder_path = os.path.join(root_directory, folder_name)
        # check if subfolder
        if os.path.isdir(folder_path):
            print(f"Folder: {folder_path}")

            try:
            # # Print the file names in the current subfolder
            # for file_name in os.listdir(folder_path):
            #     print(f" - {file_name}")
                raw_data_combined = pd.read_csv(folder_path + '/' + 'combined_raw_data.csv')

                # remove the index column name
                columns = raw_data_combined.iloc[:,1:].columns
            except:
                raise Exception('files not found, process the folder first')
        
            # reprocess each plate in the file
            combined_raw_data_list_rp = []
            plate_list = raw_data_combined['sheet_name'].unique()
            for i, plate in enumerate(plate_list):
                filtered_data = raw_data_combined[raw_data_combined['sheet_name'] == plate]
                omitted, standard, samples, control = recalculate(filtered_data,folder_path, plate)

               # stack outputs
                stacked_data = pd.concat([omitted, standard, samples, control], axis=0)
                stacked_data.reset_index()
                
                # append outputs to list
                combined_raw_data_list_rp.append(stacked_data)
            
            # combine the appended dataframe with multiple header columns into 1 single header column
            combined_raw_data_df = pd.concat(combined_raw_data_list_rp, ignore_index=True, join='outer')[columns]

            # combined_raw_data retains omitted samples even though it wasnt part of calc, so need to omit the samples again and calculate biopsy results
            combined_raw_data_df = combined_raw_data_df[combined_raw_data_df['data check'].isnull()]
            biopsy_results = calculate_sample_averages(combined_raw_data_df)

            combined_raw_data_df.to_csv(folder_path + '/' + 'combined_raw_data_reprocessed.csv')
            biopsy_results.to_csv(folder_path + '/' + 'biopsy_result_reprocessed.csv')

            # if biospsy_result_rp is not None:
            #     biospsy_result_rp.to_csv(folder_path + '/' + 'biopsy_result_reprocessed.csv')


if __name__ == "__main__":
    path = resource_path('HP_assay')
    #processing(path)
    reprocessing(path)



