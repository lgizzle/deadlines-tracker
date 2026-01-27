from django.urls import path

from . import views_licenses

urlpatterns = [
    path("licenses/", views_licenses.license_list, name="license_list"),
    path("license/<int:pk>/", views_licenses.license_detail, name="license_detail"),
    path("license/add/", views_licenses.license_add, name="license_add"),
    path("license/<int:pk>/edit/", views_licenses.license_edit, name="license_edit"),
]
