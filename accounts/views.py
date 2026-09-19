from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from attendance.models import Attendance, Employee
from lrinquiry.models import Inquiry


@login_required
def dashboard(request):
    today = date.today()

    # One query per table instead of one per tile.
    marked = Attendance.objects.filter(date=today).aggregate(
        total=Count("id"),
        present=Count("id", filter=Q(status=Attendance.PRESENT)),
        absent=Count("id", filter=Q(status=Attendance.ABSENT)),
    )
    inquiry_counts = Inquiry.objects.aggregate(
        today=Count("id", filter=Q(inquiry_date=today)),
        unsolved=Count("id", filter=Q(status=Inquiry.OPEN)),
    )

    context = {
        "today": today,
        "employee_count": Employee.objects.filter(is_active=True).count(),
        "present_today": marked["present"],
        "absent_today": marked["absent"],
        "marked_today": marked["total"] > 0,
        "inquiries_today": inquiry_counts["today"],
        "open_inquiries": inquiry_counts["unsolved"],
        "recent_inquiries": Inquiry.objects.select_related("contact")[:6],
        "active": "dashboard",
    }
    return render(request, "accounts/dashboard.html", context)
