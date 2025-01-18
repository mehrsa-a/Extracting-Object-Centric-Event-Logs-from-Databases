import pandas as pd
import json


def save_ocel_to_file(ocel_data, output_path):
    with open(output_path, 'w') as json_file:
        json.dump(ocel_data, json_file, indent=4)


def get_columns_from_csv(file_path):
    df = pd.read_csv(file_path)
    return list(df.columns)
