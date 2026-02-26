from django import forms
from .models import Address, Company, PortalUser, CompanyUser, CompanyRelationship


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["line1", "line2", "line3", "area", "city", "postcode", "country"]
        widgets = {
            "line1": forms.TextInput(attrs={"class": "form-control"}),
            "line2": forms.TextInput(attrs={"class": "form-control"}),
            "line3": forms.TextInput(attrs={"class": "form-control"}),
            "area": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "postcode": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "description", "website", "logo"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
        }


class MainAddressSelectForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["main_address"]
        widgets = {
            "main_address": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields["main_address"].queryset = Address.objects.filter(company=company)
        else:
            self.fields["main_address"].queryset = Address.objects.none()
        self.fields["main_address"].required = False


class PortalUserForm(forms.ModelForm):
    class Meta:
        model = PortalUser
        fields = ["email", "first_name", "last_name", "avatar"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control form-control-solid"}),
            "first_name": forms.TextInput(attrs={"class": "form-control form-control-solid"}),
            "last_name": forms.TextInput(attrs={"class": "form-control form-control-solid"}),
        }


class PortalUserPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("new_password1")
        p2 = cleaned_data.get("new_password2")
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

    def has_password(self):
        return bool(self.cleaned_data.get("new_password1"))


class CompanyUserForm(forms.ModelForm):
    class Meta:
        model = CompanyUser
        fields = ["user"]
        widgets = {
            "user": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            linked_ids = CompanyUser.objects.filter(company=company).values_list("user_id", flat=True)
            self.fields["user"].queryset = PortalUser.objects.exclude(id__in=linked_ids)


class CompanyRelationshipForm(forms.ModelForm):
    ROLE_CHOICES = [
        ("child", "Child company (this company is the parent)"),
        ("parent", "Parent company (this company is the child)"),
        ("customer", "Customer (this company is the supplier)"),
        ("supplier", "Supplier (this company is the customer)"),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Relationship role of the other company",
    )

    class Meta:
        model = CompanyRelationship
        fields = ["to_company", "role"]
        widgets = {
            "to_company": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "to_company": "Other company",
        }

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields["to_company"].queryset = Company.objects.exclude(id=company.id)
        self.fields["to_company"].queryset = Company.objects.all()
        if company:
            self.fields["to_company"].queryset = Company.objects.exclude(id=company.id)

    def save(self, commit=True, from_company=None):
        role = self.cleaned_data["role"]
        to_company = self.cleaned_data["to_company"]

        if role == "child":
            rel_type = "parent_child"
            f, t = from_company, to_company
        elif role == "parent":
            rel_type = "parent_child"
            f, t = to_company, from_company
        elif role == "customer":
            rel_type = "supplier_customer"
            f, t = from_company, to_company
        else:  # supplier
            rel_type = "supplier_customer"
            f, t = to_company, from_company

        obj, _ = CompanyRelationship.objects.get_or_create(
            from_company=f,
            to_company=t,
            relationship_type=rel_type,
        )
        return obj
