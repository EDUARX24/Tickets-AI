from flask import redirect, session
from functools import wraps


def login_required(f):
    """
    Decorador para requerir inicio de sesion.
    Me lo copie de FLASK :33
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("idUsuario") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function