# convert matrix (96 well plate format) into dataframe
import pandas as pd
import os
from calculation import hydroxyproline_assay_calc
import os, sys
import warnings
import mmap
from tkinter import messagebox
import time
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
            with open(remembered_folders_file, 'r+') as f:
                if folder_path not in f.read():
                    f.write(folder_path + ',')     
                    pass
                else:
                    continue

            try:
            # # Print the file names in the current subfolder
            # for file_name in os.listdir(folder_path):
            #     print(f" - {file_name}")
                sample_layout = pd.read_excel(folder_path+'/' + 'sample_layout.xlsx',engine='openpyxl',sheet_name=None, skiprows=0) #skip the first row which is the indexes of the well
                measurements = pd.read_excel(folder_path+'/' + 'abs_reading.xlsx',engine='openpyxl',sheet_name=None, skiprows=0) #skip the first row which is the indexes of the well
            except:
                continue
            
            # ------------------- format sample layout ----------------------------
            combined_layout = pd.DataFrame()
            layout_df_list = []
            for sheet_name in sample_layout:
                if sheet_name != 'Samples':
                    # Column names
                    column_names = ['ID', 'experiment_ID', 'sample_ID','sample_type','pilot_batch','tissue','hide_ID','hide_replicate',
                                    'avg loaded weight mg','avg empty weight mg','net weight mg','operator', 'ug/well', 'media_type', 'scaffold_type', 'date']
                    
                    # drop the rows/columns and expand into appropriate dataframe
                    df = sample_layout[sheet_name].iloc[0:,1:].reset_index(level=0,drop=True)
                    df = df.melt()['value'].str.split(',',expand=True)

                    # combine dataframes into single dataframe
                    combined_layout = combined_layout.append(df)

                    # put dataframes into a list
                    layout_df_list.append(df)

                    # combine dataframes with single row of header
                    layout_df = pd.concat(layout_df_list, ignore_index=True)[combined_layout.columns]
            
            # replace header
            for i, col_name in enumerate(layout_df.columns):
                layout_df.rename(columns = {col_name: column_names[i]}, inplace = True)

            # add constants to table
            layout_df['homogenate volume ul'] = 500
            layout_df['homogenate sample volume ul'] = 100
            layout_df['digest volume ul'] = 1000
            layout_df['digest sample volume ul'] = 20
            
            #  # ------------------- format absorbance measurement layout ----------------------------
            # empty dataframe for combining multiple sheets together    
            combined_abs = pd.DataFrame()
            abs_df_list = []

            # loop through each sheet in excel file
            for sheet_name in measurements:
                if sheet_name != 'General':
                    #df = measurements[sheet_name].iloc[:,1:]
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
                    combined_abs = combined_abs.append(df_converted)

                    # put dataframes into a list
                    abs_df_list.append(df_converted)

            # combine multiple dataframe and use single list of column names
            combined_abs_df = pd.concat(abs_df_list, ignore_index=True)[df_converted.columns]
            
            # combined = combined.reset_index(level=0, drop=True)
            combined_abs_df['location'] = combined_abs_df['index'] + combined_abs_df['column_name']
            combined_abs_df = combined_abs_df.iloc[:,2:]
            
            # join layout and abs measurements together
            final_layout = pd.concat([layout_df, combined_abs_df], axis=1)
            #final_layout.to_csv('data.csv')

            # run calculation
            standard, samples, biopsy_results = hydroxyproline_assay_calc(final_layout,folder_path)
            #print(biopsy_results)
        

            # save the standard and samples only dataframes to csv to respective folder
            #combined.to_csv(folder_path + '/' + 'test.csv')
            samples.to_csv(folder_path + '/' + 'sample.csv')
            standard.to_csv(folder_path + '/' + 'standard.csv')
            biopsy_results.to_csv(folder_path + '/' + 'biopsy_result.csv')

if __name__ == "__main__":
    path = resource_path('HP_assay')
    processing(path)


