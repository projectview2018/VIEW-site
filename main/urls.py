from django.conf.urls import include, url
from django.urls import register_converter, path

from django.contrib import admin
admin.autodiscover()

import blindspotapp.views

# todo : args should be passed in body... so fix views too

urlpatterns = [
	path('api/v1/<fullvin>/<partialvin>/<vmake>/<vmodel>/<vgvwr>/<perc_vis>/', blindspotapp.views.addvehicle),
	path('api/v1/vgvwr/<vgvwr>/', blindspotapp.views.getbyvgvwr),
	path('api/v1/perc/<perc>/', blindspotapp.views.getbyperc),
	path('api/v1/fullvin/<fullvin>/', blindspotapp.views.getbyfullvin),
	path('api/v1/partialvin/<partialvin>/', blindspotapp.views.getbypartialvin),
	path('api/v1/vmake/<vmake>/', blindspotapp.views.getbyvmake),
	path('api/v1/getmakes/', blindspotapp.views.getmakes),
	path('api/v1/getinterestarea/', blindspotapp.views.getinterestarea),
	path('api/v1/getblindarea/', blindspotapp.views.getblindarea),
    url(r'^$', blindspotapp.views.index, name='index'),
    url(r'^getinfo', blindspotapp.views.getinfo, name='getinfo'),
    url(r'^db', blindspotapp.views.db, name='db'),
    path('admin/', admin.site.urls),
 
]
