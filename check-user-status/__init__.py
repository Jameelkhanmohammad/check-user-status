from azure.cli.core import get_default_cli
import azure.functions as func
from datetime import datetime
from urllib import request
import pandas as pd
import subprocess
import requests
import logging
import json
import io

def check_status(row, read_df):
    
    if row.principalId in list(read_df.principalId.values) and row.role in ['Contributor']:
        
        read_cnt = read_df[(read_df['principalId'] == row.principalId) & (read_df['role'] == row.role)]['count'].values[0]
        updated_cnt = read_cnt + 1
        
        return row['name'], row['id'], row.principalId, row.role, updated_cnt
    else:
        return row['name'], row['id'], row.principalId, row.role, 1

def revoke_access(row, temp_df, headers):
    
    temp_df.drop(row['index'], inplace=True)
    response = requests.delete(f"https://management.azure.com{row['id']}?api-version=2015-07-01", headers=headers)
    
    # revoke_command = f'az role assignment delete --assignee "{row.principalId}" --role "{row.role}"'.split()
    # response = subprocess.check_output(revoke_command)
    logging.info(response)

def get_role(role_id, headers):

    role = requests.get(f'https://management.azure.com{role_id}?api-version=2015-07-01', headers=headers).json()['properties']
    
    return role['roleName']
    
def main(req: func.HttpRequest, inputBlob: func.InputStream, outputBlob: func.Out[bytes]) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    # Reading from the input binding
    input_data = io.StringIO(inputBlob.read().decode("utf-8"))
    logging.info(input_data)
    # Processing the csv file
    read_df = pd.read_csv(input_data, sep=",")
    logging.info(read_df)

    subscription_id = '3882abc4-c619-4abc-a930-9a71fc7c2343'
    # command = f'az role assignment list --subscription {subscription_id}'.split()
    # az_cli = get_default_cli()
    # response = az_cli.invoke(command)
    # logging.info(response)
    # users_list = subprocess.check_output(command) 
    tenantID = '62bd2232-c68d-4580-9469-942cbf5ad6d1'
    token_url = f'https://login.microsoftonline.com/{tenantID}/oauth2/token'

    body = {'grant_type': 'client_credentials',
            'client_id': 'cf95e80c-b048-41de-b60c-cc7258a47a05',
            'client_secret': 'Q4X8Q~jaURKyjz7-Hzrf_c7uN4Nrw-X4pCNQTanK',
            'scope': ['https://management.azure.com/user_impersonation'],
            'resource': 'https://management.azure.com'}


    response = requests.get(token_url, data=body).json()

    headers = {'Authorization': f"{response['token_type']} {response['access_token']}",
            'Host': 'management.azure.com',
            }

    subId = '3882abc4-c619-4abc-a930-9a71fc7c2343'
    users_list = requests.get(f'https://management.azure.com/subscriptions/{subId}/providers/Microsoft.Authorization/roleAssignments?api-version=2015-07-01',
                                headers=headers).json()
    temp_df = pd.DataFrame(users_list['value'])
    temp_df['roleDefinitionId'] = temp_df['properties'].apply(lambda dt: dt['roleDefinitionId'])
    temp_df['principalId'] = temp_df['properties'].apply(lambda dt: dt['principalId'])
    temp_df['role'] = temp_df['roleDefinitionId'].apply(lambda role_id: get_role(role_id, headers))
    
    # users_df = pd.DataFrame(json.loads(users_list))
    users_df = temp_df[['name', 'id', 'principalId', 'role']]

    if read_df.empty or datetime.today().strftime("%I:%M %p") == '12:00 AM':  
        users_df['count'] = 1
        stream = io.StringIO()
        users_df = users_df[['name', 'principalId', 'role', 'count']]
        users_df.to_csv(stream, sep=",", index=False)
        outputBlob.set(stream.getvalue())
    else:
        users_list = users_df.apply(lambda row: check_status(row, read_df), axis=1).tolist()
        # logging.info(users_list)
        users_df1 = pd.DataFrame(users_list, columns=['name', 'id', 'principalId', 'role', 'count'])

        # users_df1 = temp_df[['name', 'principalId', 'role']]

        merged_df = read_df.merge(users_df1, on='principalId', how='right')

        merged_df['count_x'] = merged_df[['count_x', 'count_y']].apply(lambda row: row.count_y if row.count_y > row.count_x else row.count_x, axis=1)
        
        temp_df = merged_df[['name_x', 'principalId', 'role_x', 'count_x', 'id']]
        temp_df.columns = ['name', 'principalId', 'role', 'count', 'id']
        temp_df.reset_index(inplace=True)

        # delete user
        hrs_threshold = 5
        remove_access_df = temp_df[temp_df['count'] > hrs_threshold][['index', 'id']]

        if not remove_access_df.empty: remove_access_df.apply(lambda row: revoke_access(row, temp_df, headers), axis=1)

        temp_df.drop('index', axis=1, inplace=True)
        temp_df['count'] = temp_df['count'].astype(int)
        temp_df.drop('id', axis=1, inplace=True)
        final_df = temp_df.reset_index(drop=True)
        
        # write final data to storage
        stream = io.StringIO()
        final_df.to_csv(stream, sep=",", index=False)
        outputBlob.set(stream.getvalue())
        logging.info(final_df)
    
    if name:
        return func.HttpResponse(f"Function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
