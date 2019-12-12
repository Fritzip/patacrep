from django.urls import path, re_path
from django.conf.urls import include, url

from django.contrib.auth import views as auth_views

from . import views

app_name = 'patacrep'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:pk>/', views.ChordDetail.as_view(), name='detail'),
    path('ajax/toggle_favorite/', views.toggle_favorite, name='ajax_toggle_favorite'),
    path('ajax/change_start_note/', views.change_start_note, name='ajax_change_start_note'),
    path('ajax/clean_chord/', views.clean, name='ajax_clean_chord'),

    path('<int:chord_id>/confirm_remove/', views.confirm_remove, name='confirm_remove'),
    path('ajax/save_edit/', views.save_edit, name='ajax_save_edit'),

    path('<int:chord_id>/edit/', views.edit, name='edit'),
    path('save_and_next/', views.save_and_next, name='save_and_next'),
    path('ajax/next/', views.next, name='ajax_next'),
    #url(r'^signup/$', views.SignUpView.as_view(), name='signup'),
    #url(r'^save_edit/$', views.save_edit, name='save_edit'),
    # url(r'^ajax/save_edit/$', views.save_edit, name='save_edit'),
    # path('<int:chord_id>/<str:npr>/', views.nextprevrand, name='nextprevrand'),

    # Auth related urls
    path('accounts/', include('django.contrib.auth.urls')), # new
    # url(r'^accounts/login/$', auth_views.LoginView.as_view(template_name='patacrep/login.html'), name='login'),

    # url(r'^logout$', views.LogoutView, { 'next_page': '/', }, name='logout'),

]