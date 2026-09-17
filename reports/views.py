import calendar
from datetime import date
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from attendance.models import Attendance, Employee

MONTHS = [(i, calendar.month_name[i]) for i in range(1, 13)]


def _month_from_request(request):
    today = date.today()
    try:
        month = int(request.GET.get("month", today.month))
        year = int(request.GET.get("year", today.year))
    except (TypeError, ValueError):
        month, year = today.month, today.year
    month = min(max(month, 1), 12)
    return month, year


def _build_month_data(month, year):
    days_in_month = calendar.monthrange(year, month)[1]
    days = list(range(1, days_in_month + 1))

    records = Attendance.objects.filter(
        date__year=year, date__month=month
    ).select_related("employee")

    by_employee = {}
    for record in records:
        by_employee.setdefault(record.employee_id, {})[record.date.day] = record

    rows = []
    for employee in Employee.objects.filter(is_active=True):
        marks = by_employee.get(employee.id, {})
        cells = []
        counts = {"P": 0, "A": 0, "H": 0, "L": 0, "W": 0}
        reasons = []
        for day in days:
            record = marks.get(day)
            if record:
                counts[record.status] += 1
                if record.status in Attendance.REASON_REQUIRED and record.reason:
                    reasons.append(f"{day:02d}: {record.reason}")
                cells.append({"day": day, "code": record.status,
                              "label": record.get_status_display(),
                              "reason": record.reason})
            else:
                cells.append({"day": day, "code": "", "label": "Not marked",
                              "reason": ""})
        payable = counts["P"] + counts["L"] + counts["H"] * 0.5
        rows.append({
            "employee": employee,
            "cells": cells,
            "counts": counts,
            "payable": payable,
            "reasons": reasons,
        })
    return days, rows


@login_required
def monthly_attendance(request):
    month, year = _month_from_request(request)
    days, rows = _build_month_data(month, year)
    return render(request, "reports/monthly_attendance.html", {
        "active": "monthly",
        "month": month,
        "year": year,
        "month_name": calendar.month_name[month],
        "months": MONTHS,
        "years": range(date.today().year - 5, date.today().year + 2),
        "days": days,
        "rows": rows,
        "total_present": sum(r["counts"]["P"] for r in rows),
        "total_absent": sum(r["counts"]["A"] for r in rows),
    })


@login_required
def monthly_attendance_xlsx(request):
    month, year = _month_from_request(request)
    days, rows = _build_month_data(month, year)

    wb = Workbook()
    sheet = wb.active
    sheet.title = f"{calendar.month_abbr[month]} {year}"

    header_fill = PatternFill("solid", fgColor="15202B")
    header_font = Font(color="FFFFFF", bold=True)

    header = ["Code", "Employee", "Department"] + [str(d) for d in days] + [
        "Present", "Absent", "Half day", "Leave", "Week off", "Payable days"
    ]
    sheet.append(header)
    for cell in sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")

    for row in rows:
        employee = row["employee"]
        line = [employee.code, employee.name, employee.department]
        line += [cell["code"] for cell in row["cells"]]
        line += [
            row["counts"]["P"], row["counts"]["A"], row["counts"]["H"],
            row["counts"]["L"], row["counts"]["W"], row["payable"],
        ]
        sheet.append(line)

    sheet.freeze_panes = "D2"
    sheet.column_dimensions["A"].width = 12
    sheet.column_dimensions["B"].width = 26
    sheet.column_dimensions["C"].width = 18

    # Second sheet: every absence with the reason that was recorded.
    reason_sheet = wb.create_sheet("Absence reasons")
    reason_sheet.append(["Date", "Code", "Employee", "Status", "Reason"])
    for cell in reason_sheet[1]:
        cell.fill = header_fill
        cell.font = header_font
    absences = (
        Attendance.objects.filter(date__year=year, date__month=month)
        .exclude(status=Attendance.PRESENT)
        .exclude(status=Attendance.WEEK_OFF)
        .select_related("employee")
        .order_by("date")
    )
    for record in absences:
        reason_sheet.append([
            record.date.strftime("%d-%m-%Y"),
            record.employee.code,
            record.employee.name,
            record.get_status_display(),
            record.reason,
        ])
    reason_sheet.column_dimensions["C"].width = 26
    reason_sheet.column_dimensions["E"].width = 60

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    filename = f"attendance-{year}-{month:02d}.xlsx"
    response = HttpResponse(
        stream.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
