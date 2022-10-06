from azure.cli.core import get_default_cli
import azure.functions as func
from datetime import datetime
import pandas as pd
import subprocess
import logging
import json
import io

def check_status(row, read_df):

    if row.principalName in list(read_df.principalName.values) and row.roleDefinitionName in ['Contributor']:
        read_cnt = read_df[(read_df['principalName'] == row.principalName) & (read_df['roleDefinitionName'] == row.roleDefinitionName)]['count'].values[0]
        updated_cnt = read_cnt + 1
        print('Updated Cnt', )
        return row['name'], row.principalName, row.roleDefinitionName, updated_cnt
    else:
        return row['name'], row.principalName, row.roleDefinitionName, 1


def revoke_access(row, temp_df):
    
    temp_df.drop(row['index'], inplace=True)
    revoke_command = f'az role assignment delete --assignee "{row.principalName}" --role "{row.roleDefinitionName}"'.split()
    response = subprocess.check_output(revoke_command)
    logging.info(revoke_command, response)

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
    command = f'az role assignment list --subscription {subscription_id}'.split()
    # az_cli = get_default_cli()
    # response = az_cli.invoke(command)
    # logging.info(response)
    users_list = subprocess.check_output(command)
    
    users_df = pd.DataFrame(json.loads(users_list))
    users_df = users_df[['name', 'principalName', 'roleDefinitionName']]
    if read_df.empty or datetime.today().strftime("%I:%M %p") == '12:00 AM':  
        users_df['count'] = 1
        stream = io.StringIO()
        users_df.to_csv(stream, sep=",", index=False)
        outputBlob.set(stream.getvalue())
    else:
        users_list = users_df.apply(lambda row: check_status(row, read_df), axis=1).tolist()
        logging.info(users_list)
        users_df1 = pd.DataFrame(users_list, columns=['name', 'principalName', 'roleDefinitionName', 'count'])

        merged_df = read_df.merge(users_df1, on='principalName', how='left')

        merged_df['count_x'] = merged_df[['count_x', 'count_y']].apply(lambda row: row.count_y if row.count_y > row.count_x else row.count_x, axis=1)

        temp_df = merged_df[merged_df.columns[:4]]
        temp_df.columns = ['name', 'principalName', 'roleDefinitionName', 'count']
        temp_df.reset_index(inplace=True)

        # delete user
        hrs_threshold = 5
        remove_access_df = temp_df[temp_df['count'] > hrs_threshold][['index', 'principalName', 'roleDefinitionName']]

        if not remove_access_df.empty: remove_access_df.apply(lambda row: revoke_access(row, temp_df), axis=1)

        temp_df.drop('index', axis=1, inplace=True)
        temp_df['count'] = temp_df['count'].astype(int)
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
