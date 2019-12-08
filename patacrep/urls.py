from django.urls import path, re_path
from django.conf.urls import include, url

from . import views

app_name = 'patacrep'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:pk>/', views.ChordDetail.as_view(), name='detail'),
    path('<int:chord_id>/edit/', views.edit, name='edit'),
    path('<int:chord_id>/confirm_remove/', views.confirm_remove, name='confirm_remove'),
    #url(r'^signup/$', views.SignUpView.as_view(), name='signup'),
    #url(r'^save_edit/$', views.save_edit, name='save_edit'),
    # url(r'^ajax/save_edit/$', views.save_edit, name='save_edit'),
    path('save_and_next/', views.save_and_next, name='save_and_next'),
    path('ajax/next/', views.next, name='ajax_next'),
    path('ajax/clean/', views.clean, name='ajax_clean'),
    path('save_edit/', views.save_edit, name='save_edit'),
    # path('<int:chord_id>/<str:npr>/', views.nextprevrand, name='nextprevrand'),
]