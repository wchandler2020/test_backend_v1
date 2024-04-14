from tableau_api_lib import TableauServerConnection
from tableau_api_lib.utils import querying, flatten_dict_column, flatten_dict_list_column
import pandas as pd
import concurrent.futures
import json
from mysql import connector


class Tableau_Data:
    #mysql connection
    config = {
        'user': 'root',
        'password': 'devine11',
        'host': 'localhost',
        'database': 'jorie_tableau_data'
    }

    conn = connector.connect(**config)
    cursor = conn.cursor()
    print("Connected to MySQL database!")

    
    def client_stats_data(self, client_name):
        if(client_name == "Eyecare Of Atlanta"):
            eca_url_names_list = [
                'NCR-VarianceNew', 'NCR-CurrentNew', 'NCR-ComparisonNew', 'NetRevenue-VarianceNew', 'NetRevenue-CurrentNew',
                'NetRevenue-ComparisonNew',
                'CCR-VarianceNew', 'CCR-CurrentNew', 'CCR-ComparisonNew', 'Charges-VarianceNew', 'Charges-CurrentNew',
                'Charges-ComparisonNew', 'TotalAR-VarianceNew',
                'TotalAR-CurrentNew', 'TotalAR-ComparisonNew', 'ARDays-VarianceNew', 'ARDays-CurrentNew',
                'ARDays-ComparisonNew', 'FEDR-VarianceNew', 'FEDR-CurrentNew',
                'FEDR-ComparisonNew', 'FEDenialsAmts-VarianceNew', 'FEDenialsAmts-CurrentNew',
                'FEDenialsAmts-ComparisonNew', 'Eligibility-VarianceNew', 'EVChecks-CurrentNew',
                'EVChecks-ComparisonNew'
            ]
            
            eca_chart_url_names = [
                'ARBuckets-121Version', 'ARBuckets-Variance121Version', 'ARBuckets-New181Format', 'ARBuckets-Variance181Format', 'PayerMixTable', 'ClaimVolumeTrending', 'ClaimResultTrends'
            ]
            
            return [eca_url_names_list, 'eca', eca_chart_url_names]
    
        elif(client_name == "Manchester"):
            manchester_url_name_list = [
                'NCR-VarianceNew',
                'NCR-CurrentNew',
                'NCR-ComparisonNew',
                'NetRevenue-VarianceNew',
                'NetRevenue-CurrentNew',
                'NetRevenue-ComparisonNew',
                'CCR-VarianceNew',
                'CCR-CurrentNew',
                'CCR-ComparisonNew',
                'Charges-VarianceNew',
                'Charges-CurrentNew',
                'Charges-ComparisonNew',
                'TotalAR-VarianceNew',
                'TotalAR-CurrentNew',
                'TotalAR-ComparisonNew',
                'ARDays-VarianceNew',
                'ARDays-CurrentNew',
                'ARDays-ComparisonNew',
                'FEDR-VarianceNew',
                'FEDR-CurrentNew',
                'FEDR-ComparisonNew',
                'FEDenialsAmts-VarianceNew',
                'FEDenialsAmts-CurrentNew',
                'FEDenialsAmts-ComparisonNew',
                'Eligibility-VarianceNew',
                'EVChecks-CurrentNew',
                'EVChecks-ComparisonNew',
            ]
            
            manchester_chart_url_names = [
                'ARBuckets-121Version', 'ARBuckets-Variance121Version', 'ARBuckets-New181Format', 'ARBuckets-Variance181Format', 'PayerMixTable', 'ClaimVolumeTrending', 'ClaimResultTrends'
            ]

            return [manchester_url_name_list, 'manchester', manchester_chart_url_names]
        
        elif(client_name == 'Ortho Northeast'):
            one_tableau_name_list = [
                'NetRevenueProjectedVariance',
                'NetRevenue2023',
                'NetRevenue2022YTD',
                'NetRevenue-VarianceNew',
                'NetRevenue-CurrentNew',
                'NetRevenue-ComparisonNew',
                'CCR-VarianceNew',
                'CCR-CurrentNew',
                'CCR-ComparisonNew',
                'TotalAR-VarianceNew',
                'TotalAR-CurrentNew',
                'TotalAR-ComparisonNew',
                'ARDays-VarianceNew',
                'ARDays-CurrentNew',
                'ARDays-ComparisonNew',
                'Charges-VarianceNew',
                'Charges-CurrentNew',
                'Charges-ComparisonNew',
                'FEDR-VarianceNew',
                'FEDR-CurrentNew',
                'FEDR-ComparisonNew',
                'Pre-AuthChecks-VarianceNew',
                'PAChecks-CurrentNew',
                'PAChecks-ComparisonNew',
                'ClaimVolume-VarianceNew',
                'ClaimVolume-CurrentNew',
                'ClaimVolume-ComparisonNew',
            ]
            
            one_chart_url_names = [
                'ARBuckets-121Version', 'ARBuckets-Variance121Version', 'ARBuckets-New181Format', 'ARBuckets-Variance181Format', 'PayerMixTable', 'ClaimVolumeTrending', 'ClaimResultTrends'
            ]

        return [one_tableau_name_list, 'one', one_chart_url_names]

    def get_tableau_sql_data(self, client_name):
        cleaned_data_list = []
        data_list = []
        view_url_names_list = self.client_stats_data(client_name)[0]
        table_name = self.client_stats_data(client_name)[1]
        cleaned_data_list = []  # Initialize cleaned_data_list here

        for url_name in view_url_names_list:
            # Fetch the column names dynamically
            self.cursor.execute(f"""SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}_tableau_data'""")
            column_names = [row[0] for row in self.cursor.fetchall() if row[0].startswith("data_col_name_")]

            # Construct the SQL query dynamically
            select_columns = []
            for column_name in column_names:
                value_name = column_name.replace("data_col_name_", "data_col_val_")
                select_columns.extend([
                                          f"CASE WHEN {column_name} IS NOT NULL AND {value_name} IS NOT NULL THEN {column_name} END AS {column_name}",
                                          f"CASE WHEN {column_name} IS NOT NULL AND {value_name} IS NOT NULL THEN {value_name} END AS {value_name}"])

            # Filter out None values from the select_columns list
            select_columns = [col for col in select_columns if col is not None]

            # Construct the final SQL query
            query = f"""SELECT {', '.join(select_columns)}
                        FROM {table_name}_tableau_data
                        WHERE view_name = '{url_name}'"""

            self.cursor.execute(query)

            # Fetch all rows
            rows = self.cursor.fetchall()

            for row in rows:
                data_dict = {}
                # Access by index and handle potential None values
                for i in range(0, len(row), 2):  # Increment by 2 to ensure proper pairs of column name and value
                    if row[i] is not None:  # Check if value is not None
                        column_name = row[i]
                        try:
                            data_dict[column_name] = json.loads(row[i + 1])  # Attempt to parse JSON value
                        except (json.JSONDecodeError, TypeError) as e:
                            # Handle error when JSON parsing fails
                            print(f"Error parsing JSON in column '{column_name}': {e}")
                            # You can choose to ignore this row or handle it differently based on your requirements
                            data_dict[column_name] = None  # Or any other suitable value
                data_list.append(data_dict)

        for i in range(0, len(data_list), 3):
            sub_array = []
            for j in range(3):
                if i + j < len(data_list):
                    item = data_list[i + j]
                    cleaned_item = {key: value for key, value in item.items() if value is not None}
                    sub_array.append(cleaned_item)
            cleaned_data_list.append(sub_array)
        return cleaned_data_list


    def get_chart_data(self, client_name):
        data_list = []
        table_name = self.client_stats_data(client_name)[1]

        # Fetch all rows
        rows = self.cursor.fetchall()
        query = f"""SELECT chart_data 
                    FROM tb_{table_name}_chart_data"""
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        for row in rows:
            data_list.append(row)
        
        print(data_list)
        return data_list

            
        
    
    