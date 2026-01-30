import calendar as cal
import csv
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Contact, Deadline, Document, Entity, MerchantProcessor, StateAccount, Task, Vendor


def get_deadline_status(deadline):
    """Determine the urgency status of a deadline."""
    today = timezone.now().date()
    next_due = deadline.next_due

    if not next_due:
        return "normal"

    if next_due < today:
        return "overdue"

    days_until = (next_due - today).days
    remind_days = deadline.remind_days_before or 7

    if days_until <= remind_days:
        return "upcoming"

    return "normal"


@login_required
def todo_view(request):
    """To-Do view with actionable items grouped by urgency."""
    today = timezone.now().date()

    # Get all active deadlines
    deadlines = Deadline.objects.filter(
        status__in=["Active", "Autopay"]
    ).select_related("entity")

    # Categorize deadlines
    overdue = []
    this_week = []

    for deadline in deadlines:
        if not deadline.next_due:
            continue

        urgency_status = get_deadline_status(deadline)
        deadline.urgency_status = urgency_status
        deadline.days_until = (
            (deadline.next_due - today).days if deadline.next_due else None
        )

        if urgency_status == "overdue":
            overdue.append(deadline)
        elif urgency_status == "upcoming":
            this_week.append(deadline)

    # Sort by urgency
    overdue.sort(key=lambda x: x.next_due)
    this_week.sort(key=lambda x: x.next_due)

    # Calculate stats - on_track = total active minus overdue and this_week
    on_track = deadlines.count() - len(overdue) - len(this_week)
    stats = {
        "overdue": len(overdue),
        "this_week": len(this_week),
        "on_track": on_track,
    }

    context = {
        "overdue": overdue,
        "this_week": this_week,
        "stats": stats,
        "active_tab": "todo",
    }

    return render(request, "deadlines/todo.html", context)


@login_required
def list_view(request):
    """List view with all deadlines grouped by urgency."""
    today = timezone.now().date()
    entity_filter = request.GET.get("entity", "")

    # Get all active deadlines
    deadlines = Deadline.objects.filter(
        status__in=["Active", "Autopay"]
    ).select_related("entity")

    if entity_filter:
        deadlines = deadlines.filter(entity__entity_code=entity_filter)

    # Categorize deadlines
    overdue = []
    this_week = []
    coming_up = []

    for deadline in deadlines:
        if not deadline.next_due:
            continue

        urgency_status = get_deadline_status(deadline)
        deadline.urgency_status = urgency_status
        deadline.days_until = (
            (deadline.next_due - today).days if deadline.next_due else None
        )

        if urgency_status == "overdue":
            overdue.append(deadline)
        elif urgency_status == "upcoming":
            this_week.append(deadline)
        else:
            coming_up.append(deadline)

    # Sort all by date
    overdue.sort(key=lambda x: x.next_due)
    this_week.sort(key=lambda x: x.next_due)
    coming_up.sort(key=lambda x: x.next_due)

    # Get all entities for filter dropdown
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    context = {
        "overdue": overdue,
        "this_week": this_week,
        "coming_up": coming_up,
        "entities": entities,
        "entity_filter": entity_filter,
        "active_tab": "list",
    }

    return render(request, "deadlines/list.html", context)


@login_required
def calendar_view(request):
    """Calendar view showing deadlines by date."""
    # Get month/year from request or use current
    year = int(request.GET.get("year", timezone.now().year))
    month = int(request.GET.get("month", timezone.now().month))
    entity_filter = request.GET.get("entity", "")

    # Create calendar
    c = cal.Calendar()
    month_days = c.monthdayscalendar(year, month)

    # Get all deadlines for this month
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    deadlines = Deadline.objects.filter(
        status__in=["Active", "Autopay"],
        next_due__gte=start_date,
        next_due__lt=end_date,
    ).select_related("entity")

    if entity_filter:
        deadlines = deadlines.filter(entity__entity_code=entity_filter)

    # Group deadlines by date
    deadlines_by_date = {}
    for deadline in deadlines:
        date_key = deadline.next_due.day
        if date_key not in deadlines_by_date:
            deadlines_by_date[date_key] = []
        deadline.urgency_status = get_deadline_status(deadline)
        deadlines_by_date[date_key].append(deadline)

    # Get selected date deadlines (default to today if in current month)
    selected_day = int(request.GET.get("day", 0))
    if selected_day == 0:
        today = timezone.now().date()
        if today.year == year and today.month == month:
            selected_day = today.day

    selected_deadlines = deadlines_by_date.get(selected_day, [])

    # Navigation dates
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Get all entities for filter
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    context = {
        "month_days": month_days,
        "deadlines_by_date": deadlines_by_date,
        "selected_deadlines": selected_deadlines,
        "selected_day": selected_day,
        "month": month,
        "year": year,
        "month_name": cal.month_name[month],
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "today": timezone.now().date(),
        "entities": entities,
        "entity_filter": entity_filter,
        "active_tab": "calendar",
    }

    return render(request, "deadlines/calendar.html", context)


@login_required
def deadline_detail(request, pk):
    """Detailed view of a single deadline."""
    deadline = get_object_or_404(Deadline, pk=pk)
    deadline.urgency_status = get_deadline_status(deadline)

    context = {
        "deadline": deadline,
    }

    return render(request, "deadlines/deadline_detail.html", context)


@login_required
def deadline_complete(request, pk):
    """Mark a deadline as complete and advance the date."""
    if request.method == "POST":
        deadline = get_object_or_404(Deadline, pk=pk)

        # Advance the next_due date based on frequency
        if deadline.next_due and deadline.frequency:
            if deadline.frequency == "Daily":
                deadline.next_due += timedelta(days=1)
            elif deadline.frequency == "Weekly":
                deadline.next_due += timedelta(weeks=1)
            elif deadline.frequency == "Monthly":
                deadline.next_due += relativedelta(months=1)
            elif deadline.frequency == "Quarterly":
                deadline.next_due += relativedelta(months=3)
            elif deadline.frequency == "Annual":
                deadline.next_due += relativedelta(years=1)

            deadline.save()

        # Return to the referrer or todo page
        return redirect(request.META.get("HTTP_REFERER", "deadlines:todo"))

    return redirect("deadlines:deadline_detail", pk=pk)


@login_required
def deadline_add_note(request, pk):
    """Add a note to a deadline (simplified version)."""
    if request.method == "POST":
        deadline = get_object_or_404(Deadline, pk=pk)
        note_text = request.POST.get("note", "")

        if note_text:
            # Append note to notes field with timestamp
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
            if deadline.notes:
                deadline.notes += f"\n\n[{timestamp}] {note_text}"
            else:
                deadline.notes = f"[{timestamp}] {note_text}"
            deadline.save()

        return redirect("deadlines:deadline_detail", pk=pk)

    return redirect("deadlines:deadline_detail", pk=pk)


@login_required
def deadline_add(request):
    """Add a new deadline (simplified form)."""
    if request.method == "POST":
        # Handle form submission
        entity_id = request.POST.get("entity")
        title = request.POST.get("title")
        category = request.POST.get("category")
        frequency = request.POST.get("frequency")
        next_due = request.POST.get("next_due")
        amount = request.POST.get("amount")
        account_number = request.POST.get("account_number")
        remind_days_before = request.POST.get("remind_days_before")
        notes = request.POST.get("notes")

        if entity_id and title:
            deadline = Deadline.objects.create(
                entity_id=entity_id,
                title=title,
                category=category if category else "Other",
                frequency=frequency if frequency else "One-Time",
                next_due=next_due if next_due else date.today(),
                estimated_amount=amount if amount else None,
                account_number=account_number if account_number else "",
                remind_days_before=remind_days_before if remind_days_before else 7,
                notes=notes if notes else "",
                status="Active",
            )
            return redirect("deadlines:todo")

    # GET request - show form
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    context = {
        "entities": entities,
    }

    return render(request, "deadlines/deadline_add.html", context)


@login_required
def entity_list(request):
    """List of all entities."""
    entities = Entity.objects.filter(status="Active").order_by("entity_code")

    # Add state color coding
    for entity in entities:
        if entity.physical_state == "CO":
            entity.color = "purple"
        elif entity.physical_state == "OR":
            entity.color = "green"
        else:
            entity.color = "yellow"

    context = {
        "entities": entities,
    }

    return render(request, "deadlines/entity_list.html", context)


@login_required
def entity_detail(request, pk):
    """Detailed view of an entity with tabs."""
    entity = get_object_or_404(Entity, pk=pk)
    tab = request.GET.get("tab", "overview")

    # Get all related data
    bank_accounts = entity.bank_accounts.filter(status="Active")
    credit_cards = entity.credit_cards.filter(status="Active")
    insurance_policies = entity.insurance_policies.filter(status="Active").order_by(
        "renewal_date"
    )
    licenses = entity.licenses.filter(status="Active").order_by("expiration_date")
    loans = entity.loans.filter(status="Active").order_by("maturity_date")
    deadlines = entity.deadlines.filter(status__in=["Active", "Autopay"]).order_by(
        "next_due"
    )[:10]
    contacts = entity.contacts.all().order_by("contact_type", "last_name")
    state_accounts = entity.state_accounts.filter(status="Active").order_by("state", "account_type")
    merchant_processors = entity.merchant_processors.filter(status="Active").order_by("processor_name")
    vendors = entity.vendors.filter(status="Active").order_by("vendor_name")

    context = {
        "entity": entity,
        "active_tab": tab,
        "bank_accounts": bank_accounts,
        "credit_cards": credit_cards,
        "insurance_policies": insurance_policies,
        "licenses": licenses,
        "loans": loans,
        "deadlines": deadlines,
        "contacts": contacts,
        "state_accounts": state_accounts,
        "merchant_processors": merchant_processors,
        "vendors": vendors,
    }

    return render(request, "deadlines/entity_detail.html", context)


@login_required
def search(request):
    """Global search across all models."""
    query = request.GET.get("q", "").strip()
    results = {
        "deadlines": [],
        "tasks": [],
        "documents": [],
        "entities": [],
        "contacts": [],
    }
    total_count = 0

    if query:
        # Search Deadlines (title, notes)
        deadlines = Deadline.objects.filter(
            Q(title__icontains=query) | Q(notes__icontains=query)
        ).select_related("entity")[:10]
        for deadline in deadlines:
            deadline.urgency_status = get_deadline_status(deadline)
        results["deadlines"] = list(deadlines)

        # Search Tasks (title, description)
        tasks = Task.objects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related("entity")[:10]
        results["tasks"] = list(tasks)

        # Search Documents (filename, title)
        documents = Document.objects.filter(
            Q(filename__icontains=query) | Q(title__icontains=query)
        ).select_related("entity")[:10]
        results["documents"] = list(documents)

        # Search Entities (legal_name, dba_name)
        entities = Entity.objects.filter(
            Q(legal_name__icontains=query) | Q(dba_name__icontains=query)
        )[:10]
        results["entities"] = list(entities)

        # Search Contacts (first_name, last_name, company_name)
        contacts = Contact.objects.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(company_name__icontains=query)
        ).select_related("entity")[:10]
        results["contacts"] = list(contacts)

        # Calculate total
        total_count = sum(len(v) for v in results.values())

    context = {
        "query": query,
        "results": results,
        "total_count": total_count,
    }

    return render(request, "deadlines/search_results.html", context)


def advance_deadline_to_next_due(deadline):
    """Advance a deadline's next_due date based on its frequency."""
    if not deadline.next_due or not deadline.frequency:
        return False

    if deadline.frequency == "Daily":
        deadline.next_due += timedelta(days=1)
    elif deadline.frequency == "Weekly":
        deadline.next_due += timedelta(weeks=1)
    elif deadline.frequency == "Bi-Weekly":
        deadline.next_due += timedelta(weeks=2)
    elif deadline.frequency == "Monthly":
        deadline.next_due += relativedelta(months=1)
    elif deadline.frequency == "Quarterly":
        deadline.next_due += relativedelta(months=3)
    elif deadline.frequency == "Semi-Annual":
        deadline.next_due += relativedelta(months=6)
    elif deadline.frequency == "Annual":
        deadline.next_due += relativedelta(years=1)
    else:
        # One-Time or unknown frequency - no advancement
        return False

    deadline.save()
    return True


@login_required
def bulk_complete_deadlines(request):
    """Mark multiple deadlines as complete and advance their dates."""
    if request.method == "POST":
        deadline_ids_str = request.POST.get("deadline_ids", "")

        if not deadline_ids_str:
            messages.error(request, "No deadlines selected.")
            return redirect("deadlines:list")

        # Parse comma-separated IDs
        try:
            deadline_ids = [int(id.strip()) for id in deadline_ids_str.split(",") if id.strip()]
        except ValueError:
            messages.error(request, "Invalid deadline IDs provided.")
            return redirect("deadlines:list")

        if not deadline_ids:
            messages.error(request, "No deadlines selected.")
            return redirect("deadlines:list")

        # Process each deadline
        completed_count = 0
        deadlines = Deadline.objects.filter(pk__in=deadline_ids)

        for deadline in deadlines:
            if advance_deadline_to_next_due(deadline):
                completed_count += 1

        if completed_count > 0:
            messages.success(request, f"Successfully completed {completed_count} deadline(s).")
        else:
            messages.warning(request, "No deadlines were advanced (may be one-time deadlines).")

        return redirect("deadlines:list")

    return redirect("deadlines:list")


@login_required
def export_deadlines_csv(request):
    """Export deadlines to CSV file."""
    deadline_ids_str = request.POST.get("deadline_ids", "") or request.GET.get("deadline_ids", "")

    # Get deadlines - either selected ones or all active
    if deadline_ids_str:
        try:
            deadline_ids = [int(id.strip()) for id in deadline_ids_str.split(",") if id.strip()]
            deadlines = Deadline.objects.filter(pk__in=deadline_ids).select_related("entity")
        except ValueError:
            deadlines = Deadline.objects.filter(
                status__in=["Active", "Autopay"]
            ).select_related("entity")
    else:
        deadlines = Deadline.objects.filter(
            status__in=["Active", "Autopay"]
        ).select_related("entity")

    # Sort by next_due date
    deadlines = deadlines.order_by("next_due")

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="deadlines_export.csv"'

    writer = csv.writer(response)
    writer.writerow(["Entity", "Title", "Category", "Next Due", "Amount", "Status"])

    for deadline in deadlines:
        writer.writerow([
            deadline.entity.entity_code if deadline.entity else "",
            deadline.title,
            deadline.category,
            deadline.next_due.strftime("%Y-%m-%d") if deadline.next_due else "",
            str(deadline.estimated_amount) if deadline.estimated_amount else "",
            deadline.status,
        ])

    return response
