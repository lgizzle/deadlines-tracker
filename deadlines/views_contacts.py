"""Views for global contact management (cross-entity)."""

from django.shortcuts import get_object_or_404, redirect, render

from .models import Contact, Entity


def contact_list(request):
    """List all contacts with optional filtering by entity and contact_type."""
    entity_filter = request.GET.get("entity", "")
    contact_type_filter = request.GET.get("contact_type", "")

    # Base queryset - all contacts
    contacts = Contact.objects.all().select_related("entity").order_by(
        "last_name", "first_name"
    )

    # Apply filters
    if entity_filter:
        contacts = contacts.filter(entity__entity_code=entity_filter)
    if contact_type_filter:
        contacts = contacts.filter(contact_type=contact_type_filter)

    # Get filter options
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    contact_types = [choice[0] for choice in Contact.CONTACT_TYPE_CHOICES]

    context = {
        "contacts": contacts,
        "entities": entities,
        "contact_types": contact_types,
        "entity_filter": entity_filter,
        "contact_type_filter": contact_type_filter,
        "active_tab": "contacts",
    }

    return render(request, "deadlines/contacts/contact_list.html", context)


def contact_detail(request, pk):
    """View single contact details."""
    contact = get_object_or_404(Contact, pk=pk)

    context = {
        "contact": contact,
        "active_tab": "contacts",
    }

    return render(request, "deadlines/contacts/contact_detail.html", context)


def contact_add(request):
    """Add a new contact."""
    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity") or None
        contact_type = request.POST.get("contact_type")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        company_name = request.POST.get("company_name", "")
        title = request.POST.get("title", "")
        email = request.POST.get("email", "")
        phone = request.POST.get("phone", "")
        mobile = request.POST.get("mobile", "")
        address = request.POST.get("address", "")
        ssn = request.POST.get("ssn", "")
        notes = request.POST.get("notes", "")

        if first_name and last_name and contact_type:
            Contact.objects.create(
                entity_id=entity_id if entity_id else None,
                contact_type=contact_type,
                first_name=first_name,
                last_name=last_name,
                company_name=company_name,
                title=title,
                email=email,
                phone=phone,
                mobile=mobile,
                address=address,
                ssn=ssn,
                notes=notes,
            )
            return redirect("deadlines:contact_list")

    # GET request - show form
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    contact_types = Contact.CONTACT_TYPE_CHOICES

    context = {
        "entities": entities,
        "contact_types": contact_types,
        "active_tab": "contacts",
    }

    return render(request, "deadlines/contacts/contact_form.html", context)


def contact_edit(request, pk):
    """Edit an existing contact."""
    contact = get_object_or_404(Contact, pk=pk)

    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity") or None
        contact.entity_id = entity_id if entity_id else None
        contact.contact_type = request.POST.get("contact_type")
        contact.first_name = request.POST.get("first_name")
        contact.last_name = request.POST.get("last_name")
        contact.company_name = request.POST.get("company_name", "")
        contact.title = request.POST.get("title", "")
        contact.email = request.POST.get("email", "")
        contact.phone = request.POST.get("phone", "")
        contact.mobile = request.POST.get("mobile", "")
        contact.address = request.POST.get("address", "")
        ssn = request.POST.get("ssn", "")
        # Only update SSN if a new value was provided (not the masked version)
        if ssn and not ssn.startswith("XXX-XX-"):
            contact.ssn = ssn
        contact.notes = request.POST.get("notes", "")

        if contact.first_name and contact.last_name and contact.contact_type:
            contact.save()
            return redirect("deadlines:contact_detail", pk=pk)

    # GET request - show form with existing data
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    contact_types = Contact.CONTACT_TYPE_CHOICES

    context = {
        "contact": contact,
        "entities": entities,
        "contact_types": contact_types,
        "edit_mode": True,
        "active_tab": "contacts",
    }

    return render(request, "deadlines/contacts/contact_form.html", context)


def contact_delete(request, pk):
    """Delete a contact with confirmation."""
    contact = get_object_or_404(Contact, pk=pk)

    if request.method == "POST":
        contact.delete()
        return redirect("deadlines:contact_list")

    # GET request - show confirmation page
    context = {
        "contact": contact,
        "active_tab": "contacts",
    }

    return render(request, "deadlines/contacts/contact_delete.html", context)
