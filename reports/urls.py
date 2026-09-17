from django.urls import path

from . import views

urlpatterns = [
    path("attendance/", views.monthly_attendance, name="monthly_attendance"),
    path("attendance/export/", views.monthly_attendance_xlsx,
         name="monthly_attendance_xlsx"),
]
