from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BankAccount,
    Contact,
    CreditCard,
    Deadline,
    Entity,
    InsurancePolicy,
    License,
    Loan,
)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ["entity_code", "dba_name", "legal_name", "entity_type", "status"]
    list_filter = ["status", "entity_type", "tax_filing_type"]
    search_fields = ["entity_code", "legal_name", "dba_name", "ein"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("entity_code", "legal_name", "dba_name", "ein", "status")},
        ),
        (
            "Classification",
            {"fields": ("entity_type", "tax_filing_type", "formation_date")},
        ),
        (
            "Location",
            {
                "fields": (
                    "physical_address",
                    "physical_city",
                    "physical_state",
                    "physical_zip",
                    "mailing_address",
                )
            },
        ),
        ("Contact Information", {"fields": ("business_phone", "website")}),
        ("Manager", {"fields": ("manager_name", "manager_phone", "manager_email")}),
        (
            "Secretary of State",
            {"fields": ("sos_number", "sos_state", "sos_renewal_date")},
        ),
        (
            "Additional",
            {"fields": ("partnership_splits", "notes"), "classes": ("collapse",)},
        ),
    )


@admin.register(Deadline)
class DeadlineAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "entity",
        "category",
        "next_due",
        "status_badge",
        "autopay",
        "estimated_amount",
    ]
    list_filter = ["status", "category", "frequency", "autopay", "entity"]
    search_fields = ["title", "account_number", "notes"]
    date_hierarchy = "next_due"
    ordering = ["next_due"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "entity", "category", "frequency", "status")},
        ),
        ("Due Date", {"fields": ("next_due", "due_day", "remind_days_before")}),
        (
            "Payment Details",
            {"fields": ("autopay", "account_number", "estimated_amount")},
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )

    def status_badge(self, obj):
        """Show colored status badge based on due date"""
        if obj.is_overdue:
            color = "#dc3545"  # red
            label = "OVERDUE"
        elif obj.is_due_soon:
            color = "#ffc107"  # yellow
            label = f"{obj.days_until_due}d"
        else:
            color = "#28a745"  # green
            label = f"{obj.days_until_due}d"

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            label,
        )

    status_badge.short_description = "Status"


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = [
        "entity",
        "bank_name",
        "account_type",
        "account_number_last4",
        "status",
    ]
    list_filter = ["status", "account_type", "entity"]
    search_fields = ["bank_name", "account_number_last4"]


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ["entity", "card_name", "network", "last4", "credit_limit", "status"]
    list_filter = ["status", "network", "entity"]
    search_fields = ["card_name", "last4"]


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    list_display = [
        "entity",
        "policy_type",
        "carrier",
        "renewal_date",
        "premium_amount",
        "status",
    ]
    list_filter = ["status", "policy_type", "entity"]
    search_fields = ["policy_type", "carrier", "policy_number"]
    date_hierarchy = "renewal_date"


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = [
        "entity",
        "license_type",
        "issuing_authority",
        "expiration_date",
        "status",
    ]
    list_filter = ["status", "entity"]
    search_fields = ["license_type", "license_number", "issuing_authority"]
    date_hierarchy = "expiration_date"


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = [
        "entity",
        "loan_type",
        "lender",
        "current_balance",
        "payment_amount",
        "maturity_date",
        "status",
    ]
    list_filter = ["status", "payment_frequency", "entity"]
    search_fields = ["loan_type", "lender", "account_number"]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("entity", "loan_type", "lender", "account_number", "status")},
        ),
        (
            "Amounts",
            {"fields": ("original_amount", "current_balance", "interest_rate")},
        ),
        ("Payments", {"fields": ("payment_amount", "payment_frequency")}),
        ("Dates", {"fields": ("origination_date", "maturity_date")}),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "company_name",
        "contact_type",
        "entity",
        "email",
        "phone",
    ]
    list_filter = ["contact_type", "entity"]
    search_fields = ["first_name", "last_name", "company_name", "email"]

    fieldsets = (
        ("Personal Information", {"fields": ("first_name", "last_name", "title")}),
        ("Organization", {"fields": ("entity", "company_name", "contact_type")}),
        ("Contact Details", {"fields": ("email", "phone", "mobile", "address")}),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )
