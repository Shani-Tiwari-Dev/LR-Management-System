"""LR coming now has only two statuses: "LR coming" (P) and "LR not coming" (A).

Any record saved earlier as Half day (H), On leave (L) or Week off (W) means
the LR boy did not come, so it becomes "LR not coming" (A). The old wording is
kept at the front of the remark so nothing that was recorded is lost.
"""

from django.db import migrations

OLD_LABELS = {"H": "Half day", "L": "On leave", "W": "Week off"}


def to_not_coming(apps, schema_editor):
    Attendance = apps.get_model("attendance", "Attendance")
    for code, label in OLD_LABELS.items():
        for record in Attendance.objects.filter(status=code):
            record.reason = f"{label}: {record.reason}" if record.reason else label
            record.status = "A"
            record.save(update_fields=["status", "reason"])


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0003_alter_attendance_reason_alter_attendance_status_and_more"),
    ]

    operations = [
        # Cannot be undone: the original code is folded into the remark.
        migrations.RunPython(to_not_coming, migrations.RunPython.noop),
    ]
