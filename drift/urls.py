from django.urls import path
from . import views

urlpatterns = [
    path('', views.drift_monitoring, name='drift_monitoring'),
]
