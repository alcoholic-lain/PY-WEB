from django.urls import path

from . import views

app_name = "expedition"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("afficher/<str:name>/", views.afficher, name="afficher"),
    path("lister/", views.lister, name="lister"),
    path("creer/", views.ExpeditionCreateView.as_view(), name="create"),
    path(
        "detail/<int:expedition_id>/",
        views.ExpeditionDetailView.as_view(),
        name="detail",
    ),
    path(
        "detail/<int:expedition_id>/modifier/",
        views.ExpeditionUpdateView.as_view(),
        name="update",
    ),
    path(
        "detail/<int:expedition_id>/supprimer/",
        views.ExpeditionDeleteView.as_view(),
        name="delete",
    ),
]
