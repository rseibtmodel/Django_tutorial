from django.urls import path
from . import views

app_name = 'app_testes'

urlpatterns = [
    path('', views.index, name='index'),
]

