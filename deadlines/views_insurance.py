"""
Insurance Policy views for cross-entity insurance management.
"""
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Entity, InsurancePolicy


@login_required
def insurance_list(request):
    """List all insurance policies with filters."""
    # Get filter parameters
    entity_filter = request.GET.get("entity", "")
    policy_type_filter = request.GET.get("policy_type", "")
    carrier_filter = request.GET.get("carrier", "")

    # Base queryset - only active policies, ordered by renewal_date
    policies = InsurancePolicy.objects.filter(status="Active").select_related(
        "entity"
    ).order_by("renewal_date")

    # Apply filters
    if entity_filter:
        policies = policies.filter(entity__entity_code=entity_filter)
    if policy_type_filter:
        policies = policies.filter(policy_type=policy_type_filter)
    if carrier_filter:
        policies = policies.filter(carrier=carrier_filter)

    # Calculate days until renewal and flag policies due soon
    today = date.today()
    thirty_days = today + timedelta(days=30)

    for policy in policies:
        if policy.renewal_date:
            policy.days_until_renewal = (policy.renewal_date - today).days
            policy.is_due_soon = policy.renewal_date <= thirty_days
            policy.is_overdue = policy.renewal_date < today
        else:
            policy.days_until_renewal = None
            policy.is_due_soon = False
            policy.is_overdue = False

    # Get distinct values for filter dropdowns
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    policy_types = (
        InsurancePolicy.objects.filter(status="Active")
        .values_list("policy_type", flat=True)
        .distinct()
        .order_by("policy_type")
    )
    carriers = (
        InsurancePolicy.objects.filter(status="Active")
        .values_list("carrier", flat=True)
        .distinct()
        .order_by("carrier")
    )

    context = {
        "policies": policies,
        "entities": entities,
        "policy_types": policy_types,
        "carriers": carriers,
        "entity_filter": entity_filter,
        "policy_type_filter": policy_type_filter,
        "carrier_filter": carrier_filter,
    }

    return render(request, "deadlines/insurance/insurance_list.html", context)


@login_required
def insurance_detail(request, pk):
    """View single policy details."""
    policy = get_object_or_404(InsurancePolicy, pk=pk)

    # Calculate days until renewal
    today = date.today()
    if policy.renewal_date:
        policy.days_until_renewal = (policy.renewal_date - today).days
        policy.is_due_soon = policy.renewal_date <= (today + timedelta(days=30))
        policy.is_overdue = policy.renewal_date < today
    else:
        policy.days_until_renewal = None
        policy.is_due_soon = False
        policy.is_overdue = False

    context = {
        "policy": policy,
    }

    return render(request, "deadlines/insurance/insurance_detail.html", context)


@login_required
def insurance_add(request):
    """Add new insurance policy form."""
    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity")
        policy_type = request.POST.get("policy_type")
        carrier = request.POST.get("carrier")
        policy_number = request.POST.get("policy_number")
        coverage_amount = request.POST.get("coverage_amount")
        premium_amount = request.POST.get("premium_amount")
        renewal_date = request.POST.get("renewal_date")
        notes = request.POST.get("notes")

        if entity_id and policy_type and carrier:
            policy = InsurancePolicy.objects.create(
                entity_id=entity_id,
                policy_type=policy_type,
                carrier=carrier,
                policy_number=policy_number if policy_number else "",
                coverage_amount=coverage_amount if coverage_amount else None,
                premium_amount=premium_amount if premium_amount else None,
                renewal_date=renewal_date if renewal_date else None,
                notes=notes if notes else "",
                status="Active",
            )
            return redirect("deadlines:insurance_detail", pk=policy.pk)

    # GET request - show form
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    # Common policy types for dropdown suggestions
    policy_type_choices = [
        "General Liability",
        "Property",
        "Workers Compensation",
        "Commercial Auto",
        "Professional Liability",
        "Directors & Officers",
        "Cyber Liability",
        "Umbrella",
        "Business Owner's Policy (BOP)",
        "Product Liability",
        "Employment Practices Liability",
        "Liquor Liability",
        "Health Insurance",
        "Life Insurance",
        "Other",
    ]

    context = {
        "entities": entities,
        "policy_type_choices": policy_type_choices,
        "form_title": "Add Insurance Policy",
        "submit_label": "Create Policy",
    }

    return render(request, "deadlines/insurance/insurance_form.html", context)


@login_required
def insurance_edit(request, pk):
    """Edit existing insurance policy."""
    policy = get_object_or_404(InsurancePolicy, pk=pk)

    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity")
        policy_type = request.POST.get("policy_type")
        carrier = request.POST.get("carrier")
        policy_number = request.POST.get("policy_number")
        coverage_amount = request.POST.get("coverage_amount")
        premium_amount = request.POST.get("premium_amount")
        renewal_date = request.POST.get("renewal_date")
        status = request.POST.get("status")
        notes = request.POST.get("notes")

        if entity_id and policy_type and carrier:
            policy.entity_id = entity_id
            policy.policy_type = policy_type
            policy.carrier = carrier
            policy.policy_number = policy_number if policy_number else ""
            policy.coverage_amount = coverage_amount if coverage_amount else None
            policy.premium_amount = premium_amount if premium_amount else None
            policy.renewal_date = renewal_date if renewal_date else None
            policy.status = status if status else "Active"
            policy.notes = notes if notes else ""
            policy.save()
            return redirect("deadlines:insurance_detail", pk=policy.pk)

    # GET request - show form with existing data
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    # Common policy types for dropdown suggestions
    policy_type_choices = [
        "General Liability",
        "Property",
        "Workers Compensation",
        "Commercial Auto",
        "Professional Liability",
        "Directors & Officers",
        "Cyber Liability",
        "Umbrella",
        "Business Owner's Policy (BOP)",
        "Product Liability",
        "Employment Practices Liability",
        "Liquor Liability",
        "Health Insurance",
        "Life Insurance",
        "Other",
    ]

    context = {
        "policy": policy,
        "entities": entities,
        "policy_type_choices": policy_type_choices,
        "form_title": "Edit Insurance Policy",
        "submit_label": "Save Changes",
    }

    return render(request, "deadlines/insurance/insurance_form.html", context)
