from django import forms


class UploadForm(forms.Form):
    excel_file = forms.FileField(
        label="Raw billing file",
        help_text="Accepts .xlsx, .xlsm and .csv, up to 20 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": ".xlsx,.xlsm,.csv,.txt"}),
    )
    include_blank_lr = forms.BooleanField(
        label="Also treat an empty LR number cell as missing",
        required=False,
        initial=False,
    )
    merge_series = forms.BooleanField(
        label="Put the bill series in front of the bill number",
        required=False,
        initial=False,
    )

    def clean_excel_file(self):
        uploaded = self.cleaned_data["excel_file"]
        name = uploaded.name.lower()
        if not name.endswith((".xlsx", ".xlsm", ".csv", ".txt")):
            raise forms.ValidationError(
                "Save the file as .xlsx or .csv first. Old .xls files cannot be read."
            )
        if uploaded.size > 20 * 1024 * 1024:
            raise forms.ValidationError("The file is larger than 20 MB.")
        return uploaded
