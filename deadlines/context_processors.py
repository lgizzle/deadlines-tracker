"""
Context processors for deadlines app.

These inject global variables into every template context.
"""

from datetime import date

from .models import Deadline, Task, License, InsurancePolicy


def urgency_stats(request):
    """
    Inject global urgency counts into all templates.

    This enables the sidebar badge to show overdue count and
    supports the global critical alert banner.
    """
    today = date.today()

    # Count overdue deadlines (Active or Autopay status)
    overdue_deadlines = Deadline.objects.filter(
        status__in=['Active', 'Autopay'],
        next_due__lt=today
    ).count()

    # Count overdue tasks (pending status with past due date)
    overdue_tasks = Task.objects.filter(
        status='pending',
        due_date__lt=today
    ).count()

    # Count expired licenses
    expired_licenses = License.objects.filter(
        status='Active',
        expiration_date__lt=today
    ).count()

    # Count expired insurance policies
    expired_insurance = InsurancePolicy.objects.filter(
        status='Active',
        renewal_date__lt=today
    ).count()

    # Total overdue items across all models
    total_overdue = (
        overdue_deadlines +
        overdue_tasks +
        expired_licenses +
        expired_insurance
    )

    return {
        'overdue_count': total_overdue,
        'overdue_deadlines_count': overdue_deadlines,
        'overdue_tasks_count': overdue_tasks,
        'expired_licenses_count': expired_licenses,
        'expired_insurance_count': expired_insurance,
    }
