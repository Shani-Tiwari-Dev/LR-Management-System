from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Attendance, Employee


class LrComingStatusTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("tester", password="pw12345678")
        cls.employee = Employee.objects.create(code="LR-01", name="Rakesh")

    def setUp(self):
        self.client.login(username="tester", password="pw12345678")

    def sheet(self, status, reason=""):
        return {
            "day": "2026-09-19",
            "att-TOTAL_FORMS": "1", "att-INITIAL_FORMS": "0",
            "att-MIN_NUM_FORMS": "0", "att-MAX_NUM_FORMS": "1000",
            "att-0-employee_id": str(self.employee.id),
            "att-0-status": status,
            "att-0-reason": reason,
        }

    def test_only_two_statuses_exist(self):
        self.assertEqual(
            [label for _, label in Attendance.STATUS_CHOICES],
            ["LR coming", "LR not coming"],
        )

    def test_sheet_shows_only_two_options(self):
        html = self.client.get(reverse("mark_attendance") + "?date=2026-09-19").content.decode()
        self.assertIn("LR coming", html)
        self.assertIn("LR not coming", html)
        for removed in ("Half day", "On leave", "Week off"):
            self.assertNotIn(removed, html)

    def test_removed_statuses_are_rejected(self):
        for code in ("H", "L", "W"):
            response = self.client.post(reverse("mark_attendance"), self.sheet(code, "x"))
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_not_coming_needs_a_remark(self):
        response = self.client.post(reverse("mark_attendance"), self.sheet("A", ""))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Attendance.objects.count(), 0)

    def test_saving_both_statuses(self):
        self.client.post(reverse("mark_attendance"), self.sheet("A", "sick"))
        self.assertEqual(Attendance.objects.get().status, "A")
        self.client.post(reverse("mark_attendance"), self.sheet("P"))
        record = Attendance.objects.get()
        self.assertEqual((record.status, record.reason), ("P", ""))

    def test_monthly_report_and_export(self):
        Attendance.objects.create(employee=self.employee, date=date(2026, 9, 1), status="P")
        Attendance.objects.create(employee=self.employee, date=date(2026, 9, 2), status="A", reason="sick")
        Attendance.objects.create(employee=self.employee, date=date(2026, 10, 1), status="P")
        response = self.client.get(reverse("monthly_attendance"), {"month": 9, "year": 2026})
        self.assertEqual(response.status_code, 200)
        row = response.context["rows"][0]
        self.assertEqual(row["counts"], {"P": 1, "A": 1})
        self.assertEqual(row["payable"], 1)
        html = response.content.decode()
        self.assertNotIn("<th>H</th>", html)
        self.assertNotIn("<th>W</th>", html)
        export = self.client.get(reverse("monthly_attendance_xlsx"), {"month": 12, "year": 2026})
        self.assertEqual(export.status_code, 200)

    def test_absurd_year_does_not_crash(self):
        response = self.client.get(reverse("monthly_attendance"), {"month": 1, "year": 99999})
        self.assertEqual(response.status_code, 200)
