"""Views for task management."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Entity, Task


@login_required
def task_list(request):
    """List all tasks with filtering by status, priority, entity, and task_type."""
    status_filter = request.GET.get("status", "")
    priority_filter = request.GET.get("priority", "")
    entity_filter = request.GET.get("entity", "")
    task_type_filter = request.GET.get("task_type", "")

    # Base queryset - all tasks ordered by created_at descending
    tasks = Task.objects.all().select_related("entity").order_by("-created_at")

    # Apply filters
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if entity_filter:
        tasks = tasks.filter(entity__entity_code=entity_filter)
    if task_type_filter:
        tasks = tasks.filter(task_type=task_type_filter)

    # Count tasks by status for sidebar
    status_counts = {
        "pending": Task.objects.filter(status="pending").count(),
        "in_progress": Task.objects.filter(status="in_progress").count(),
        "completed": Task.objects.filter(status="completed").count(),
        "deferred": Task.objects.filter(status="deferred").count(),
    }

    # Get filter options
    entities = Entity.objects.filter(status="Active").order_by("entity_code")
    statuses = [choice[0] for choice in Task.STATUS_CHOICES]
    priorities = [choice[0] for choice in Task.PRIORITY_CHOICES]
    task_types = [choice[0] for choice in Task.TASK_TYPE_CHOICES]

    context = {
        "tasks": tasks,
        "entities": entities,
        "statuses": statuses,
        "priorities": priorities,
        "task_types": task_types,
        "status_filter": status_filter,
        "priority_filter": priority_filter,
        "entity_filter": entity_filter,
        "task_type_filter": task_type_filter,
        "status_counts": status_counts,
        "active_tab": "tasks",
    }

    return render(request, "deadlines/tasks/task_list.html", context)


@login_required
def task_detail(request, pk):
    """View single task details."""
    task = get_object_or_404(Task, pk=pk)

    context = {
        "task": task,
        "active_tab": "tasks",
    }

    return render(request, "deadlines/tasks/task_detail.html", context)


@login_required
def task_status_update(request, pk):
    """Update task status via POST."""
    if request.method == "POST":
        task = get_object_or_404(Task, pk=pk)
        new_status = request.POST.get("status")

        if new_status in [choice[0] for choice in Task.STATUS_CHOICES]:
            task.status = new_status
            # Set completed_at timestamp when marking as completed
            if new_status == "completed":
                task.completed_at = timezone.now()
            elif task.completed_at:
                # Clear completed_at if status changed from completed
                task.completed_at = None
            task.save()

        return redirect("deadlines:task_detail", pk=pk)

    return redirect("deadlines:task_detail", pk=pk)
