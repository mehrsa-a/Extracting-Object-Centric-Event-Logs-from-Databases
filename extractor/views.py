import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
import json
import os
from django.http import JsonResponse
import pm4py
from django.conf import settings
from .utils import convert_to_ocel_format, save_ocel_to_file


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

        file_path = request.session.get('uploaded_file_path')
        if not file_path:
            return render(request, 'extractor/upload_error.html', {'error': 'Uploaded file not found!'})

        try:
            event_log = pd.read_csv(file_path)
            temp_log = event_log.copy()

            temp_log['start_date'] = pd.to_datetime(event_log['Start Date'])
            temp_log['Timestamp'] = temp_log['start_date']
            temp_log.drop(columns=['Start Date', 'End Date'], inplace=True)

            temp_log = temp_log.rename(columns={
                'case ID': 'ocel:eid',
                'Activity': 'ocel:activity',
                'Timestamp': 'ocel:timestamp',
                'Customer ID': 'ocel:type:Customer ID'
            })

            ocel_data = pm4py.convert_log_to_ocel(
                temp_log,
                activity_column='ocel:activity',
                timestamp_column='ocel:timestamp'
            )

            ocel_file_path = os.path.join('media', 'ocel_export_file.json')
            pm4py.write_ocel2_json(ocel_data, ocel_file_path)

            return render(request, 'extractor/ocel_download.html', {'download_url': f'/media/ocel_export_file.json'})
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})


def process_columns(request):
    if request.method == 'POST':
        selected_columns = request.POST.getlist('selected_columns')
        file_path = request.session.get('uploaded_file_path')

        if not file_path or not selected_columns:
            return render(request, 'extractor/upload_error.html', {'error': 'No file or columns selected!'})

        try:
            ocel_data = convert_to_ocel_format(file_path, selected_columns)

            ocel_file_path = os.path.join(settings.MEDIA_ROOT, 'ocel_export.json')
            save_ocel_to_file(ocel_data, ocel_file_path)

            download_url = f"{settings.MEDIA_URL}ocel_export.json"

            return render(request, 'extractor/processed_columns.html', {
                'json_data': json.dumps(ocel_data, indent=4),
                'download_url': download_url
            })
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})
