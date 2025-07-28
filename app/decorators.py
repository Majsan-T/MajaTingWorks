from functools import wraps
from flask import abort
from flask_login import current_user


def roles_required(*role_names):
    """
    ✅ Dekorator för att skydda routes baserat på användarroller.

    Användning:
    -----------
    @app.route('/admin')
    @roles_required('admin')
    def admin_dashboard():
        pass

    Parametrar:
    -----------
    *role_names : tuple
        En eller flera roller som krävs för att få tillgång till vyn.

    Funktion:
    ---------
    - Kontrollerar att användaren är inloggad (`current_user.is_authenticated`).
    - Kontrollerar att användaren har minst en av de angivna rollerna.
    - Returnerar **403 Forbidden** om användaren saknar rättigheter.

    Debug:
    ------
    - Skriver ut användarens e-post och alla roller i konsolen (för felsökning).
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 🔍 DEBUG: Visar vem som försöker nå sidan och vilka roller den har
            print("DEBUG USER:", current_user.email, [r.name for r in current_user.roles])

            # ❌ Om användaren inte är inloggad eller saknar nödvändig roll → avbryt
            if not current_user.is_authenticated or not any(current_user.has_role(r) for r in role_names):
                return abort(403)

            # ✅ Annars körs den faktiska funktionen
            return f(*args, **kwargs)

        return decorated_function

    return decorator
