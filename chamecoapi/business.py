import os
from typing import Callable

import requests
from django.core.cache import cache
from django.test import RequestFactory
from dotenv import load_dotenv

load_dotenv()

url_base = os.environ.get("urlBase")

URL_BASE_TOKEN = f"{url_base}api/token/"


def requestFactory(
    method: str,
    url: str,
    id_user: int,
    body: dict[str, str] | None = None,
):
    request = getattr(requests, method.lower(), None)

    if request is None:
        raise ValueError(f"Método {method} não é suportado.")

    # Testa todos as possibilidades possíveis de obter a autenticação, se não for possível retorna False
    # O retorno False deste trecho deve ser tratado na view como uma resposta HTTP 401
    auth = {}
    if isAuthenticated(id_user):
        tokens = isTokenValid(id_user)
        if not tokens:
            return False
        else:
            auth = tokens

    else:
        return False

    access = auth["access"]
    header = {"Authorization": f"Bearer {access}"}

    response = request(url, json=body, headers=header)

    return response


def getTokens(id_user: int) -> dict[str, str | None] | None:
    access = cache.get(f"api_cortex_access_token_user_{id_user}")
    refresh = cache.get(f"api_cortex_refresh_token_user_{id_user}")

    if not access and not refresh:
        return None

    return {"access": access, "refresh": refresh}


def setTokens(id_user: int, access: str, refresh: str):
    cache.set(
        f"api_cortex_access_token_user_{id_user}", f"{access}", timeout=600)
    cache.set(
        f"api_cortex_refresh_token_user_{id_user}", f"{refresh}", timeout=2100)


def verifyToken(id_user: int) -> bool:
    token = getTokens(id_user)["access"]

    data = {"token": token}

    response = requests.post(url=f"{URL_BASE_TOKEN}verify/", json=data)

    if response.status_code != 200:
        return False

    return True


def refreshToken(id_user: int) -> bool:
    refresh = getTokens(id_user)["refresh"]

    if refresh:
        data = {"refresh": refresh}
    else:
        data = {"refresh": "null"}

    response = requests.post(url=f"{URL_BASE_TOKEN}refresh/", json=data)

    if response.status_code != 200:
        cache.delete(f"api_cortex_access_token_user_{id_user}")
        cache.delete(f"api_cortex_refresh_token_user_{id_user}")

        return False

    data = response.json()

    setTokens(id_user, data["access"], refresh)

    return True


def isTokenValid(id_user: int) -> dict[str, str | None] | bool:
    if verifyToken(id_user):
        auth = getTokens(id_user)
        return auth

    elif refreshToken(id_user):
        auth = getTokens(id_user)
        return auth

    else:
        return False


def isAuthenticated(id_user: int) -> bool:
    isAuthenticated = False

    if getTokens(id_user):
        isAuthenticated = True

    return isAuthenticated
