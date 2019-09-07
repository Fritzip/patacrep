from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('patacrep/', include('patacrep.urls')),
    path('admin/', admin.site.urls),
]