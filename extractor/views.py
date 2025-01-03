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
            return render(request, 'extractor/upload_success.html', {'columns': columns})
        except Exception as e:
            return render(request, 'extractor/upload_error.html', {'error': str(e)})

    return render(request, 'extractor/upload.html')
