from django import forms

from .models import Attendance, Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "code", "name", "designation", "department",
            "phone", "date_joined", "is_active",
        ]
        widgets = {
            "date_joined": forms.DateInput(attrs={"type": "date"}),
            "code": forms.TextInput(attrs={"placeholder": "LR-01"}),
            "name": forms.TextInput(attrs={"placeholder": "LR boy's name"}),
        }


class DayPickerForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))


class AttendanceRowForm(forms.Form):
    """One row of the daily marking sheet."""

    employee_id = forms.IntegerField(widget=forms.HiddenInput)
    status = forms.ChoiceField(
        choices=Attendance.STATUS_CHOICES, widget=forms.RadioSelect
    )
    reason = forms.CharField(required=False, widget=forms.TextInput)

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        reason = (cleaned.get("reason") or "").strip()
        if status in Attendance.REASON_REQUIRED and not reason:
            self.add_error("reason", "Add a reason so the record is complete.")
        cleaned["reason"] = reason if status in Attendance.REASON_REQUIRED else ""
        return cleaned
