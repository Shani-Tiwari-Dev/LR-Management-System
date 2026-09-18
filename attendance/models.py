from django.db import models


class Employee(models.Model):
    code = models.CharField("Party code", max_length=20, unique=True)
    name = models.CharField("Party name", max_length=120)
    designation = models.CharField("Transport name", max_length=80, blank=True)
    department = models.CharField("Route / area", max_length=80, blank=True)
    phone = models.CharField("Contact number", max_length=20, blank=True)
    date_joined = models.DateField("Added on", null=True, blank=True)
    is_active = models.BooleanField("Currently tracked", default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Attendance(models.Model):
    PRESENT = "P"
    ABSENT = "A"
    HALF_DAY = "H"
    LEAVE = "L"
    WEEK_OFF = "W"

    STATUS_CHOICES = [
        (PRESENT, "LR received"),
        (ABSENT, "LR not received"),
        (HALF_DAY, "Partially received"),
        (LEAVE, "LR pending"),
        (WEEK_OFF, "Not expected"),
    ]

    # Statuses that require an explanation for why the LR hasn't come in.
    REASON_REQUIRED = {ABSENT, HALF_DAY, LEAVE}

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendance"
    )
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=PRESENT)
    reason = models.TextField(
        "Remarks",
        blank=True,
        help_text="Filled in whenever the LR hasn't been received.",
    )
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee__name"]
        unique_together = ("employee", "date")
        verbose_name_plural = "LR coming status"

    def __str__(self):
        return f"{self.employee.name} {self.date} {self.get_status_display()}"

    @property
    def needs_reason(self):
        return self.status in self.REASON_REQUIRED
