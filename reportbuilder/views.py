import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from .forms import UploadForm
from .processor import FINAL_COLUMNS, build_workbook, process_workbook

PREVIEW_LIMIT = 200


@login_required
def report_builder(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    context = {"form": form, "columns": FINAL_COLUMNS, "active": "builder"}

    if request.method == "POST" and form.is_valid():
        try:
            data, report = process_workbook(
                form.cleaned_data["excel_file"],
                include_blank_lr=form.cleaned_data["include_blank_lr"],
                merge_series=form.cleaned_data["merge_series"],
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            messages.error(
                request,
                f"That file could not be read ({exc}). Open it in Excel, "
                "save it as .xlsx and try again.",
            )
            return render(request, "reportbuilder/builder.html", context)

        if not data:
            messages.error(
                request,
                "No rows were left. Nothing in the LR number column was marked OK - "
                "tick the empty cell option if blanks mean the LR is missing.",
            )

        context.update({
            "data": data[:PREVIEW_LIMIT],
            "total_rows": len(data),
            "truncated": len(data) > PREVIEW_LIMIT,
            "report": report,
            "payload": json.dumps(data),
            "processed": True,
        })

    return render(request, "reportbuilder/builder.html", context)


@login_required
def download_result(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    try:
        data = json.loads(request.POST.get("payload", "[]"))
    except json.JSONDecodeError:
        data = []

    stream = build_workbook(data)
    response = HttpResponse(
        stream.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="lr-pending-ok.xlsx"'
    return response
