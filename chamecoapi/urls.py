from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import BlocosViewSet, SalasViewSet, UsuariosViewSet

chameco_router = SimpleRouter()
chameco_router.register("blocos", BlocosViewSet)
chameco_router.register("usuarios", UsuariosViewSet)
chameco_router.register("salas", SalasViewSet)
urlpatterns = [
    ####### API #######
    path("api/v1/", include(chameco_router.urls)),
]
