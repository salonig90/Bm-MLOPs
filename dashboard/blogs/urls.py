from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_list, name='blog_list'),
    path('drift-detection-insight/', views.drift_detection_blog, name='drift_detection_blog'),
]
