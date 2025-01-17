import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
import json
import os
from django.http import JsonResponse
import pm4py
from django.conf import settings
from .utils import convert_to_ocel_format, save_ocel_to_file, get_columns_from_csv, get_columns_from_file


def index(request):
    return render(request, 'extractor/index.html')


def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        file_name = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(file_name)

        request.session['uploaded_file_path'] = file_path

        return redirect('select_case_id')

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
    file_path = request.session.get('uploaded_file_path')
    case_id_column = request.session.get('case_id')
    activity_column = request.session.get('activity')
    timestamp_column = request.session.get('timestamp')
    sorting_column = request.session.get('sorting_column')

    try:
        event_log = pd.read_csv(file_path)

        temp_log = event_log.copy()
        temp_log[timestamp_column] = pd.to_datetime(event_log[timestamp_column])
        temp_log['Timestamp'] = temp_log[timestamp_column]

        temp_log = temp_log.rename(columns={
            case_id_column: 'ocel:eid',
            activity_column: 'ocel:activity',
            'Timestamp': 'ocel:timestamp'
        })
        sorting_columns = []
        sorting_columns.append(sorting_column)

        for item in sorting_columns:
            temp_log = temp_log.rename(columns={
                item: f'ocel:type:{item}'
            })

        ocel_data = pm4py.convert_log_to_ocel(
            temp_log,
            activity_column='ocel:activity',
            timestamp_column='ocel:timestamp'
        )

        pm4py.write_ocel2_json(ocel_data, 'ocel_file')

        with open('ocel_file.jsonocel', 'r') as file:
            logs = json.load(file)

        ocel_file_path = os.path.join(settings.MEDIA_ROOT, 'ocel_export.json')
        save_ocel_to_file(logs, ocel_file_path)

        download_url = f"{settings.MEDIA_URL}ocel_export.json"
        return render(request, 'extractor/processed_columns.html', {
            'json_data': json.dumps(logs, indent=4),
            'download_url': download_url
        })
    except Exception as e:
        return render(request, 'extractor/upload_error.html', {'error': str(e)})


def select_case_id(request):
    if request.method == 'POST':
        selected_case_id = request.POST.get('selected_column')
        request.session['case_id'] = selected_case_id  # ذخیره در سشن
        return redirect('select_activity')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return redirect('upload_file')

    columns = get_columns_from_csv(file_path)
    return render(request, 'extractor/select_column.html', {
        'columns': columns,
        'title': 'Select Case ID Column',
        'message': 'Please select the column that represents Case IDs.',
        'action_url': 'select_case_id'
    })


def select_activity(request):
    if request.method == 'POST':
        selected_activity = request.POST.get('selected_column')
        request.session['activity'] = selected_activity  # ذخیره در سشن
        return redirect('select_timestamp')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return redirect('upload_file')

    case_id = request.session.get('case_id')
    columns = [col for col in get_columns_from_csv(file_path) if col != case_id]
    return render(request, 'extractor/select_column.html', {
        'columns': columns,
        'title': 'Select Activity Column',
        'message': 'Please select the column that represents Activities.',
        'action_url': 'select_activity'
    })


def select_timestamp(request):
    if request.method == 'POST':
        selected_timestamp = request.POST.get('selected_column')
        request.session['timestamp'] = selected_timestamp  # ذخیره در سشن
        return redirect('select_sorting_column')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return redirect('upload_file')

    case_id = request.session.get('case_id')
    activity = request.session.get('activity')
    columns = [col for col in get_columns_from_csv(file_path) if col not in [case_id, activity]]
    return render(request, 'extractor/select_column.html', {
        'columns': columns,
        'title': 'Select Timestamp Column',
        'message': 'Please select the column that represents Timestamps.',
        'action_url': 'select_timestamp'
    })


def select_sorting_column(request):
    file_path = request.session.get('uploaded_file_path')

    if not file_path:
        return redirect('upload_file')

    try:
        columns = get_columns_from_file(file_path)
    except ValueError as e:
        return render(request, 'extractor/upload_error.html', {'error': str(e)})

    case_id = request.session.get('case_id')
    activity = request.session.get('activity')
    timestamp = request.session.get('timestamp')

    if request.method == 'POST':
        sorting_column = request.POST.get('sorting_column', None)

        if sorting_column and sorting_column != 'none':
            request.session['sorting_column'] = sorting_column
        else:
            request.session['sorting_column'] = None  # Skip case

        return redirect('process_columns')

    return render(request, 'extractor/select_sorting_column.html', {
        'columns': columns,
        'case_id': case_id,
        'activity': activity,
        'timestamp': timestamp
    })
