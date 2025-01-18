from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_file, name='upload_file'),
    # path('generate_ocel/', views.generate_ocel, name='generate_ocel'),
    # path('process_columns/', views.process_columns, name='process_columns'),
    path('select_activity/', views.select_activity, name='select_activity'),
    path('select_timestamp/', views.select_timestamp, name='select_timestamp'),
    path('select_object_type/', views.select_object_type, name='select_object_type'),
    path('process_columns/', views.process_columns, name='process_columns'),
    path('select-event-attributes/', views.select_event_attributes, name='select_event_attributes'),
    path('select-object-attributes/', views.select_object_attributes, name='select_object_attributes'),
]
