"""
API URL routing for gmail-daily integration.
"""
from django.urls import path

from . import views_api

app_name = "api"

urlpatterns = [
    # Health check
    path("health/", views_api.health_check, name="health"),

    # Entities
    path("entities/", views_api.entity_list, name="entity_list"),

    # Tasks
    path("tasks/", views_api.task_create, name="task_create"),
    path("tasks/check-duplicate/", views_api.task_check_duplicate, name="task_check_duplicate"),
    path("tasks/<int:task_id>/", views_api.task_update, name="task_update"),

    # Documents
    path("documents/", views_api.document_create, name="document_create"),
    path("documents/check-duplicate/", views_api.document_check_duplicate, name="document_check_duplicate"),

    # Deadline search
    path("deadlines/search/", views_api.deadline_search, name="deadline_search"),
]
