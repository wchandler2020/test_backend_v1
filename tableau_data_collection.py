# Import necessary libraries
import mysql.connector  # For MySQL database interaction
import json  # For JSON data manipulation
from tableau_api_lib import TableauServerConnection  # For connecting to Tableau Server
from tableau_api_lib.utils import querying, flatten_dict_column  # For Tableau data manipulation
import pandas as pd  # For DataFrame operations

# MySQL connection configuration
mysql_config = {
    'user': 'root',  # MySQL username
    'password': 'devine11',  # MySQL password
    'host': 'localhost',  # MySQL host address
    'database': 'jorie_tableau_data'  # MySQL database name
}

try:
    # Connect to MySQL database
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor() #used in most cases to retrieve rows from your resultset and then perform operations on that data
    print("Connected to MySQL database!")
except mysql.connector.Error as err:
    print(f"Error: {err}")

# Tableau server configurations
tableau_config = {
    'jorie_tableau_dev': {
        'server': 'https://10az.online.tableau.com/',  # Tableau Server URL
        'api_version': '3.22',  # Tableau Server API version
        'personal_access_token_name': 'Test Token',  # Tableau Personal Access Token name
        'personal_access_token_secret': '',  # Tableau Personal Access Token secret
        'site_name': 'joriehealthcare',  # Tableau site name
        'site_url': 'joriehealthcare'  # Tableau site URL
    },
    'test_tableau_dev': {
        'server': 'https://prod-useast-b.online.tableau.com',  # Tableau Server URL
        'api_version': '3.21',  # Tableau Server API version
        'username': 'william.chandler21@yahoo.com',  # Tableau username
        'password': '',  # Tableau password
        'site_name': 'williamchandlertestacc',  # Tableau site name
        'site_url': 'williamchandlertestacc'  # Tableau site URL
    }
}

# Establish connection to Tableau Server
connection = TableauServerConnection(config_json=tableau_config, env='jorie_tableau_dev')
connection.sign_in()

# Retrieve views data from Tableau Server
views_df = querying.get_views_dataframe(connection)

# Exclude specific views based on their content URL
excluded_urls = ['Regional/sheets/GlobalTemperatures', 'Regional/sheets/FlightDelays', 'Regional/sheets/Economy',
                 'Superstore/sheets/Overview', 'AdminInsightsStarter/sheets/PublishEventDrilldown',
                 'AdminInsightsStarter/sheets/StaleContent', 'AdminInsightsStarter/sheets/StatsforSpaceUsage',
                 'Regional/sheets/Stocks', 'Regional/sheets/College', 'Regional/sheets/Obesity',
                 'Superstore/sheets/OrderDetails', 'Superstore/sheets/CommissionModel', 'Superstore/sheets/Performance',
                 'Superstore/sheets/Shipping', 'Superstore/sheets/Forecast', 'Superstore/sheets/WhatIfForecast',
                 'AdminInsightsStarter/sheets/GroupDrilldown', 'AdminInsightsStarter/sheets/UserDrilldown',
                 'AdminInsightsStarter/sheets/Overview', 'Superstore/sheets/Product', 'Superstore/sheets/Customers',
                 'Traffic and Adoption Drilldown', 'Login Activity Drilldown', 'Traffic and Adoption Drilldown']
for url in excluded_urls:
    views_df = views_df[~views_df['contentUrl'].str.contains(url, na=False)]

# Flatten dictionary columns in views DataFrame
views_df = flatten_dict_column(views_df, keys=['name', 'id'], col_name='workbook')

# Exclude views based on specific criteria
excluded_criteria = ['dashboard', 'RCM Starter_v2019.2', 'Payment Analysis', 'RCM Starter_v10.5', 'Arrow',
                     'CloseIcon', 'Blank', 'MenuIcon', 'UpdatedThrough-New', 'ECALocationsIncluded']
for criteria in excluded_criteria:
    views_df = views_df[~views_df['sheetType'].str.contains(criteria, na=False) |
                        ~views_df['workbook_name'].str.contains(criteria, na=False) |
                        ~views_df['viewUrlName'].str.contains(criteria, na=False)]

# Define function to insert view data into MySQL table
def insert_data_into_table(connection, cursor, view_id, view_name, workbook_name, data, table_name):
    first_key, first_value, second_key, second_value, third_key, third_value = None, None, None, None, None, None
    if len(data) >= 3:
        first_key, first_value = list(data.items())[0]
        second_key, second_value = list(data.items())[1]
        third_key, third_value = list(data.items())[2]
    elif len(data) == 2:
        first_key, first_value = list(data.items())[0]
        second_key, second_value = list(data.items())[1]
    elif len(data) == 1:
        first_key, first_value = list(data.items())[0]

    first_value, second_value, third_value = json.dumps(first_value), json.dumps(second_value), json.dumps(third_value) if third_key else None

    values = (view_id, view_name, workbook_name, first_key, first_value, second_key, second_value, third_key, third_value)
    print('VALUES: ', values)
    sql = f"INSERT INTO {table_name}_tableau_data (view_id, view_name, workbook_name, data_col_name_1, data_col_val_1, data_col_name_2, data_col_val_2, data_col_name_3, data_col_val_3) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor.execute(sql, values)
    conn.commit()

# Define workbook names and their respective table names
workbook_tables = {'Live - ECA': 'eca', 'Live - Manchester': 'manchester', 'Live - ONE': 'one'}

# Iterate through views DataFrame and insert data into MySQL tables
count = 0
for index, row in views_df.iterrows():
    count += 1
    print('interaction: ', count)
    view_id, view_name, workbook_name = row['id'], row['viewUrlName'], row['workbook_name']
    returned_data = querying.get_view_data_dataframe(connection, view_id=view_id).to_json()
    data = json.loads(returned_data)
    if workbook_name in workbook_tables:
        table_name = workbook_tables[workbook_name]
        insert_data_into_table(connection, cursor, view_id, view_name, workbook_name, data, table_name)
    else:
        continue

# Close cursor and connection
cursor.close()
connection.close()
