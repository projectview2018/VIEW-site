from django.conf.urls import include, url
from django.urls import register_converter, path, re_path

from django.contrib import admin
admin.autodiscover()

import blindspotapp.views

# future work : args should be passed in body... so fix views too

urlpatterns = [
    path('api/v1/addvehicle/', blindspotapp.views.addvehicle),
	path('api/v1/getinterestarea/', blindspotapp.views.getinterestarea),
	path('api/v1/getblindarea/', blindspotapp.views.getblindarea),
    path('api/v1/getddata/', blindspotapp.views.getddata),
    path('api/v1/getvehicles/', blindspotapp.views.getvehicles),
    path('api/v1/uploadimages/', blindspotapp.views.uploadimages),
    path('api/v1/getspecificimage/', blindspotapp.views.getspecificimage),
    path('api/v1/getvehicleimages_vruchanged/', blindspotapp.views.getvehicleimages_vruchanged),
    url(r'^addvehicle', blindspotapp.views.index, name='index'),
    path('getinfo/<int:user_data>', blindspotapp.views.getinfo, name='getinfo'),
    url(r'^getinfo', blindspotapp.views.getinfo, name='getinfo'),
    url(r'^visualize', blindspotapp.views.visualize, name='visualize'),
    url(r'^FAQs', blindspotapp.views.FAQs, name='FAQs'),
    url(r'^', blindspotapp.views.home, name='home'),
    path('admin/', admin.site.urls),
]
