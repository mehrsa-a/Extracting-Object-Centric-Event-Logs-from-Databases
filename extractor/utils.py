import pandas as pd
import json
from datetime import datetime

def convert_to_ocel_format(file_path, selected_columns):
    data = pd.read_csv(file_path)

    filtered_data = data[selected_columns]

    ocel_data = {
        "eventTypes": [],
        "objectTypes": [],
        "events": [],
        "objects": []
    }

    event_types = filtered_data["Activity"].unique()
    for event_type in event_types:
        ocel_data["eventTypes"].append({
            "name": event_type,
            "attributes": [
                {"name": col, "type": "string"} for col in filtered_data.columns if col not in ["Activity", "Case ID"]
            ]
        })

    object_types = filtered_data["Case ID"].unique()
    for object_type in object_types:
        ocel_data["objectTypes"].append({
            "name": "object",
            "attributes": [
                {"name": "Case ID", "type": "string"}
            ]
        })

    for index, row in filtered_data.iterrows():
        event = {
            "id": f"e{index + 1}",
            "type": row["Activity"],
            # "time": datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S").isoformat() + "Z",
            "attributes": [
                {"name": col, "value": row[col]} for col in filtered_data.columns if col not in ["Activity", "Case ID"]
            ],
            "relationships": [
                {"objectId": f"o{row['Case ID']}", "qualifier": "related-to"}
            ]
        }
        ocel_data["events"].append(event)

    for object_id in object_types:
        ocel_data["objects"].append({
            "id": f"o{object_id}",
            "type": "object",
            "attributes": [
                {"name": "Case ID", "value": object_id}
            ]
        })

    return ocel_data


def save_ocel_to_file(ocel_data, output_path):
    with open(output_path, 'w') as json_file:
        json.dump(ocel_data, json_file, indent=4)
