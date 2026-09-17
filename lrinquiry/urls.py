from django.urls import path

from . import views

urlpatterns = [
    path("", views.inquiry_dashboard, name="inquiry_dashboard"),
    path("add/", views.add_inquiry, name="add_inquiry"),
    path("<int:pk>/edit/", views.edit_inquiry, name="edit_inquiry"),
    path("<int:pk>/delete/", views.delete_inquiry, name="delete_inquiry"),
    path("contacts/", views.contact_book, name="contact_book"),
    path("contacts/lookup/", views.contact_lookup, name="contact_lookup"),
]
