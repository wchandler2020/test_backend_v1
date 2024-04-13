from tableau_api_lib import TableauServerConnection
from tableau_api_lib.utils import querying
from dotenv import load_dotenv
import os
import json


load_dotenv()  # take environment variables from .env.

jorie_server = 'https://10az.online.tableau.com/'
jorie_token_name = 'Test Token 2'
jorie_token_value = 'qowkdlt+SYqin6kzyLUemA==:cYgxuFvfsHtrbc9HSZI7oPa6IbTrf7nJ'
jorie_site_url = 'joriehealthcare'
jorie_site_name = 'joriehealthcare'

jorie_username = 'wchandler@joriehc.com'
jorie_password = 'DEvine11**'


tableau_config = {
    'jorie_tableau_dev': {
        'server': jorie_server,
        'api_version': '3.22',
        # 'username': jorie_username,
        # 'password': jorie_password,
        'personal_access_token_name': jorie_token_name,
        'personal_access_token_secret': jorie_token_value,
        'site_name': jorie_site_name,
        'site_url': jorie_site_url,
    },'test_tableau_dev': {
        'server': 'server',
        'api_version': '3.21',
        'username': 'username',
        'password': 'password',
        # 'personal_access_token_name': jorie_token_name,
        # 'personal_access_token_secret': jorie_token_value,
        'site_name': 'site_name',
        'site_url': 'site_url',
    },
}

connection = TableauServerConnection(config_json=tableau_config, env='jorie_tableau_dev')
connection.sign_in()

def fetch_data(data_id):
    orth_one_view_id = str(data_id)
    visual_orho_one_data = querying.get_view_data_dataframe(connection, view_id=orth_one_view_id)
    data = visual_orho_one_data.to_json()
    return data