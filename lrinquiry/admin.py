from django.contrib import admin

from .models import Contact, Inquiry


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "party_name", "transport_name", "times_used")
    search_fields = ("name", "phone")


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = (
        "inquiry_date", "party_name", "transport_name",
        "bill_series", "bill_no", "bill_date", "lr_no", "contact", "status",
    )
    list_filter = ("status", "inquiry_date", "transport_name")
    search_fields = ("party_name", "bill_no", "lr_no", "contact__name")
    date_hierarchy = "inquiry_date"
