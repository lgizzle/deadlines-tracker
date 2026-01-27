"""
URL patterns for financial views (Bank Accounts, Credit Cards, Loans).
"""

from django.urls import path

from . import views_financial

urlpatterns = [
    # Bank Accounts
    path("bank-accounts/", views_financial.bank_account_list, name="bank_account_list"),
    path(
        "bank-account/<int:pk>/",
        views_financial.bank_account_detail,
        name="bank_account_detail",
    ),
    # Credit Cards
    path("credit-cards/", views_financial.credit_card_list, name="credit_card_list"),
    path(
        "credit-card/<int:pk>/",
        views_financial.credit_card_detail,
        name="credit_card_detail",
    ),
    # Loans
    path("loans/", views_financial.loan_list, name="loan_list"),
    path("loan/<int:pk>/", views_financial.loan_detail, name="loan_detail"),
]
