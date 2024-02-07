from django.urls import path

from . import views


app_name = 'lidar'
urlpatterns = [
    path('', views.index, name='index'),
    path('add_vehicle/', views.add_vehicle, name='add_vehicle'),
    path('data_upload/', views.data_upload, name='data_upload'),
    path('faq/', views.faq, name='faq'),
    path('vehicle_database_loading/', views.vehicle_database_loading, name='vehicle_database_loading'),
    path('vehicle_database_table/', views.vehicle_database_table, name='vehicle_database_table'),
]
