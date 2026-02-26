from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Companies
    path("companies/", views.company_list, name="company_list"),
    path("companies/add/", views.company_create, name="company_create"),
    path("companies/<int:pk>/", views.company_detail, name="company_detail"),
    path("companies/<int:pk>/edit/", views.company_edit, name="company_edit"),
    path("companies/<int:pk>/delete/", views.company_delete, name="company_delete"),
    path("companies/<int:pk>/logo/", views.company_logo_upload, name="company_logo_upload"),

    # Addresses (nested under company)
    path("companies/<int:company_pk>/addresses/add/", views.address_create, name="address_create"),
    path("companies/<int:company_pk>/addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("companies/<int:company_pk>/addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("companies/<int:company_pk>/addresses/<int:pk>/set-main/", views.address_set_main, name="address_set_main"),

    # Company-User links
    path("companies/<int:company_pk>/users/add/", views.company_user_add, name="company_user_add"),
    path("companies/<int:company_pk>/users/<int:pk>/remove/", views.company_user_remove, name="company_user_remove"),

    # Company Relationships
    path("companies/<int:company_pk>/relationships/add/", views.company_relationship_add, name="company_relationship_add"),
    path("companies/<int:company_pk>/relationships/<int:pk>/delete/", views.company_relationship_delete, name="company_relationship_delete"),

    # Users
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),

    # Regular user views (my_ prefix)
    path("my/", views.my_dashboard, name="my_dashboard"),
    path("my/company/", views.my_company_detail, name="my_company_detail"),
    path("my/company/edit/", views.my_company_edit, name="my_company_edit"),
    path("my/company/logo/", views.my_company_logo_upload, name="my_company_logo_upload"),
    path("my/company/select/", views.my_company_select, name="my_company_select"),
    path("my/company/switch/<int:pk>/", views.my_company_switch, name="my_company_switch"),
    path("my/company/addresses/add/", views.my_address_create, name="my_address_create"),
    path("my/company/addresses/<int:pk>/edit/", views.my_address_edit, name="my_address_edit"),
    path("my/company/addresses/<int:pk>/delete/", views.my_address_delete, name="my_address_delete"),
    path("my/company/addresses/<int:pk>/set-main/", views.my_address_set_main, name="my_address_set_main"),
    path("my/users/", views.my_user_list, name="my_user_list"),
    path("my/users/add/", views.my_user_create, name="my_user_create"),
    path("my/users/<int:pk>/", views.my_user_detail, name="my_user_detail"),
    path("my/users/<int:pk>/edit/", views.my_user_edit, name="my_user_edit"),
    path("my/users/<int:pk>/remove/", views.my_user_remove, name="my_user_remove"),

    # Parkour game
    path("parkour/", views.parkour_game, name="parkour_game"),
]
