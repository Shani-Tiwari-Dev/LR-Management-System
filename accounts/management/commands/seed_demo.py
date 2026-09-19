"""Create a starter admin account plus the LR boy and sample contacts.

    python manage.py seed_demo
"""

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from attendance.models import Attendance, Employee
from lrinquiry.models import Contact, Inquiry

# (code, name, role, area covered, phone) - just the one LR boy.
EMPLOYEES = [
    ("LR-01", "Rakesh Patel", "LR boy", "Ahmedabad", "9825011223"),
]

CONTACTS = [
    ("Jignesh Bhai", "9898011223", "Shree Krishna Traders", "Gati Express"),
    ("Suresh Yadav", "9898044556", "Balaji Agencies", "VRL Logistics"),
]


class Command(BaseCommand):
    help = "Seed a first admin user and sample records."

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin12345")
            self.stdout.write("Created admin / admin12345 - change this password now.")

        for code, name, designation, department, phone in EMPLOYEES:
            Employee.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "designation": designation,
                    "department": department,
                    "phone": phone,
                },
            )

        today = date.today()
        for employee in Employee.objects.all():
            for offset in range(3):
                day = today - timedelta(days=offset)
                Attendance.objects.get_or_create(
                    employee=employee,
                    date=day,
                    defaults={"status": Attendance.PRESENT},  # LR received
                )

        for name, phone, party, transport in CONTACTS:
            contact, _ = Contact.objects.get_or_create(
                name=name, phone=phone,
                defaults={"party_name": party, "transport_name": transport},
            )
            Inquiry.objects.get_or_create(
                inquiry_date=today,
                party_name=party,
                transport_name=transport,
                bill_series="GJ",
                bill_no=str(10400 + contact.id),
                defaults={"contact": contact},
            )

        self.stdout.write(self.style.SUCCESS("Sample data ready."))
