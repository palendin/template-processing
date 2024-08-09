import pandas as pd
import gspread as gs
import os
from googleapiclient.discovery import build
import pygsheets
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# pip install google api libaries
from httplib2 import Http
from oauth2client import file, client, tools
from getfilelistpy import getfilelist
from google.oauth2 import service_account
from googleapiclient.discovery import build


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

def read_gsheet_by_name(experiment_folder_id):
    root_path = '/Users/wayne/Library/CloudStorage/GoogleDrive-wayne@vitrolabsinc.com/Shared drives/R&PD Team/Vitrolab Experimental Data (Trained User Only)/Analytical/DNA'
    #experiment_path = os.path.join(root_path,folder_name)
    vscode_path = os.path.dirname(os.path.dirname(os.getcwd())) # when running as a function within SQL_query folder, it takes you two levels up
    service_account_file = os.path.join(vscode_path,'API/Google_API/service_account.json')
    credential = os.path.join(vscode_path,'API/Google_API/VL_client_secrets.json')

    gc = gs.service_account(filename=service_account_file)
    
    
    # Define the scope and credentials file
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly','https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(credential, SCOPES)
        creds = tools.run_flow(flow, store)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # points to HP_assay folder in vitrolab google drive
    resource = {
        "oauth2": creds.authorize(Http()),
        "id": experiment_folder_id,
        "fields": "files(name,id)",
    }

    # # direct to the folder tree only
    # r = getfilelist.GetFolderTree(resource)
    # folders = r.get('folders')

    # # for each subfolder, get sample layout id
    # for f in folders[1:]:
    #     resource = {
    #         "oauth2": creds.authorize(Http()),
    #         "id": f,
    #         "fields": "files(name,id)",
    #     }
        
    res = getfilelist.GetFileList(resource)

    # get only fileList in the "res" dictionary
    filelist = res.get('fileList',[])
  
    # combine information only about the "files" in "fileList" into a list
    AllFilesInFolder = sum([e.get('files',[]) for e in filelist],[])
    
    # list all files in the all folder, only output "name" and "id" information
    listing = [[e[f] for f in ['name', 'id']] for e in AllFilesInFolder]
    # print('folder is {} and resource is {}'.format(f, listing))

    columns = ['file_name', 'file_id']
    df = pd.DataFrame(listing, columns = columns)
    
    # open only sample layout file
    sample_layout_file_id = df[df['file_name'] == 'sample_layout']['file_id'].iloc[0]

    sh = gc.open_by_key(sample_layout_file_id)

    worksheet = sh.worksheet('Samples')

    list_of_lists = worksheet.get_all_values()

    df = pd.DataFrame(list_of_lists[1:], columns = list_of_lists[0]) # [1:] is used cuz not pulling header row

    csv_data = df.reset_index(drop=True)

    csv_data = df.to_csv(index=False)

# Encode CSV data as bytes using UTF-8 encoding
    csv_data_bytes = csv_data.encode('utf-8')
    
    credentials = service_account.Credentials.from_service_account_file(service_account_file)
    drive_service = build('drive', 'v3', credentials=credentials)


    # Upload CSV data to Google Drive
    file_metadata = {
        'name': 'your_csv_file.csv',
        'parents': [experiment_folder_id]
    }
    media_body = MediaIoBaseUpload(io.BytesIO(csv_data_bytes), mimetype='text/csv', resumable=True)
    files = drive_service.files().create(body=file_metadata, media_body=media_body).execute()





if __name__ == "__main__":
    # file_id = '1-n2zwPWklDmYvsyYcuaSqdirkg1vnwAaMFXQvvDCyLc'
    # sheet_name = "Tracker"
    # print(read_gsheet_all_tabs(file_id))

    read_gsheet_by_name('1gOveAuLzT__Ri8dyodQaWJB2wsN48WSy')

