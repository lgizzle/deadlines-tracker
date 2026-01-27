from django.urls import path

from . import views_insurance

urlpatterns = [
    path("insurance/", views_insurance.insurance_list, name="insurance_list"),
    path("insurance/<int:pk>/", views_insurance.insurance_detail, name="insurance_detail"),
    path("insurance/add/", views_insurance.insurance_add, name="insurance_add"),
    path("insurance/<int:pk>/edit/", views_insurance.insurance_edit, name="insurance_edit"),
]
