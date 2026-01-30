"""
Financial views for Bank Accounts, Credit Cards, and Loans.

These views provide global list and detail views across all entities,
with filtering capabilities.
"""

import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import BankAccount, CreditCard, Entity, Loan

# Security audit logger for PCI DSS compliance
audit_logger = logging.getLogger("security.audit")


# =============================================================================
# AJAX endpoints for sensitive data (never render in HTML DOM)
# =============================================================================


@staff_member_required
@require_GET
def get_sensitive_card_data(request, pk):
    """AJAX endpoint to fetch sensitive credit card data."""
    card = get_object_or_404(CreditCard, pk=pk)
    field = request.GET.get("field", "")

    # SECURITY: Log all access to cardholder data (PCI DSS 10.2)
    audit_logger.warning(
        f"SENSITIVE_DATA_ACCESS: user={request.user.username} "
        f"type=credit_card card_id={pk} field={field} "
        f"entity={card.entity.entity_code if card.entity else 'N/A'} "
        f"card_name={card.card_name} last4={card.last4} "
        f"ip={request.META.get('REMOTE_ADDR')} "
        f"user_agent={request.META.get('HTTP_USER_AGENT', '')[:100]}"
    )

    if field == "number":
        return JsonResponse({"value": card.full_card_number or ""})
    elif field == "cvv":
        return JsonResponse({"value": card.cvv or ""})
    elif field == "expiration":
        return JsonResponse({"value": card.expiration or ""})

    return JsonResponse({"error": "Invalid field"}, status=400)


@staff_member_required
@require_GET
def get_sensitive_account_data(request, pk):
    """AJAX endpoint to fetch sensitive bank account data."""
    account = get_object_or_404(BankAccount, pk=pk)
    field = request.GET.get("field", "")

    # SECURITY: Log all access to account data
    audit_logger.warning(
        f"SENSITIVE_DATA_ACCESS: user={request.user.username} "
        f"type=bank_account account_id={pk} field={field} "
        f"entity={account.entity.entity_code if account.entity else 'N/A'} "
        f"bank={account.bank_name} last4={account.account_number_last4} "
        f"ip={request.META.get('REMOTE_ADDR')} "
        f"user_agent={request.META.get('HTTP_USER_AGENT', '')[:100]}"
    )

    if field == "number":
        return JsonResponse({"value": account.full_account_number or ""})

    return JsonResponse({"error": "Invalid field"}, status=400)


@staff_member_required
def bank_account_list(request):
    """List all active bank accounts, filterable by entity and bank_name."""
    entity_filter = request.GET.get("entity", "")
    bank_filter = request.GET.get("bank", "")

    accounts = BankAccount.objects.filter(status="Active").select_related("entity")

    if entity_filter:
        accounts = accounts.filter(entity__entity_code=entity_filter)
    if bank_filter:
        accounts = accounts.filter(bank_name__icontains=bank_filter)

    accounts = accounts.order_by("entity__entity_code", "bank_name")

    # Get filter options
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    banks = (
        BankAccount.objects.filter(status="Active")
        .values_list("bank_name", flat=True)
        .distinct()
        .order_by("bank_name")
    )

    context = {
        "accounts": accounts,
        "entities": entities,
        "banks": banks,
        "entity_filter": entity_filter,
        "bank_filter": bank_filter,
        "active_nav": "financial",
    }

    return render(request, "deadlines/financial/bank_account_list.html", context)


@staff_member_required
def bank_account_detail(request, pk):
    """View a single bank account's details."""
    account = get_object_or_404(BankAccount, pk=pk)

    context = {
        "account": account,
        "active_nav": "financial",
    }

    return render(request, "deadlines/financial/bank_account_detail.html", context)


@staff_member_required
def credit_card_list(request):
    """List all active credit cards, filterable by entity and network."""
    entity_filter = request.GET.get("entity", "")
    network_filter = request.GET.get("network", "")

    cards = CreditCard.objects.filter(status="Active").select_related("entity")

    if entity_filter:
        cards = cards.filter(entity__entity_code=entity_filter)
    if network_filter:
        cards = cards.filter(network__icontains=network_filter)

    cards = cards.order_by("entity__entity_code", "card_name")

    # Get filter options
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    networks = (
        CreditCard.objects.filter(status="Active")
        .exclude(network="")
        .values_list("network", flat=True)
        .distinct()
        .order_by("network")
    )

    context = {
        "cards": cards,
        "entities": entities,
        "networks": networks,
        "entity_filter": entity_filter,
        "network_filter": network_filter,
        "active_nav": "financial",
    }

    return render(request, "deadlines/financial/credit_card_list.html", context)


@staff_member_required
def credit_card_detail(request, pk):
    """View a single credit card's details."""
    card = get_object_or_404(CreditCard, pk=pk)

    context = {
        "card": card,
        "active_nav": "financial",
    }

    return render(request, "deadlines/financial/credit_card_detail.html", context)


@staff_member_required
def loan_list(request):
    """List all active loans, filterable by entity, lender, and loan_type."""
    entity_filter = request.GET.get("entity", "")
    lender_filter = request.GET.get("lender", "")
    type_filter = request.GET.get("type", "")

    loans = Loan.objects.filter(status="Active").select_related("entity")

    if entity_filter:
        loans = loans.filter(entity__entity_code=entity_filter)
    if lender_filter:
        loans = loans.filter(lender__icontains=lender_filter)
    if type_filter:
        loans = loans.filter(loan_type__icontains=type_filter)

    # Sort by maturity_date (soonest first), then by entity
    loans = loans.order_by("maturity_date", "entity__entity_code")

    # Get filter options
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    lenders = (
        Loan.objects.filter(status="Active")
        .values_list("lender", flat=True)
        .distinct()
        .order_by("lender")
    )
    loan_types = (
        Loan.objects.filter(status="Active")
        .values_list("loan_type", flat=True)
        .distinct()
        .order_by("loan_type")
    )

    context = {
        "loans": loans,
        "entities": entities,
        "lenders": lenders,
        "loan_types": loan_types,
        "entity_filter": entity_filter,
        "lender_filter": lender_filter,
        "type_filter": type_filter,
        "active_nav": "financial",
    }

    return render(request, "deadlines/financial/loan_list.html", context)


@staff_member_required
def loan_detail(request, pk):
    """View a single loan's details."""
    loan = get_object_or_404(Loan, pk=pk)

    context = {
        "loan": loan,
        "active_nav": "financial",
    }

    return render(request, "deadlines/financial/loan_detail.html", context)
