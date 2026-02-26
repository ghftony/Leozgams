from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.urls import reverse

from .models import Company, Address, PortalUser, CompanyUser, CompanyRelationship
from .forms import (
    AddressForm,
    CompanyForm,
    MainAddressSelectForm,
    PortalUserForm,
    PortalUserPasswordForm,
    CompanyUserForm,
    CompanyRelationshipForm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_active_company(request):
    """Return (portal_user, active_company) for a regular (non-superadmin) user."""
    try:
        portal_user = PortalUser.objects.get(email=request.user.email)
    except PortalUser.DoesNotExist:
        return None, None
    companies = list(portal_user.companies.order_by("name"))
    if not companies:
        return portal_user, None
    active_id = request.session.get("active_company_id")
    active = next((c for c in companies if c.pk == active_id), None)
    if active is None:
        active = companies[0]
        request.session["active_company_id"] = active.pk
    return portal_user, active


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    context = {
        "company_count": Company.objects.count(),
        "user_count": PortalUser.objects.count(),
        "address_count": Address.objects.count(),
        "relationship_count": CompanyRelationship.objects.count(),
    }
    return render(request, "core/dashboard.html", context)


# ---------------------------------------------------------------------------
# Company
# ---------------------------------------------------------------------------

@login_required
def company_list(request):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    companies = Company.objects.select_related("main_address").order_by("name")
    return render(request, "core/company_list.html", {"companies": companies})


@login_required
def company_detail(request, pk):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    company = get_object_or_404(Company, pk=pk)
    addresses = Address.objects.filter(company=company)
    users = CompanyUser.objects.filter(company=company).select_related("user")

    outgoing = CompanyRelationship.objects.filter(from_company=company).select_related("to_company")
    incoming = CompanyRelationship.objects.filter(to_company=company).select_related("from_company")

    relationships = []
    for rel in outgoing:
        if rel.relationship_type == "parent_child":
            relationships.append({"label": "Child company", "company": rel.to_company, "rel": rel})
        else:
            relationships.append({"label": "Customer", "company": rel.to_company, "rel": rel})
    for rel in incoming:
        if rel.relationship_type == "parent_child":
            relationships.append({"label": "Parent company", "company": rel.from_company, "rel": rel})
        else:
            relationships.append({"label": "Supplier", "company": rel.from_company, "rel": rel})

    return render(request, "core/company_detail.html", {
        "company": company,
        "addresses": addresses,
        "users": users,
        "relationships": relationships,
    })


@login_required
def company_create(request):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'Company "{company.name}" created.')
            return redirect("company_detail", pk=company.pk)
    else:
        form = CompanyForm()
    return render(request, "core/company_form.html", {"form": form, "title": "Add Company"})


@login_required
def company_edit(request, pk):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated.")
            return redirect("company_detail", pk=company.pk)
    else:
        form = CompanyForm(instance=company)
    return render(request, "core/company_form.html", {
        "form": form,
        "title": "Edit Company",
        "company": company,
    })


@login_required
def company_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST":
        name = company.name
        company.delete()
        messages.success(request, f'Company "{name}" deleted.')
        return redirect("company_list")
    return render(request, "core/confirm_delete.html", {
        "object": company,
        "object_type": "Company",
        "cancel_url": reverse("company_detail", args=[pk]),
    })


@login_required
def company_logo_upload(request, pk):
    if not request.user.is_superuser:
        return redirect("my_dashboard")
    company = get_object_or_404(Company, pk=pk)
    if request.method == "POST" and request.FILES.get("logo"):
        company.logo = request.FILES["logo"]
        company.save(update_fields=["logo"])
        messages.success(request, "Logo updated.")
    return redirect("company_detail", pk=pk)


# ---------------------------------------------------------------------------
# Address (managed within company context)
# ---------------------------------------------------------------------------

@login_required
def address_create(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.company = company
            address.save()
            if not company.main_address:
                company.main_address = address
                company.save()
            messages.success(request, "Address added.")
            return redirect("company_detail", pk=company_pk)
    else:
        form = AddressForm()
    return render(request, "core/address_form.html", {
        "form": form,
        "company": company,
        "title": "Add Address",
    })


@login_required
def address_edit(request, company_pk, pk):
    company = get_object_or_404(Company, pk=company_pk)
    address = get_object_or_404(Address, pk=pk, company=company)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("company_detail", pk=company_pk)
    else:
        form = AddressForm(instance=address)
    return render(request, "core/address_form.html", {
        "form": form,
        "company": company,
        "title": "Edit Address",
    })


@login_required
def address_delete(request, company_pk, pk):
    company = get_object_or_404(Company, pk=company_pk)
    address = get_object_or_404(Address, pk=pk, company=company)
    if request.method == "POST":
        if company.main_address_id == address.pk:
            company.main_address = None
            company.save()
        address.delete()
        messages.success(request, "Address deleted.")
        return redirect("company_detail", pk=company_pk)
    return render(request, "core/confirm_delete.html", {
        "object": address,
        "object_type": "Address",
        "cancel_url": reverse("company_detail", args=[company_pk]),
    })


@login_required
def address_set_main(request, company_pk, pk):
    company = get_object_or_404(Company, pk=company_pk)
    address = get_object_or_404(Address, pk=pk, company=company)
    company.main_address = address
    company.save()
    messages.success(request, "Main address updated.")
    return redirect("company_detail", pk=company_pk)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

def _set_portal_user_password(portal_user, raw_password):
    from django.contrib.auth.models import User
    try:
        auth_user = User.objects.get(username=portal_user.email)
        auth_user.set_password(raw_password)
        auth_user.save(update_fields=["password"])
    except User.DoesNotExist:
        User.objects.create_user(
            username=portal_user.email,
            email=portal_user.email,
            password=raw_password,
        )


@login_required
def user_list(request):
    if not request.user.is_superuser:
        return redirect("my_user_list")
    users = PortalUser.objects.order_by("last_name", "first_name")
    return render(request, "core/user_list.html", {"users": users})


@login_required
def user_detail(request, pk):
    if not request.user.is_superuser:
        return redirect("my_user_list")
    user = get_object_or_404(PortalUser, pk=pk)
    company_links = CompanyUser.objects.filter(user=user).select_related("company")
    return render(request, "core/user_detail.html", {
        "portal_user": user,
        "company_links": company_links,
    })


@login_required
def user_create(request):
    if not request.user.is_superuser:
        return redirect("my_user_list")
    if request.method == "POST":
        form = PortalUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User {user.first_name} {user.last_name} created.")
            return redirect("user_detail", pk=user.pk)
    else:
        form = PortalUserForm()
    return render(request, "core/user_form.html", {"form": form, "title": "Add User"})


@login_required
def user_edit(request, pk):
    user = get_object_or_404(PortalUser, pk=pk)
    is_superuser = request.user.is_superuser
    if request.method == "POST":
        form = PortalUserForm(request.POST, instance=user)
        password_form = PortalUserPasswordForm(request.POST) if is_superuser else None
        if form.is_valid() and (password_form is None or password_form.is_valid()):
            form.save()
            if password_form and password_form.has_password():
                _set_portal_user_password(user, password_form.cleaned_data["new_password1"])
            messages.success(request, "User updated.")
            return redirect("user_detail", pk=user.pk)
    else:
        form = PortalUserForm(instance=user)
        password_form = PortalUserPasswordForm() if is_superuser else None
    return render(request, "core/user_form.html", {
        "form": form,
        "password_form": password_form,
        "title": "Edit User",
        "portal_user": user,
    })


@login_required
def user_delete(request, pk):
    if not request.user.is_superuser:
        return redirect("my_user_list")
    user = get_object_or_404(PortalUser, pk=pk)
    if request.method == "POST":
        name = f"{user.first_name} {user.last_name}"
        user.delete()
        messages.success(request, f'User "{name}" deleted.')
        return redirect("user_list")
    return render(request, "core/confirm_delete.html", {
        "object": user,
        "object_type": "User",
        "cancel_url": reverse("user_detail", args=[pk]),
    })


# ---------------------------------------------------------------------------
# Company-User links
# ---------------------------------------------------------------------------

@login_required
def company_user_add(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)
    if request.method == "POST":
        form = CompanyUserForm(request.POST, company=company)
        if form.is_valid():
            cu = form.save(commit=False)
            cu.company = company
            try:
                cu.save()
                messages.success(request, "User linked to company.")
            except IntegrityError:
                messages.error(request, "User is already linked to this company.")
            return redirect("company_detail", pk=company_pk)
    else:
        form = CompanyUserForm(company=company)
    return render(request, "core/company_user_form.html", {
        "form": form,
        "company": company,
    })


@login_required
def company_user_remove(request, company_pk, pk):
    company = get_object_or_404(Company, pk=company_pk)
    cu = get_object_or_404(CompanyUser, pk=pk, company=company)
    if request.method == "POST":
        cu.delete()
        messages.success(request, "User removed from company.")
        return redirect("company_detail", pk=company_pk)
    return render(request, "core/confirm_delete.html", {
        "object": cu,
        "object_type": "Company-User Link",
        "cancel_url": reverse("company_detail", args=[company_pk]),
    })


# ---------------------------------------------------------------------------
# Company Relationships
# ---------------------------------------------------------------------------

@login_required
def company_relationship_add(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)
    if request.method == "POST":
        form = CompanyRelationshipForm(request.POST, company=company)
        if form.is_valid():
            form.save(from_company=company)
            messages.success(request, "Relationship added.")
            return redirect("company_detail", pk=company_pk)
    else:
        form = CompanyRelationshipForm(company=company)
    return render(request, "core/relationship_form.html", {
        "form": form,
        "company": company,
    })


@login_required
def company_relationship_delete(request, company_pk, pk):
    company = get_object_or_404(Company, pk=company_pk)
    rel = get_object_or_404(CompanyRelationship, pk=pk)
    if rel.from_company != company and rel.to_company != company:
        messages.error(request, "Not authorised.")
        return redirect("company_detail", pk=company_pk)
    if request.method == "POST":
        rel.delete()
        messages.success(request, "Relationship removed.")
        return redirect("company_detail", pk=company_pk)
    return render(request, "core/confirm_delete.html", {
        "object": rel,
        "object_type": "Relationship",
        "cancel_url": reverse("company_detail", args=[company_pk]),
    })


# ---------------------------------------------------------------------------
# Regular user views (my_ prefix)
# ---------------------------------------------------------------------------

@login_required
def my_dashboard(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None:
        messages.error(request, "No portal user found for your account.")
        from django.contrib.auth import logout
        logout(request)
        return redirect("login")
    return render(request, "core/my_dashboard.html", {
        "active_company": active_company,
    })


@login_required
def my_company_select(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None:
        return redirect("my_dashboard")
    companies = list(portal_user.companies.order_by("name"))
    return render(request, "core/my_company_select.html", {
        "companies": companies,
        "active_company": active_company,
    })


@login_required
def my_company_switch(request, pk):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, _ = _get_active_company(request)
    if portal_user is None:
        return redirect("my_dashboard")
    if not CompanyUser.objects.filter(user=portal_user, company_id=pk).exists():
        messages.error(request, "You are not linked to that company.")
        return redirect("my_company_select")
    request.session["active_company_id"] = pk
    return redirect("my_dashboard")


@login_required
def my_company_detail(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    addresses = Address.objects.filter(company=active_company)
    users = CompanyUser.objects.filter(company=active_company).select_related("user")

    outgoing = CompanyRelationship.objects.filter(from_company=active_company).select_related("to_company")
    incoming = CompanyRelationship.objects.filter(to_company=active_company).select_related("from_company")

    relationships = []
    for rel in outgoing:
        if rel.relationship_type == "parent_child":
            relationships.append({"label": "Child company", "company": rel.to_company, "rel": rel})
        else:
            relationships.append({"label": "Customer", "company": rel.to_company, "rel": rel})
    for rel in incoming:
        if rel.relationship_type == "parent_child":
            relationships.append({"label": "Parent company", "company": rel.from_company, "rel": rel})
        else:
            relationships.append({"label": "Supplier", "company": rel.from_company, "rel": rel})

    return render(request, "core/my_company_detail.html", {
        "company": active_company,
        "addresses": addresses,
        "users": users,
        "relationships": relationships,
    })


@login_required
def my_company_edit(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=active_company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company updated.")
            return redirect("my_company_detail")
    else:
        form = CompanyForm(instance=active_company)
    return render(request, "core/company_form.html", {
        "form": form,
        "title": "Edit Company",
        "cancel_url": reverse("my_company_detail"),
    })


@login_required
def my_company_logo_upload(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")
    if request.method == "POST" and request.FILES.get("logo"):
        active_company.logo = request.FILES["logo"]
        active_company.save(update_fields=["logo"])
        messages.success(request, "Logo updated.")
    return redirect("my_company_detail")


@login_required
def my_address_create(request):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.company = active_company
            address.save()
            if not active_company.main_address:
                active_company.main_address = address
                active_company.save()
            messages.success(request, "Address added.")
            return redirect("my_company_detail")
    else:
        form = AddressForm()
    return render(request, "core/address_form.html", {
        "form": form,
        "company": active_company,
        "title": "Add Address",
        "cancel_url": reverse("my_company_detail"),
    })


@login_required
def my_address_edit(request, pk):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    address = get_object_or_404(Address, pk=pk, company=active_company)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect("my_company_detail")
    else:
        form = AddressForm(instance=address)
    return render(request, "core/address_form.html", {
        "form": form,
        "company": active_company,
        "title": "Edit Address",
        "cancel_url": reverse("my_company_detail"),
    })


@login_required
def my_address_delete(request, pk):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    address = get_object_or_404(Address, pk=pk, company=active_company)
    if request.method == "POST":
        if active_company.main_address_id == address.pk:
            active_company.main_address = None
            active_company.save()
        address.delete()
        messages.success(request, "Address deleted.")
        return redirect("my_company_detail")
    return render(request, "core/confirm_delete.html", {
        "object": address,
        "object_type": "Address",
        "cancel_url": reverse("my_company_detail"),
    })


@login_required
def my_address_set_main(request, pk):
    if request.user.is_superuser:
        return redirect("dashboard")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    address = get_object_or_404(Address, pk=pk, company=active_company)
    active_company.main_address = address
    active_company.save()
    messages.success(request, "Main address updated.")
    return redirect("my_company_detail")


@login_required
def my_user_list(request):
    if request.user.is_superuser:
        return redirect("user_list")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    users = PortalUser.objects.filter(companies=active_company).order_by("last_name", "first_name")
    return render(request, "core/my_user_list.html", {
        "users": users,
        "active_company": active_company,
    })


@login_required
def my_user_detail(request, pk):
    if request.user.is_superuser:
        return redirect("user_detail", pk=pk)
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    user = get_object_or_404(PortalUser, pk=pk, companies=active_company)
    return render(request, "core/my_user_detail.html", {
        "portal_user": user,
        "active_company": active_company,
    })


@login_required
def my_user_create(request):
    if request.user.is_superuser:
        return redirect("user_create")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    if request.method == "POST":
        form = PortalUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            CompanyUser.objects.create(company=active_company, user=user)
            messages.success(request, f"User {user.first_name} {user.last_name} created.")
            return redirect("my_user_detail", pk=user.pk)
    else:
        form = PortalUserForm()
    return render(request, "core/my_user_form.html", {
        "form": form,
        "title": "Add User",
        "cancel_url": reverse("my_user_list"),
        "portal_user": None,
    })


@login_required
def my_user_edit(request, pk):
    if request.user.is_superuser:
        return redirect("user_edit", pk=pk)
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    user = get_object_or_404(PortalUser, pk=pk, companies=active_company)
    if request.method == "POST":
        form = PortalUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated.")
            return redirect("my_user_detail", pk=user.pk)
    else:
        form = PortalUserForm(instance=user)
    return render(request, "core/my_user_form.html", {
        "form": form,
        "title": "Edit User",
        "portal_user": user,
        "cancel_url": reverse("my_user_detail", args=[pk]),
    })


@login_required
def my_user_remove(request, pk):
    if request.user.is_superuser:
        return redirect("user_list")
    portal_user, active_company = _get_active_company(request)
    if portal_user is None or active_company is None:
        return redirect("my_dashboard")

    user = get_object_or_404(PortalUser, pk=pk, companies=active_company)
    cu = get_object_or_404(CompanyUser, user=user, company=active_company)
    if request.method == "POST":
        cu.delete()
        messages.success(request, f"User {user.first_name} {user.last_name} removed from {active_company.name}.")
        return redirect("my_user_list")
    return render(request, "core/confirm_delete.html", {
        "object": user,
        "object_type": "User from company",
        "cancel_url": reverse("my_user_detail", args=[pk]),
    })


# ---------------------------------------------------------------------------
# Parkour Game
# ---------------------------------------------------------------------------

@login_required
def parkour_game(request):
    return render(request, "core/parkour.html")
