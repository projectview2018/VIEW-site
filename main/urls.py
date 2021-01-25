from django.conf.urls import include, url
from django.urls import register_converter, path

from django.contrib import admin
admin.autodiscover()

import blindspotapp.views

# future work : args should be passed in body... so fix views too

urlpatterns = [
    path('api/v1/addvehicle/', blindspotapp.views.addvehicle),
	path('api/v1/getinterestarea/', blindspotapp.views.getinterestarea),
	path('api/v1/getblindarea/', blindspotapp.views.getblindarea),
    url(r'^addvehicle', blindspotapp.views.index, name='index'),
    path('getinfo/<int:user_data>', blindspotapp.views.getinfo, name='getinfo'),
    url(r'^getinfo', blindspotapp.views.getinfo, name='getinfo'),
    url(r'^', blindspotapp.views.home, name='home'),
    path('admin/', admin.site.urls),
 
]
