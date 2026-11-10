from django.urls import path

from . import views

app_name = "vehicule"

urlpatterns = [
    path("", views.VehiculeListView.as_view(), name="lister"),
    path("creer/", views.VehiculeCreateView.as_view(), name="create"),
    path("<int:pk>/", views.VehiculeDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", views.VehiculeUpdateView.as_view(), name="update"),
    path("<int:pk>/supprimer/", views.VehiculeDeleteView.as_view(), name="delete"),
]
