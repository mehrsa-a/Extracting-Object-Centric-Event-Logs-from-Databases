import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
import json
import os
from django.http import JsonResponse


def index(request):
    return render(request, 'extractor/index.html')


def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_path = fs.path(filename)

        try:
            data = pd.read_csv(file_path)
            columns = data.columns.tolist()
            if file_path:
                request.session['uploaded_file_path'] = file_path
            else:
                return render(request, 'extractor/upload_error.html', {'error': 'File path is invalid.'})

            return render(request, 'extractor/upload_success.html', {'columns': columns})
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})

    return render(request, 'extractor/upload.html')


def generate_ocel(request):
    if request.method == 'POST':
        selected_columns = request.POST.getlist('columns')
        if not selected_columns:
            return render(request, 'extractor/upload_error.html',
                          {'error': 'No columns were selected for OCEL extraction.'})

        csv_data = json.loads(request.session.get('csv_data', '{}'))
        df = pd.DataFrame(csv_data)

        try:
            extracted_data = df[selected_columns]

            ocel = {
                "ocel:global-log": {},
                "ocel:events": [],
                "ocel:objects": {}
            }
            for index, row in extracted_data.iterrows():
                event = {
                    "ocel:eid": str(index),
                    "ocel:activity": "Sample Activity",
                    "ocel:timestamp": "2025-01-01T00:00:00Z",
                    "ocel:vmap": row.to_dict(),
                    "ocel:omap": []
                }
                ocel["ocel:events"].append(event)

            ocel_file_path = os.path.join('media', 'ocel.json')
            with open(ocel_file_path, 'w') as f:
                json.dump(ocel, f, indent=4)

            return render(request, 'extractor/ocel_download.html', {'download_url': '/media/ocel.json'})
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})


def process_columns(request):
    if request.method == 'POST':
        selected_columns = request.POST.getlist('selected_columns')
        file_path = request.session.get('uploaded_file_path')

        if not file_path or not selected_columns:
            return render(request, 'extractor/upload_error.html', {'error': 'No file or columns selected!'})

        try:
            data = pd.read_csv(file_path)

            processed_data = data[selected_columns]

            ocel_json = processed_data.to_json(orient='records')

            return JsonResponse({'ocel': ocel_json})
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})
