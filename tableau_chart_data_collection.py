import mysql.connector
from tableau_api_lib import TableauServerConnection
import json

def connect_to_mysql():
    config = {
        'user': 'root',
        'password': 'devine11',
        'host': 'localhost',
        'database': 'jorie_tableau_data'
    }
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        print("Connected to MySQL database!")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
        return None, None

def connect_to_tableau():
    server = 'https://10az.online.tableau.com/'
    token_name = 'Test Token'
    token_value = 'tmgLnaAoR6GBQQ0GFc+7JQ==:Rnm1XZXs2SFOpiDxk84tuy13t3W8CbWJ'
    site_url = 'joriehealthcare'
    site_name = 'joriehealthcare'

    tableau_config = {
        'server': server,
        'api_version': '3.22',
        'personal_access_token_name': token_name,
        'personal_access_token_secret': token_value,
        'site_name': site_name,
        'site_url': site_url,
    }

    connection = TableauServerConnection(config_json=tableau_config, env='jorie_tableau_dev')
    try:
        connection.sign_in()
        print("Connected to Tableau Server!")
        return connection
    except Exception as e:
        print(f"Error connecting to Tableau Server: {e}")
        return None

def insert_chart_data_into_table(conn, cursor, view_id, view_name, work_book_name, data, table_name):
    try:
        chart_data = json.dumps(data)
        values = (view_id, view_name, work_book_name, chart_data)
        sql = f"INSERT INTO tb_{table_name}_chart_data (view_id, view_name, workbook_name, chart_data) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, values)
        conn.commit()
    except Exception as e:
        print(f"An error occurred while inserting data into the table: {e}")

def get_chart_data_from_dataframe(views_df, conn, cursor, tableau_connection):
    if not conn or not cursor or not tableau_connection:
        print("Database or Tableau connection is not established.")
        return

    workbook_tables = {
        'Live - ECA': 'eca',
        'Live - Manchester': 'manchester',
        'Live - ONE': 'one'
    }

    chart_url_names = [
        'ARBuckets-121Version', 'ARBuckets-Variance121Version', 'PayerMixTable', 
        'ClaimVolumeTrending', 'ClaimResultTrends', 'RevenueTrends'
    ]

    count = 0
    for index, row in views_df.iterrows():
        count += 1
        print('interaction: ', count)
        view_id = row['id']
        view_name = row['viewUrlName']
        work_book_name = row['workbook_name']
            
        try:
            # Assuming querying.get_view_data_dataframe() is replaced with Tableau API calls
            returned_data = tableau_connection.get_view_data_dataframe(view_id=view_id).to_json()
            data = json.loads(returned_data)
            
            if any(chart_url_name in view_name for chart_url_name in chart_url_names):
                if work_book_name in workbook_tables:
                    table_name = workbook_tables[work_book_name]
                    insert_chart_data_into_table(conn, cursor, view_id, view_name, work_book_name, data, table_name)
        except Exception as e:
            print(f"An error occurred while processing data for view '{view_name}': {e}")

    print('All Data has been loaded...')

# Main script
try:
    print('Starting data retrieval and insertion...')
    conn, cursor = connect_to_mysql()
    tableau_connection = connect_to_tableau()
    if conn and cursor and tableau_connection:
        get_chart_data_from_dataframe(views_df, conn, cursor, tableau_connection)
except Exception as e:
    print(f'Oops, an error occurred: {e}')
finally:
    if conn:
        conn.close()
    if tableau_connection:
        tableau_connection.sign_out()