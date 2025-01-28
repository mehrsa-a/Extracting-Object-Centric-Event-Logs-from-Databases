import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
import json
import os
import pm4py
from django.conf import settings
from .utils import save_ocel_to_file, get_columns_from_csv


def index(request):
    return render(request, 'extractor/index.html')


def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        file_name = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(file_name)

        try:
            pd.read_csv(file_path)
            if file_path:
                request.session['uploaded_file_path'] = file_path
            else:
                return render(request, 'extractor/upload_error.html', {'error': 'File path is invalid.'})

            return redirect('select_activity')
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})

    return render(request, 'extractor/upload.html')


def select_activity(request):
    if request.method == 'POST':
        selected_activity = request.POST.get('selected_column')
        request.session['activity'] = selected_activity
        return redirect('select_timestamp')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return redirect('upload_file')

    columns = get_columns_from_csv(file_path)
    return render(request, 'extractor/select_column.html', {
        'columns': columns,
        'title': 'Select Activity Column',
        'message': 'Please select the column that represents Activities.',
        'action_url': 'select_activity'
    })


def select_timestamp(request):
    if request.method == 'POST':
        selected_timestamp = request.POST.get('selected_column')
        request.session['timestamp'] = selected_timestamp
        return redirect('select_object_type')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return redirect('upload_file')

    activity = request.session.get('activity')
    columns = [col for col in get_columns_from_csv(file_path) if col != activity]
    return render(request, 'extractor/select_column.html', {
        'columns': columns,
        'title': 'Select Timestamp Column',
        'message': 'Please select the column that represents Timestamps.',
        'action_url': 'select_timestamp'
    })


def select_object_type(request):
    if request.method == 'POST':
        selected_columns = request.POST.getlist('selected_columns')
        if not selected_columns:
            return render(request, 'extractor/upload_error.html', {'error': 'No columns selected!'})

        request.session['object_types'] = selected_columns

        return redirect('select_event_attributes')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return render(request, 'extractor/upload_error.html', {'error': 'Uploaded file not found!'})

    activity = request.session.get('activity')
    timestamp = request.session.get('timestamp')
    columns = [col for col in get_columns_from_csv(file_path) if col not in [activity, timestamp]]

    return render(request, 'extractor/select_multiple_columns.html', {
        'columns': columns,
    })


def select_event_attributes(request):
    if request.method == 'POST':
        selected_attributes = request.POST.getlist('selected_attributes')
        # if not selected_attributes:
        #     return render(request, 'extractor/upload_error.html', {'error': 'No columns selected!'})

        request.session['event_attributes'] = selected_attributes

        return redirect('select_object_attributes')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return render(request, 'extractor/upload_error.html', {'error': 'Uploaded file not found!'})

    activity = request.session.get('activity')
    timestamp = request.session.get('timestamp')
    object_types = request.session.get('object_types', [])

    columns = get_columns_from_csv(file_path)
    excluded_columns = {activity, timestamp, *object_types}
    available_columns = [col for col in columns if col not in excluded_columns]

    return render(request, 'extractor/select_event_attributes.html', {
        'columns': available_columns,
    })


def select_object_attributes(request):
    if request.method == 'POST':
        object_attributes = {}
        for object_type in request.session.get('object_types', []):
            selected_columns = request.POST.getlist(f'attributes_{object_type}')
            object_attributes[object_type] = selected_columns

        request.session['object_attributes'] = object_attributes

        return redirect('process_columns')

    file_path = request.session.get('uploaded_file_path')
    if not file_path:
        return render(request, 'extractor/upload_error.html', {'error': 'Uploaded file not found!'})

    all_columns = get_columns_from_csv(file_path)
    object_types = request.session.get('object_types', [])
    event_attributes = request.session.get('event_attributes')
    excluded_columns = {*object_types, *event_attributes}
    available_columns = [col for col in all_columns if col not in excluded_columns]

    return render(request, 'extractor/select_object_attributes.html', {
        'columns': available_columns,
        'object_types': object_types,
    })


def process_columns(request):
    file_path = request.session.get('uploaded_file_path')
    activity_column = request.session.get('activity')
    timestamp_column = request.session.get('timestamp')
    object_types = request.session.get('object_types')
    selected_event_attributes = request.session.get('event_attributes')
    selected_object_attributes = request.session.get('object_attributes')

    try:
        event_log = pd.read_csv(file_path)

        temp_log = event_log.copy()
        temp_log[timestamp_column] = pd.to_datetime(event_log[timestamp_column])

        event_log = event_log.rename(columns={
            activity_column: 'ocel:activity',
            timestamp_column: 'ocel:timestamp'
        })

        if selected_event_attributes is None:
            selected_event_attributes = []

        if selected_object_attributes is None:
            selected_object_attributes = []
        # for obj_type in object_types:
        #     event_log[f'ocel:type:{obj_type}'] = event_log[obj_type]

        ocel_data = pm4py.convert_log_to_ocel(
            event_log,
            activity_column='ocel:activity',
            timestamp_column='ocel:timestamp',
            object_types=object_types,
            additional_event_attributes=selected_event_attributes,
            additional_object_attributes=selected_object_attributes
        )

        pm4py.write_ocel2_json(ocel_data, 'ocel_file')

        with open('ocel_file.jsonocel', 'r') as file:
            ocel_data = json.load(file)

        if os.path.exists("ocel_file.jsonocel"):
            os.remove("ocel_file.jsonocel")

        ocel_file_path = os.path.join(settings.MEDIA_ROOT, 'ocel_export.json')
        save_ocel_to_file(ocel_data, ocel_file_path)

        download_url = f"{settings.MEDIA_URL}ocel_export.json"
        return render(request, 'extractor/processed_columns.html', {
            'json_data': json.dumps(ocel_data, indent=4),
            'download_url': download_url
        })
    except Exception as e:
        return render(request, 'extractor/upload_error.html', {'error': str(e)})
