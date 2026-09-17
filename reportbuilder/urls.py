from django.urls import path

from . import views

urlpatterns = [
    path("", views.report_builder, name="report_builder"),
    path("download/", views.download_result, name="download_result"),
]
