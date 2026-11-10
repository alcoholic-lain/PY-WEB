from django.urls import path

from . import views

app_name = "expedition"

urlpatterns = [
    path("home/", views.home, name="home"),
    path("afficher/<str:name>/", views.afficher, name="afficher"),
    path("lister/", views.lister, name="lister"),
    path(
        "detail/<int:expedition_id>/",
        views.ExpeditionDetailView.as_view(),
        name="detail",
    ),
]
