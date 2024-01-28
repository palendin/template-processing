import pandas as pd
import gspread as gs
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def read_gsheet(file_id, sheet_name):

    vscode_path = os.path.dirname(os.path.dirname(os.getcwd())) # when running as a function within SQL_query folder, it takes you two levels up
    service_account = os.path.join(vscode_path,'API/Google_API/service_account.json')
    gc = gs.service_account(filename=service_account)

    # open the file that you want data to append to
    sh = gc.open_by_key(file_id)

    worksheet = sh.worksheet(sheet_name) # assign sheet

    # append to worksheet
    list_of_lists = worksheet.get_all_values()

    df = pd.DataFrame(list_of_lists[1:], columns = list_of_lists[0]) # [1:] is used cuz not pulling header row

    df = df.reset_index(drop=True)

    return df

# using file id
def read_gsheet_all_tabs(file_id):

    vscode_path = os.path.dirname(os.path.dirname(os.getcwd())) # when running as a function within SQL_query folder, it takes you two levels up
    service_account = os.path.join(vscode_path,'API/Google_API/service_account.json') 

    df_list = []
    gc = gs.service_account(filename=service_account)

    # open the file that you want data to append to
    sh = gc.open_by_key(file_id)
    
    for worksheet in sh.worksheets():

        # append to worksheet
        list_of_lists = worksheet.get_all_values()

        df = pd.DataFrame(list_of_lists[1:], columns = list_of_lists[0])

        df = df.reset_index(drop=True)
        
        df_list.append(df)
    
    return df_list


def read_gsheet_by_name(worksheet_name):
    vscode_path = os.path.dirname(os.path.dirname(os.getcwd())) # when running as a function within SQL_query folder, it takes you two levels up
    service_account = os.path.join(vscode_path,'API/Google_API/service_account.json') 
    
    print(service_account)
    # df_list = []
    # gc = gs.service_account(filename=service_account)

    #  # open the file that you want data to append to
    # sh = gc.open(worksheet_name)

    # # retrieve file ID knowing google dive folder path

    # # Define your folder path
    # folder_path = '/Folder/Subfolder'

    # # Load your Google Drive credentials
    # credentials = Credentials.from_authorized_user_file('credentials.json')  # Replace with your credentials file path

    # # Build the Drive API service
    # drive_service = build('drive', 'v3', credentials=credentials)

    # # Search for the folder by name
    # response = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder' and name='{}'".format(folder_path)).execute()

    # # Get the ID of the first matching folder
    # folder_id = response.get('files', [])[0]['id']

    # # Search for files within the folder
    # response = drive_service.files().list(q="'{}' in parents".format(folder_id)).execute()

    # # Get the IDs of all files within the folder
    # file_ids = [file['id'] for file in response.get('files', [])]

    # print("File IDs within the folder:", file_ids)



if __name__ == "__main__":
    file_id = '1-n2zwPWklDmYvsyYcuaSqdirkg1vnwAaMFXQvvDCyLc'
    sheet_name = "Tracker"
    print(read_gsheet_all_tabs(file_id))

