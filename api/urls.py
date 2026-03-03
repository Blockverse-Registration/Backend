from django.urls import path
from . import views

urlpatterns = [
    path("v1/payment/create-order", views.create_order),
    path("v1/payment/verify", views.verify_payment),
    path("v1/team-registration-ax92", views.register_team),
]