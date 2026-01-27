from django.urls import include, path

from . import views, views_contacts, views_financial, views_insurance, views_licenses, views_operations

app_name = "deadlines"

urlpatterns = [
    # Main dashboard views
    path("", views.todo_view, name="todo"),
    path("list/", views.list_view, name="list"),
    path("calendar/", views.calendar_view, name="calendar"),
    # Deadline views
    path("deadline/<int:pk>/", views.deadline_detail, name="deadline_detail"),
    path("deadline/add/", views.deadline_add, name="deadline_add"),
    path(
        "deadline/<int:pk>/complete/", views.deadline_complete, name="deadline_complete"
    ),
    path(
        "deadline/<int:pk>/add-note/", views.deadline_add_note, name="deadline_add_note"
    ),
    # Entity views
    path("entities/", views.entity_list, name="entity_list"),
    path("entity/<str:pk>/", views.entity_detail, name="entity_detail"),
    # Insurance views
    path("insurance/", views_insurance.insurance_list, name="insurance_list"),
    path("insurance/<int:pk>/", views_insurance.insurance_detail, name="insurance_detail"),
    path("insurance/add/", views_insurance.insurance_add, name="insurance_add"),
    path("insurance/<int:pk>/edit/", views_insurance.insurance_edit, name="insurance_edit"),
    # License views
    path("licenses/", views_licenses.license_list, name="license_list"),
    path("license/<int:pk>/", views_licenses.license_detail, name="license_detail"),
    path("license/add/", views_licenses.license_add, name="license_add"),
    path("license/<int:pk>/edit/", views_licenses.license_edit, name="license_edit"),
    # Contact views
    path("contacts/", views_contacts.contact_list, name="contact_list"),
    path("contact/<int:pk>/", views_contacts.contact_detail, name="contact_detail"),
    path("contact/add/", views_contacts.contact_add, name="contact_add"),
    path("contact/<int:pk>/edit/", views_contacts.contact_edit, name="contact_edit"),
    path("contact/<int:pk>/delete/", views_contacts.contact_delete, name="contact_delete"),
    # Operations views (State Accounts, Merchant Processors, Vendors)
    path(
        "state-accounts/",
        views_operations.state_account_list,
        name="state_account_list",
    ),
    path(
        "state-account/<int:pk>/",
        views_operations.state_account_detail,
        name="state_account_detail",
    ),
    path(
        "merchant-processors/",
        views_operations.merchant_processor_list,
        name="merchant_processor_list",
    ),
    path(
        "merchant-processor/<int:pk>/",
        views_operations.merchant_processor_detail,
        name="merchant_processor_detail",
    ),
    path("vendors/", views_operations.vendor_list, name="vendor_list"),
    path("vendor/<int:pk>/", views_operations.vendor_detail, name="vendor_detail"),
    # Financial views - Bank Accounts
    path("bank-accounts/", views_financial.bank_account_list, name="bank_account_list"),
    path(
        "bank-account/<int:pk>/",
        views_financial.bank_account_detail,
        name="bank_account_detail",
    ),
    # Financial views - Credit Cards
    path("credit-cards/", views_financial.credit_card_list, name="credit_card_list"),
    path(
        "credit-card/<int:pk>/",
        views_financial.credit_card_detail,
        name="credit_card_detail",
    ),
    # Financial views - Loans
    path("loans/", views_financial.loan_list, name="loan_list"),
    path("loan/<int:pk>/", views_financial.loan_detail, name="loan_detail"),
]
