from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Entity, License


def get_license_urgency(license_obj):
    """Determine the urgency status of a license based on expiration date."""
    if not license_obj.expiration_date:
        return "normal"

    today = timezone.now().date()
    expiration = license_obj.expiration_date

    if expiration < today:
        return "expired"  # Red - already expired

    days_until = (expiration - today).days

    if days_until <= 30:
        return "critical"  # Orange - expires within 30 days
    elif days_until <= 90:
        return "warning"  # Yellow - expires within 90 days

    return "normal"  # Green - more than 90 days


@login_required
def license_list(request):
    """List all licenses with filtering by entity, license_type, issuing_authority."""
    # Get filter parameters
    entity_filter = request.GET.get("entity", "")
    type_filter = request.GET.get("license_type", "")
    authority_filter = request.GET.get("issuing_authority", "")

    # Base queryset - only active licenses
    licenses = License.objects.filter(status="Active").select_related("entity")

    # Apply filters
    if entity_filter:
        licenses = licenses.filter(entity__entity_code=entity_filter)
    if type_filter:
        licenses = licenses.filter(license_type__icontains=type_filter)
    if authority_filter:
        licenses = licenses.filter(issuing_authority__icontains=authority_filter)

    # Order by expiration date (soonest first, nulls last)
    licenses = licenses.order_by("expiration_date")

    # Add urgency status and days until expiration to each license
    today = timezone.now().date()
    for license_obj in licenses:
        license_obj.urgency_status = get_license_urgency(license_obj)
        if license_obj.expiration_date:
            license_obj.days_until = (license_obj.expiration_date - today).days
        else:
            license_obj.days_until = None

    # Get unique values for filter dropdowns
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    license_types = (
        License.objects.filter(status="Active")
        .values_list("license_type", flat=True)
        .distinct()
        .order_by("license_type")
    )
    issuing_authorities = (
        License.objects.filter(status="Active")
        .values_list("issuing_authority", flat=True)
        .distinct()
        .order_by("issuing_authority")
    )

    # Calculate stats
    expired_count = sum(1 for l in licenses if l.urgency_status == "expired")
    critical_count = sum(1 for l in licenses if l.urgency_status == "critical")
    warning_count = sum(1 for l in licenses if l.urgency_status == "warning")

    context = {
        "licenses": licenses,
        "entities": entities,
        "license_types": license_types,
        "issuing_authorities": issuing_authorities,
        "entity_filter": entity_filter,
        "type_filter": type_filter,
        "authority_filter": authority_filter,
        "stats": {
            "expired": expired_count,
            "critical": critical_count,
            "warning": warning_count,
            "total": licenses.count(),
        },
    }

    return render(request, "deadlines/licenses/license_list.html", context)


@login_required
def license_detail(request, pk):
    """View single license details."""
    license_obj = get_object_or_404(License, pk=pk)
    license_obj.urgency_status = get_license_urgency(license_obj)

    today = timezone.now().date()
    if license_obj.expiration_date:
        license_obj.days_until = (license_obj.expiration_date - today).days
    else:
        license_obj.days_until = None

    context = {
        "license": license_obj,
    }

    return render(request, "deadlines/licenses/license_detail.html", context)


@login_required
def license_add(request):
    """Add new license form."""
    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity")
        license_type = request.POST.get("license_type")
        license_number = request.POST.get("license_number")
        issuing_authority = request.POST.get("issuing_authority")
        issue_date = request.POST.get("issue_date")
        expiration_date = request.POST.get("expiration_date")
        renewal_fee = request.POST.get("renewal_fee")
        notes = request.POST.get("notes")

        if entity_id and license_type and license_number:
            License.objects.create(
                entity_id=entity_id,
                license_type=license_type,
                license_number=license_number,
                issuing_authority=issuing_authority if issuing_authority else "",
                issue_date=issue_date if issue_date else None,
                expiration_date=expiration_date if expiration_date else None,
                renewal_fee=renewal_fee if renewal_fee else None,
                notes=notes if notes else "",
                status="Active",
            )
            return redirect("deadlines:license_list")

    # GET request - show form
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    # Get existing license types for autocomplete suggestions
    existing_types = (
        License.objects.values_list("license_type", flat=True)
        .distinct()
        .order_by("license_type")
    )
    existing_authorities = (
        License.objects.values_list("issuing_authority", flat=True)
        .distinct()
        .order_by("issuing_authority")
    )

    context = {
        "entities": entities,
        "existing_types": existing_types,
        "existing_authorities": existing_authorities,
        "form_action": "Add",
    }

    return render(request, "deadlines/licenses/license_form.html", context)


@login_required
def license_edit(request, pk):
    """Edit license form."""
    license_obj = get_object_or_404(License, pk=pk)

    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity")
        license_type = request.POST.get("license_type")
        license_number = request.POST.get("license_number")
        issuing_authority = request.POST.get("issuing_authority")
        issue_date = request.POST.get("issue_date")
        expiration_date = request.POST.get("expiration_date")
        renewal_fee = request.POST.get("renewal_fee")
        notes = request.POST.get("notes")
        status = request.POST.get("status")

        if entity_id and license_type and license_number:
            license_obj.entity_id = entity_id
            license_obj.license_type = license_type
            license_obj.license_number = license_number
            license_obj.issuing_authority = issuing_authority if issuing_authority else ""
            license_obj.issue_date = issue_date if issue_date else None
            license_obj.expiration_date = expiration_date if expiration_date else None
            license_obj.renewal_fee = renewal_fee if renewal_fee else None
            license_obj.notes = notes if notes else ""
            license_obj.status = status if status else "Active"
            license_obj.save()
            return redirect("deadlines:license_detail", pk=pk)

    # GET request - show form with existing data
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    # Get existing license types for autocomplete suggestions
    existing_types = (
        License.objects.values_list("license_type", flat=True)
        .distinct()
        .order_by("license_type")
    )
    existing_authorities = (
        License.objects.values_list("issuing_authority", flat=True)
        .distinct()
        .order_by("issuing_authority")
    )

    context = {
        "license": license_obj,
        "entities": entities,
        "existing_types": existing_types,
        "existing_authorities": existing_authorities,
        "form_action": "Edit",
    }

    return render(request, "deadlines/licenses/license_form.html", context)
