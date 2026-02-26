from .models import PortalUser


def portal_context(request):
    if not request.user.is_authenticated or request.user.is_superuser:
        return {}
    try:
        portal_user = PortalUser.objects.get(email=request.user.email)
        companies = list(portal_user.companies.order_by("name"))
        active_id = request.session.get("active_company_id")
        active = next((c for c in companies if c.pk == active_id), None)
        if active is None and companies:
            active = companies[0]
            request.session["active_company_id"] = active.pk
        return {
            "portal_user": portal_user,
            "active_company": active,
            "user_companies": companies,
        }
    except PortalUser.DoesNotExist:
        return {}
