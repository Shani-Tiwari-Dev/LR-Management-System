from django.contrib import admin

from .models import Attendance, Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "designation", "department", "is_active")
    search_fields = ("code", "name")
    list_filter = ("department", "is_active")


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("date", "employee", "status", "reason")
    list_filter = ("status", "date")
    search_fields = ("employee__name", "employee__code")
    date_hierarchy = "date"
