from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AttendanceRowForm, EmployeeForm
from .models import Attendance, Employee

AttendanceFormSet = formset_factory(AttendanceRowForm, extra=0)


def _parse_day(raw):
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


@login_required
def mark_attendance(request):
    """The daily sheet: mark present, and give a reason when someone is not."""
    day = _parse_day(request.GET.get("date") or request.POST.get("day"))
    employees = list(Employee.objects.filter(is_active=True))
    existing = {
        a.employee_id: a for a in Attendance.objects.filter(date=day)
    }

    if request.method == "POST":
        formset = AttendanceFormSet(request.POST, prefix="att")
        if formset.is_valid():
            for form in formset:
                data = form.cleaned_data
                Attendance.objects.update_or_create(
                    employee_id=data["employee_id"],
                    date=day,
                    defaults={
                        "status": data["status"],
                        "reason": data["reason"],
                    },
                )
            messages.success(request, f"LR coming status saved for {day:%d %b %Y}.")
            return redirect(f"{request.path}?date={day:%Y-%m-%d}")
        messages.error(request, "Some rows need a remark before this sheet can be saved.")
    else:
        initial = []
        for emp in employees:
            record = existing.get(emp.id)
            initial.append({
                "employee_id": emp.id,
                "status": record.status if record else Attendance.PRESENT,
                "reason": record.reason if record else "",
            })
        formset = AttendanceFormSet(initial=initial, prefix="att")

    rows = list(zip(employees, formset.forms))
    return render(request, "attendance/mark.html", {
        "active": "mark",
        "day": day,
        "rows": rows,
        "formset": formset,
        "already_marked": bool(existing),
        "status_choices": Attendance.STATUS_CHOICES,
        "reason_statuses": "".join(sorted(Attendance.REASON_REQUIRED)),
    })


@login_required
def day_register(request):
    day = _parse_day(request.GET.get("date"))
    records = (
        Attendance.objects.filter(date=day)
        .select_related("employee")
        .order_by("employee__name")
    )
    return render(request, "attendance/register.html", {
        "active": "register",
        "day": day,
        "records": records,
        "present": records.filter(status=Attendance.PRESENT).count(),
        "absent": records.filter(status=Attendance.ABSENT).count(),
    })


@login_required
def employee_list(request):
    query = request.GET.get("q", "").strip()
    employees = Employee.objects.all()
    if query:
        employees = employees.filter(name__icontains=query)
    return render(request, "attendance/employees.html", {
        "active": "employees",
        "employees": employees,
        "query": query,
    })


@login_required
def employee_form(request, pk=None):
    employee = get_object_or_404(Employee, pk=pk) if pk else None
    form = EmployeeForm(request.POST or None, instance=employee)
    if request.method == "POST" and form.is_valid():
        saved = form.save()
        messages.success(request, f"Saved party {saved.name}.")
        return redirect("employee_list")
    return render(request, "attendance/employee_form.html", {
        "active": "employees",
        "form": form,
        "employee": employee,
    })
