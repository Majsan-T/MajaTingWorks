# app/utils/tokens.py
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_token(email):
    """
    ✅ Skapar en tidsbegränsad token för t.ex. återställning av lösenord.
    - `email`: E-postadressen som ska kodas in i token.
    - Token är signerad med applikationens SECRET_KEY och en salt-sträng ("password-reset-salt").
    - Resultatet är en URL-säker sträng.
    """
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset-salt")


def confirm_token(token, expiration=3600):
    """
    ✅ Verifierar en token och returnerar den dekodade e-posten om giltig.
    - `token`: Den token som ska verifieras.
    - `expiration`: Token är giltig i sekunder (standard: 3600s = 1 timme).
    - Returnerar e-postadressen om token är giltig, annars `None`.
    """
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None
