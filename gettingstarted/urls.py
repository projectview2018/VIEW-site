from django.conf.urls import include, url
from django.urls import register_converter, path

from django.contrib import admin
admin.autodiscover()

import hello.views

# Examples:
# url(r'^$', 'gettingstarted.views.home', name='home'),
# url(r'^blog/', include('blog.urls')),

urlpatterns = [
	path('api/v1/<fullvin>/<partialvin>/<vmake>/<vmodel>/<vgvwr>/<perc_vis>/', hello.views.addvehicle),
	path('api/v1/vgvwr/<vgvwr>/', hello.views.getbyvgvwr),
	path('api/v1/perc/<perc>/', hello.views.getbyperc),
	path('api/v1/fullvin/<fullvin>/', hello.views.getbyfullvin),
	path('api/v1/partialvin/<partialvin>/', hello.views.getbypartialvin),
	path('api/v1/vmake/<vmake>/', hello.views.getbyvmake),
	path('api/v1/getmakes/', hello.views.getmakes),
	path('api/v1/getinterestarea/', hello.views.getinterestarea),
	path('api/v1/getblindarea/<NVPs>/<angles>/<DH>/<c>/<d>/', hello.views.getinterestarea),
    url(r'^$', hello.views.index, name='index'),
    url(r'^getinfo', hello.views.getinfo, name='getinfo'),
    url(r'^db', hello.views.db, name='db'),
    path('admin/', admin.site.urls),
 
]
