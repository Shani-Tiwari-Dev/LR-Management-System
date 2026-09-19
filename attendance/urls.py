from django.urls import path

from . import views

urlpatterns = [
    path("", views.mark_attendance, name="mark_attendance"),
    path("register/", views.day_register, name="day_register"),
    path("records/<int:pk>/delete/", views.delete_attendance, name="attendance_delete"),
    path("employees/", views.employee_list, name="employee_list"),
    path("employees/<int:pk>/", views.employee_form, name="employee_edit"),
]
