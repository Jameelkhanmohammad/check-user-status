import requests

# auth_headers = {'grant_type': 'client_credentials',
#                 'client_id': 'a21332c9-c20b-41c3-aa2e-ccc15555f5d4',
#                 'client_secret': '72a6903c-7ca9-4990-bd0b-92f91fade17f',
#                 'resource': 'https://management.azure.com/'}

# headers = {'Authorization': 'Bearer P7M7K9_TkcJFhIKiDcuYfNdEeU--RMqAi0YmV_1zIO2hAzFuDexLEw=='}
# response = requests.get('https://management.azure.com/subscriptions/3882abc4-c619-4abc-a930-9a71fc7c2343/providers/Microsoft.Authorization/roleAssignments?api-version=2015-07-01',
#                         headers=headers)

tenantID = '62bd2232-c68d-4580-9469-942cbf5ad6d1'
token_url = f'https://login.microsoftonline.com/common/oauth2/v2.0/token'

# authorize = f'https://login.microsoftonline.com/{tenantID}/oauth2/v2.0/authorize'

# body = {'resource': 'https://management.core.windows.net/',
#         'client_id': 'cf95e80c-b048-41de-b60c-cc7258a47a05',
#         'redirect_uri': 'api://cf95e80c-b048-41de-b60c-cc7258a47a05'}

# response = requests.get(authorize, data=body)
# print(response.content)
body = {'grant_type': 'client_credentials',
        'client_id': 'cf95e80c-b048-41de-b60c-cc7258a47a05',
        'client_secret': 'Q4X8Q~jaURKyjz7-Hzrf_c7uN4Nrw-X4pCNQTanK',
        'scope': 'https://graph.microsoft.com/.default',
        'resource': 'https://management.azure.com/'}
        # 'tenant_id': '62bd2232-c68d-4580-9469-942cbf5ad6d1',
        # 'subscription_id': '3882abc4-c619-4abc-a930-9a71fc7c2343'}

response = requests.get(token_url, data=body).json()
print(response)
print(f"{response['token_type']} {response['access_token']}")
# print(response)
headers = {'Authorization': f"{response['token_type']} {response['access_token']}",
           'Host': 'management.azure.com',
           }

subId = '3882abc4-c619-4abc-a930-9a71fc7c2343'
users_list = requests.get(f'https://management.azure.com/subscriptions/{subId}/providers/Microsoft.Authorization/roleAssignments?api-version=2015-07-01',
                            headers=headers)

# headers = {'clientId': 'a21332c9-c20b-41c3-aa2e-ccc15555f5d4',
#     'clientSecret': '72a6903c-7ca9-4990-bd0b-92f91fade17f',
#     'subscriptionId': '3882abc4-c619-4abc-a930-9a71fc7c2343',
#     'tenantId': '62bd2232-c68d-4580-9469-942cbf5ad6d1',
#     'resource': 'https://management.azure.com/'
# }



## command: az ad sp create-for-rbac -n "User_Test_ASPN"
# {
#   "appId": "cf95e80c-b048-41de-b60c-cc7258a47a05",
#   "displayName": "User_Test_ASPN",
#   "password": "Q4X8Q~jaURKyjz7-Hzrf_c7uN4Nrw-X4pCNQTanK",
#   "tenant": "62bd2232-c68d-4580-9469-942cbf5ad6d1"
# }


print(users_list.content)