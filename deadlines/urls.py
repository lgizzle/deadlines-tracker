from django.urls import path

from . import views

app_name = "deadlines"

urlpatterns = [
    # Main dashboard views
    path("", views.todo_view, name="todo"),
    path("list/", views.list_view, name="list"),
    path("calendar/", views.calendar_view, name="calendar"),
    # Deadline views
    path("deadline/<int:pk>/", views.deadline_detail, name="deadline_detail"),
    path("deadline/add/", views.deadline_add, name="deadline_add"),
    path(
        "deadline/<int:pk>/complete/", views.deadline_complete, name="deadline_complete"
    ),
    path(
        "deadline/<int:pk>/add-note/", views.deadline_add_note, name="deadline_add_note"
    ),
    # Entity views
    path("entities/", views.entity_list, name="entity_list"),
    path("entity/<str:pk>/", views.entity_detail, name="entity_detail"),
]
