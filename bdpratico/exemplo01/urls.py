from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index_alias'),
    #path('', views.index, name='index'),
    path('pagina0', views.pagina0, name='pagina0'),
    path('pagina1', views.pagina1, name='pagina1'),
    path('pagina2', views.pagina2, name='pagina2'),
    path('pagina3', views.pagina3, name='pagina3'),
    path('pagina4', views.pagina4, name='pagina4_alias'),
    path('pagina5', views.pagina5, name='pagina5_alias'),
    path('menu', views.pessoa_menu.as_view(), name='menu_alias'),
    path("pessoa_create/", views.pessoa_create.as_view(), name='pessoa_create_alias'),
    path("pessoa_list/", views.pessoa_list.as_view(), name='pessoa_list_alias'),
    path("pessoa_update/<int:pk>/", views.pessoa_update.as_view(),name='pessoa_update_alias'),
    path('pessoa_delete/<int:pk>/', views.pessoa_delete.as_view(),name='pessoa_delete_alias'),
    
]