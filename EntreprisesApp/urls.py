from django.urls import path

from . import views

app_name = "entreprise"

urlpatterns = [
    path("", views.EntrepriseListView.as_view(), name="lister"),
    path("creer/", views.EntrepriseCreateView.as_view(), name="create"),
    path("<int:pk>/", views.EntrepriseDetailView.as_view(), name="detail"),
    path("<int:pk>/modifier/", views.EntrepriseUpdateView.as_view(), name="update"),
    path("<int:pk>/supprimer/", views.EntrepriseDeleteView.as_view(), name="delete"),
]
