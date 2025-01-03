from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('generate_ocel/', views.generate_ocel, name='generate_ocel'),
    path('process_columns/', views.process_columns, name='process_columns'),
]
