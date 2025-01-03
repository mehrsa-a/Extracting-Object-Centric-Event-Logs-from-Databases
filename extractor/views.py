from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pandas as pd


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


from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import pandas as pd
import json
import os


def generate_ocel(request):
    if request.method == 'POST':
        selected_columns = request.POST.getlist('columns')
        if not selected_columns:
            return render(request, 'extractor/upload_error.html', {'error': 'No columns were selected for OCEL extraction.'})

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


from django.http import JsonResponse


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


from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
import json
import os

# def process_columns(request):
#     if request.method == 'POST':
#         selected_columns = request.POST.getlist('columns')
#         data = request.session.get('uploaded_data')
#
#         if not data:
#             return render(request, 'extractor/upload_error.html', {'error': 'No uploaded data found in session.'})
#
#         try:
#             filtered_data = data[selected_columns]
#             json_output = filtered_data.to_dict(orient='records')
#
#             file_name = "processed_data.json"
#             file_path = os.path.join("processed_files", file_name)
#
#             if not os.path.exists("processed_files"):
#                 os.makedirs("processed_files")
#
#             with open(file_path, "w") as json_file:
#                 json.dump(json_output, json_file, indent=4)
#
#             download_url = f"/media/{file_name}"
#
#             json_pretty = json.dumps(json_output, indent=4)
#
#             return render(request, 'extractor/process_success.html', {
#                 'json_data': json_pretty,
#                 'download_url': download_url,
#             })
#
#         except Exception as e:
#             return render(request, 'extractor/upload_error.html', {'error': str(e)})
#
#     return redirect('upload')
