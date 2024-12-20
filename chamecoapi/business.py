import os
from datetime import timedelta
from typing import Callable

import requests
from django.utils import timezone
from dotenv import load_dotenv

from .models import Tokens

load_dotenv()

url_base = os.environ.get("urlBase")

URL_BASE_TOKEN = f"{url_base}cortex/api/token/"


def requestFactory(
    method: str,
    url: str,
    hash_token: str,
    body: dict[str, str] | None = None,
):
    request = getattr(requests, method.lower(), None)

    if request is None:
        raise ValueError(f"Método {method} não é suportado.")

    # Testa todos as possibilidades possíveis de obter a autenticação, se não for possível retorna False
    # O retorno False deste trecho deve ser tratado na view como uma resposta HTTP 401
    auth = {}

    if isAuthenticated(hash_token):

        tokens = isTokenValid(hash_token)
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


def getTokens(hash_token: str) -> dict[str, str | None] | None:
    Tokens.objects.filter(data_expiracao__lt=timezone.now()).delete()

    access = None
    refresh = None

    try:
        access = Tokens.objects.get(hash_token=f"{hash_token}_access").valor
    except:
        pass

    try:
        refresh = Tokens.objects.get(hash_token=f"{hash_token}_refresh").valor
    except:
        pass

    if not access and not refresh:
        return None

    return {"access": access, "refresh": refresh}


def setTokens(hash_token: str, access: str, refresh: str):
    Tokens.objects.update_or_create(
        hash_token=f"{hash_token}_access",
        defaults={
            "valor": access,
            "data_expiracao": timezone.now() + timedelta(minutes=10),
        },
    )
    Tokens.objects.update_or_create(
        hash_token=f"{hash_token}_refresh",
        defaults={
            "valor": refresh,
            "data_expiracao": timezone.now() + timedelta(minutes=35),
        },
    )


def setIdUser(hash_token: str, id_user: int):
    Tokens.objects.update_or_create(
        hash_token=f"{hash_token}_id_user",
        defaults={
            "valor": str(id_user),
            "data_expiracao": timezone.now() + timedelta(minutes=35),
        },
    )


def getIdUser(hash_token: str) -> int | None:
    Tokens.objects.filter(data_expiracao__lt=timezone.now()).delete()

    id_user = None

    try:
        id_user = Tokens.objects.get(hash_token=f"{hash_token}_id_user").valor
    except:
        pass

    if not id_user:
        return None

    return int(id_user)


def verifyToken(hash_token: str) -> bool:
    token = getTokens(hash_token)

    if token:
        data = {"token": token["access"]}
    else:
        return False

    response = requests.post(url=f"{URL_BASE_TOKEN}verify/", json=data)

    if response.status_code != 200:
        return False

    return True


def refreshToken(hash_token: str) -> bool:
    refresh = getTokens(hash_token)

    if refresh:
        data = {"refresh": refresh["refresh"]}
    else:
        return False

    response = requests.post(url=f"{URL_BASE_TOKEN}refresh/", json=data)

    if response.status_code != 200:
        Tokens.objects.filter(hash_token=f"{hash_token}_access").delete()
        Tokens.objects.filter(hash_token=f"{hash_token}_refresh").delete()

        return False

    data = response.json()

    setTokens(hash_token, data["access"], refresh)

    return True


def isTokenValid(hash_token: str) -> dict[str, str | None] | bool:
    if verifyToken(hash_token):
        auth = getTokens(hash_token)
        return auth

    elif refreshToken(hash_token):
        auth = getTokens(hash_token)
        return auth

    else:
        return False


def isAuthenticated(hash_token: str) -> bool:
    isAuthenticated = False

    if getTokens(hash_token):
        isAuthenticated = True

    return isAuthenticated
