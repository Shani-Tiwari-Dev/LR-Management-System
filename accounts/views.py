from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from attendance.models import Attendance, Employee
from lrinquiry.models import Inquiry


@login_required
def dashboard(request):
    today = date.today()
    marked_today = Attendance.objects.filter(date=today)

    context = {
        "today": today,
        "employee_count": Employee.objects.filter(is_active=True).count(),
        "present_today": marked_today.filter(status=Attendance.PRESENT).count(),
        "absent_today": marked_today.filter(status=Attendance.ABSENT).count(),
        "marked_today": marked_today.exists(),
        "inquiries_today": Inquiry.objects.filter(inquiry_date=today).count(),
        "open_inquiries": Inquiry.objects.filter(status=Inquiry.OPEN).count(),
        "recent_inquiries": Inquiry.objects.select_related("contact")[:6],
        "active": "dashboard",
    }
    return render(request, "accounts/dashboard.html", context)
