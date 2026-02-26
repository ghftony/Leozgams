from django.contrib import admin
from .models import Address, Company, PortalUser, CompanyUser, CompanyRelationship

admin.site.register(Address)
admin.site.register(Company)
admin.site.register(PortalUser)
admin.site.register(CompanyUser)
admin.site.register(CompanyRelationship)
