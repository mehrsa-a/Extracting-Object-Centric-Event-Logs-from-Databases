from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    path('generate_ocel/', views.generate_ocel, name='generate_ocel'),
    # path('process_columns/', views.process_columns, name='process_columns'),
    path('select_case_id/', views.select_case_id, name='select_case_id'),
    path('select_activity/', views.select_activity, name='select_activity'),
    path('select_timestamp/', views.select_timestamp, name='select_timestamp'),
    path('select_sorting_column/', views.select_sorting_column, name='select_sorting_column'),
    path('process_columns/', views.process_columns, name='process_columns'),
]
