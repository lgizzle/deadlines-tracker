from django.urls import path

from . import views_operations

urlpatterns = [
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
]
