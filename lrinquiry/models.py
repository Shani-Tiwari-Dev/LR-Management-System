import re

from django.conf import settings
from django.db import models
from django.utils import timezone


def clean_number(raw):
    """Keep digits only so wa.me links always work."""
    return re.sub(r"\D", "", raw or "")


class Contact(models.Model):
    """A contact person is stored the first time it is typed, then offered
    as a choice on every later inquiry."""

    name = models.CharField("Contact person name", max_length=120)
    phone = models.CharField("Contact number", max_length=20)
    party_name = models.CharField(max_length=150, blank=True)
    transport_name = models.CharField(max_length=150, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-times_used", "name"]
        unique_together = ("name", "phone")

    def __str__(self):
        return f"{self.name} ({self.phone})"

    def save(self, *args, **kwargs):
        self.phone = clean_number(self.phone)
        super().save(*args, **kwargs)

    @property
    def whatsapp_number(self):
        digits = self.phone
        if len(digits) == 10:
            digits = f"{settings.WHATSAPP_COUNTRY_CODE}{digits}"
        return digits


class Inquiry(models.Model):
    OPEN = "OPEN"
    FOLLOWED = "FOLLOWED"
    CLOSED = "CLOSED"
    STATUS_CHOICES = [
        (OPEN, "Unsolved"),
        (FOLLOWED, "LR coming"),
        (CLOSED, "Solved"),
    ]

    inquiry_date = models.DateField(default=timezone.localdate)
    party_name = models.CharField(max_length=150)
    transport_name = models.CharField(max_length=150)
    bill_series = models.CharField(max_length=20)
    bill_no = models.CharField(max_length=40)
    lr_no = models.CharField("LR number", max_length=60, blank=True)
    contact = models.ForeignKey(
        Contact, on_delete=models.PROTECT, related_name="inquiries"
    )
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-inquiry_date", "-created_at"]
        verbose_name_plural = "Inquiries"

    def __str__(self):
        return f"{self.bill_series}-{self.bill_no} / {self.party_name}"

    @property
    def bill_reference(self):
        return f"{self.bill_series}-{self.bill_no}".strip("-")

    @property
    def whatsapp_url(self):
        text = (
            f"Hello {self.contact.name}, this is regarding LR for bill "
            f"{self.bill_reference} of {self.party_name} "
            f"sent through {self.transport_name}. "
            "Could you please share the LR number and LR date?"
        )
        from urllib.parse import quote

        return f"https://wa.me/{self.contact.whatsapp_number}?text={quote(text)}"
