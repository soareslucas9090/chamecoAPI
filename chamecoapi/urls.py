from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (BlocosViewSet, ChavesViewSet, LoginAPIView, SalasViewSet,
                    UsuariosViewSet)

chameco_router = SimpleRouter()
chameco_router.register("blocos", BlocosViewSet)
chameco_router.register("usuarios", UsuariosViewSet)
chameco_router.register("salas", SalasViewSet)
chameco_router.register("chaves", ChavesViewSet)
urlpatterns = [
    ####### API #######
    path("", include(chameco_router.urls)),
    path("login/", LoginAPIView.as_view(), name="login"),
]
