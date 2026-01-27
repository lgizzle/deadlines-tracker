from django.urls import path

from . import views_contacts

urlpatterns = [
    path("contacts/", views_contacts.contact_list, name="contact_list"),
    path("contact/<int:pk>/", views_contacts.contact_detail, name="contact_detail"),
    path("contact/add/", views_contacts.contact_add, name="contact_add"),
    path("contact/<int:pk>/edit/", views_contacts.contact_edit, name="contact_edit"),
    path("contact/<int:pk>/delete/", views_contacts.contact_delete, name="contact_delete"),
]
