"""
Views for global Operations module: State Accounts, Merchant Processors, Vendors.
These views provide cross-entity access to operational data.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Entity, MerchantProcessor, StateAccount, Vendor


@staff_member_required
def state_account_list(request):
    """List all state accounts across all entities."""
    state_filter = request.GET.get("state", "")
    account_type_filter = request.GET.get("account_type", "")

    accounts = StateAccount.objects.filter(status="Active").select_related("entity")

    if state_filter:
        accounts = accounts.filter(state=state_filter)

    if account_type_filter:
        accounts = accounts.filter(account_type=account_type_filter)

    accounts = accounts.order_by("state", "account_type", "entity__entity_code")

    # Get unique states and account types for filter dropdowns
    states = (
        StateAccount.objects.filter(status="Active")
        .values_list("state", flat=True)
        .distinct()
        .order_by("state")
    )
    account_types = (
        StateAccount.objects.filter(status="Active")
        .values_list("account_type", flat=True)
        .distinct()
        .order_by("account_type")
    )

    context = {
        "accounts": accounts,
        "states": states,
        "account_types": account_types,
        "state_filter": state_filter,
        "account_type_filter": account_type_filter,
    }

    return render(request, "deadlines/operations/state_account_list.html", context)


@staff_member_required
def state_account_detail(request, pk):
    """View details of a single state account."""
    account = get_object_or_404(StateAccount, pk=pk)

    context = {
        "account": account,
    }

    return render(request, "deadlines/operations/state_account_detail.html", context)


@staff_member_required
def merchant_processor_list(request):
    """List all merchant processors across all entities."""
    entity_filter = request.GET.get("entity", "")
    processor_filter = request.GET.get("processor", "")

    processors = MerchantProcessor.objects.filter(status="Active").select_related(
        "entity"
    )

    if entity_filter:
        processors = processors.filter(entity__entity_code=entity_filter)

    if processor_filter:
        processors = processors.filter(processor_name__icontains=processor_filter)

    processors = processors.order_by("processor_name", "entity__entity_code")

    # Get unique entities and processor names for filter dropdowns
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    processor_names = (
        MerchantProcessor.objects.filter(status="Active")
        .values_list("processor_name", flat=True)
        .distinct()
        .order_by("processor_name")
    )

    context = {
        "processors": processors,
        "entities": entities,
        "processor_names": processor_names,
        "entity_filter": entity_filter,
        "processor_filter": processor_filter,
    }

    return render(
        request, "deadlines/operations/merchant_processor_list.html", context
    )


@staff_member_required
def merchant_processor_detail(request, pk):
    """View details of a single merchant processor."""
    processor = get_object_or_404(MerchantProcessor, pk=pk)

    context = {
        "processor": processor,
    }

    return render(
        request, "deadlines/operations/merchant_processor_detail.html", context
    )


@staff_member_required
def vendor_list(request):
    """List all vendors across all entities."""
    entity_filter = request.GET.get("entity", "")
    search_query = request.GET.get("q", "")

    vendors = Vendor.objects.filter(status="Active").select_related("entity")

    if entity_filter:
        vendors = vendors.filter(entity__entity_code=entity_filter)

    if search_query:
        vendors = vendors.filter(
            Q(vendor_name__icontains=search_query)
            | Q(purpose__icontains=search_query)
            | Q(account_number__icontains=search_query)
        )

    vendors = vendors.order_by("vendor_name", "entity__entity_code")

    # Get unique entities for filter dropdown
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    context = {
        "vendors": vendors,
        "entities": entities,
        "entity_filter": entity_filter,
        "search_query": search_query,
    }

    return render(request, "deadlines/operations/vendor_list.html", context)


@staff_member_required
def vendor_detail(request, pk):
    """View details of a single vendor."""
    vendor = get_object_or_404(Vendor, pk=pk)

    context = {
        "vendor": vendor,
    }

    return render(request, "deadlines/operations/vendor_detail.html", context)
