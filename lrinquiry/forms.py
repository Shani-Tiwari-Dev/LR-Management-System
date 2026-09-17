from django import forms

from .models import Contact, Inquiry, clean_number


class InquiryForm(forms.ModelForm):
    contact_name = forms.CharField(
        label="Contact person name",
        max_length=120,
        widget=forms.TextInput(attrs={
            "list": "contact-names",
            "autocomplete": "off",
            "placeholder": "Start typing - saved contacts appear below",
        }),
    )
    contact_phone = forms.CharField(
        label="Contact number",
        max_length=20,
        widget=forms.TextInput(attrs={
            "inputmode": "tel",
            "placeholder": "10 digit mobile number",
        }),
    )

    class Meta:
        model = Inquiry
        fields = [
            "inquiry_date", "party_name", "transport_name",
            "bill_series", "bill_no", "lr_no", "remarks", "status",
        ]
        widgets = {
            "inquiry_date": forms.DateInput(attrs={"type": "date"}),
            "party_name": forms.TextInput(attrs={"list": "party-names", "autocomplete": "off"}),
            "transport_name": forms.TextInput(attrs={"list": "transport-names", "autocomplete": "off"}),
            "bill_series": forms.TextInput(attrs={"placeholder": "e.g. GJ"}),
            "bill_no": forms.TextInput(attrs={"placeholder": "e.g. 10482"}),
            "lr_no": forms.TextInput(attrs={"placeholder": "Leave blank until the LR arrives"}),
            "remarks": forms.Textarea(attrs={"rows": 2}),
        }

    def clean_contact_phone(self):
        digits = clean_number(self.cleaned_data["contact_phone"])
        if len(digits) < 10:
            raise forms.ValidationError("Enter at least 10 digits.")
        return digits

    def save(self, commit=True):
        inquiry = super().save(commit=False)
        name = self.cleaned_data["contact_name"].strip()
        phone = self.cleaned_data["contact_phone"]

        contact = Contact.objects.filter(name__iexact=name, phone=phone).first()
        if contact is None:
            contact = Contact.objects.create(
                name=name,
                phone=phone,
                party_name=inquiry.party_name,
                transport_name=inquiry.transport_name,
            )
        else:
            contact.times_used += 1
            contact.save(update_fields=["times_used"])
        inquiry.contact = contact
        if commit:
            inquiry.save()
        return inquiry
