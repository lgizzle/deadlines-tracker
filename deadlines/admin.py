import logging

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BankAccount,
    Contact,
    CreditCard,
    Deadline,
    Document,
    Entity,
    InsurancePolicy,
    License,
    Loan,
    MerchantProcessor,
    StateAccount,
    Task,
    Vendor,
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
        "ssn_masked",
    ]
    list_filter = ["contact_type", "entity"]
    search_fields = ["first_name", "last_name", "company_name", "email"]
    # SECURITY: Exclude raw SSN field - show masked version only
    exclude = ["ssn"]
    readonly_fields = ["ssn_masked"]

    fieldsets = (
        ("Personal Information", {"fields": ("first_name", "last_name", "title", "ssn_masked")}),
        ("Organization", {"fields": ("entity", "company_name", "contact_type")}),
        ("Contact Details", {"fields": ("email", "phone", "mobile", "address")}),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )

    def ssn_masked(self, obj):
        """Display masked SSN for security."""
        if obj.ssn:
            return f"XXX-XX-{obj.ssn[-4:]}"
        return "-"
    ssn_masked.short_description = "SSN (masked)"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Log access to contact records with SSN."""
        audit_logger = logging.getLogger("security.audit")
        audit_logger.warning(
            f"ADMIN_ACCESS: user={request.user.username} "
            f"model=Contact object_id={object_id} "
            f"ip={request.META.get('REMOTE_ADDR')}"
        )
        return super().change_view(request, object_id, form_url, extra_context)


# =============================================================================
# Operations Models (Added 2026-01-28)
# =============================================================================


@admin.register(StateAccount)
class StateAccountAdmin(admin.ModelAdmin):
    list_display = ["entity", "state", "account_type", "account_number", "portal_name", "status"]
    list_filter = ["status", "state", "account_type", "entity"]
    search_fields = ["account_number", "portal_name", "entity__entity_code"]
    ordering = ["entity", "state", "account_type"]


@admin.register(MerchantProcessor)
class MerchantProcessorAdmin(admin.ModelAdmin):
    list_display = ["entity", "processor_name", "merchant_id", "dba_name", "status"]
    list_filter = ["status", "processor_name", "entity"]
    search_fields = ["processor_name", "merchant_id", "dba_name", "entity__entity_code"]
    ordering = ["entity", "processor_name"]


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ["entity", "vendor_name", "purpose", "account_number", "status"]
    list_filter = ["status", "entity"]
    search_fields = ["vendor_name", "account_number", "purpose", "entity__entity_code"]
    ordering = ["entity", "vendor_name"]


# =============================================================================
# Task & Document Models (Added 2026-01-28)
# =============================================================================


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "entity",
        "task_type",
        "priority_badge",
        "status",
        "due_date",
        "source",
        "created_at",
    ]
    list_filter = ["status", "priority", "task_type", "source", "entity"]
    search_fields = ["title", "description", "email_subject", "email_from"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "completed_at"]

    fieldsets = (
        ("Task", {"fields": ("title", "description", "entity", "task_type", "status")}),
        ("Priority & Due", {"fields": ("priority", "due_date", "amount")}),
        ("Source", {"fields": ("source", "deadline")}),
        (
            "Email Origin",
            {
                "fields": ("email_id", "email_thread_id", "email_subject", "email_from", "email_date"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at", "completed_at"), "classes": ("collapse",)},
        ),
    )

    def priority_badge(self, obj):
        """Show colored priority badge"""
        colors = {
            "urgent": "#dc3545",  # red
            "high": "#fd7e14",  # orange
            "normal": "#28a745",  # green
            "low": "#6c757d",  # gray
        }
        color = colors.get(obj.priority, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.priority.upper() if obj.priority else "N/A",
        )

    priority_badge.short_description = "Priority"


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "filename",
        "entity",
        "document_type",
        "source",
        "document_date",
        "file_size_display",
        "created_at",
    ]
    list_filter = ["document_type", "source", "entity"]
    search_fields = ["filename", "title", "email_subject", "email_from", "sha256_hash"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "sha256_hash"]

    fieldsets = (
        ("Document", {"fields": ("filename", "title", "document_type", "entity")}),
        ("File", {"fields": ("file_path", "file_size", "mime_type", "sha256_hash")}),
        ("Dates & Amounts", {"fields": ("document_date", "due_date", "amount")}),
        ("Source", {"fields": ("source",)}),
        (
            "Email Origin",
            {
                "fields": ("email_id", "email_subject", "email_from", "email_date"),
                "classes": ("collapse",),
            },
        ),
        ("Notes", {"fields": ("notes",), "classes": ("collapse",)}),
    )

    def file_size_display(self, obj):
        """Show file size in human-readable format"""
        if not obj.file_size:
            return "-"
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"

    file_size_display.short_description = "Size"
