import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, Q, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InquiryForm
from .models import Contact, Inquiry


# Unsolved on top, LR coming in the middle, solved sinks to the bottom.
_STATUS_ORDER = Case(
    When(status=Inquiry.OPEN, then=0),
    When(status=Inquiry.FOLLOWED, then=1),
    When(status=Inquiry.CLOSED, then=2),
    output_field=IntegerField(),
)


def _sorted(queryset):
    return queryset.annotate(status_rank=_STATUS_ORDER).order_by(
        "status_rank", "-inquiry_date", "-created_at"
    )


def _parse_day(raw):
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


def _datalists():
    """Saved values offered as choices on the entry form."""
    contacts = Contact.objects.all()[:500]
    return {
        "contacts_json": json.dumps([
            {"name": c.name, "phone": c.phone,
             "party": c.party_name, "transport": c.transport_name}
            for c in contacts
        ]),
        "contact_names": sorted({c.name for c in contacts}),
        "party_names": sorted(
            {p for p in Inquiry.objects.values_list("party_name", flat=True).distinct() if p}
        ),
        "transport_names": sorted(
            {t for t in Inquiry.objects.values_list("transport_name", flat=True).distinct() if t}
        ),
    }


@login_required
def inquiry_dashboard(request):
    """Day wise board: the day's inquiries plus the add form."""
    day = _parse_day(request.GET.get("date"))
    query = request.GET.get("q", "").strip()

    inquiries = Inquiry.objects.select_related("contact")
    if query:
        inquiries = inquiries.filter(
            Q(party_name__icontains=query)
            | Q(transport_name__icontains=query)
            | Q(bill_no__icontains=query)
            | Q(lr_no__icontains=query)
            | Q(contact__name__icontains=query)
        )
        heading = f"Search results for “{query}”"
    else:
        inquiries = inquiries.filter(inquiry_date=day)
        heading = f"Inquiries on {day:%d %b %Y}"

    inquiries = _sorted(inquiries)

    form = InquiryForm(initial={"inquiry_date": day})

    context = {
        "active": "inquiry",
        "day": day,
        "prev_day": day - timedelta(days=1),
        "next_day": day + timedelta(days=1),
        "inquiries": inquiries,
        "heading": heading,
        "query": query,
        "form": form,
        "open_count": inquiries.filter(status=Inquiry.OPEN).count(),
        "pending_lr": inquiries.filter(lr_no="").count(),
    }
    context.update(_datalists())
    return render(request, "lrinquiry/dashboard.html", context)


@login_required
def add_inquiry(request):
    day = _parse_day(request.POST.get("inquiry_date"))
    if request.method != "POST":
        return redirect("inquiry_dashboard")

    form = InquiryForm(request.POST)
    if form.is_valid():
        inquiry = form.save()
        messages.success(
            request,
            f"Inquiry added for bill {inquiry.bill_reference} "
            f"({inquiry.contact.name}).",
        )
        return redirect(f"/lr/?date={inquiry.inquiry_date:%Y-%m-%d}")

    messages.error(request, "Check the highlighted fields and save again.")
    context = {
        "active": "inquiry",
        "day": day,
        "prev_day": day - timedelta(days=1),
        "next_day": day + timedelta(days=1),
        "inquiries": _sorted(Inquiry.objects.select_related("contact").filter(inquiry_date=day)),
        "heading": f"Inquiries on {day:%d %b %Y}",
        "query": "",
        "form": form,
        "open_form": True,
    }
    context.update(_datalists())
    return render(request, "lrinquiry/dashboard.html", context)


@login_required
def edit_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    form = InquiryForm(
        request.POST or None,
        instance=inquiry,
        initial={
            "contact_name": inquiry.contact.name,
            "contact_phone": inquiry.contact.phone,
        },
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Inquiry updated.")
        return redirect(f"/lr/?date={inquiry.inquiry_date:%Y-%m-%d}")

    context = {"form": form, "inquiry": inquiry, "active": "inquiry"}
    context.update(_datalists())
    return render(request, "lrinquiry/edit.html", context)


@login_required
def update_status(request, pk):
    """Quick status change from the board or dashboard card — no need to
    open the edit page just to flip Unsolved / LR coming / Solved."""
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in dict(Inquiry.STATUS_CHOICES):
            inquiry.status = status
            inquiry.save(update_fields=["status"])
            messages.success(
                request,
                f"{inquiry.bill_reference or inquiry.party_name} marked {inquiry.get_status_display()}.",
            )
        else:
            messages.error(request, "That isn't a valid status.")
    referer = request.META.get("HTTP_REFERER")
    return redirect(referer or "inquiry_dashboard")


@login_required
def delete_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == "POST":
        day = inquiry.inquiry_date
        inquiry.delete()
        messages.success(request, "Inquiry removed.")
        return redirect(f"/lr/?date={day:%Y-%m-%d}")
    return redirect("inquiry_dashboard")


@login_required
def contact_lookup(request):
    """Used by the form to fill the number once a saved name is chosen."""
    name = request.GET.get("name", "").strip()
    contact = Contact.objects.filter(name__iexact=name).first()
    if not contact:
        return JsonResponse({"found": False})
    return JsonResponse({
        "found": True,
        "name": contact.name,
        "phone": contact.phone,
        "party_name": contact.party_name,
        "transport_name": contact.transport_name,
    })


@login_required
def contact_book(request):
    return render(request, "lrinquiry/contacts.html", {
        "active": "contacts",
        "contacts": Contact.objects.all(),
    })
